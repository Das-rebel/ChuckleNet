#!/usr/bin/env python3
"""
Batch Process Pipeline for Laughter Detection Data Collection
Handles: Download → VTT → Whisper → Alignment → Upload

Usage:
    python3 training/batch_process_pipeline.py --batch 12 --videos 5
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path

def run_cmd(cmd, timeout=600):
    """Run shell command with timeout"""
    print(f"  CMD: {' '.join(cmd[:5])}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0, result.stdout, result.stderr

def download_audio(video_ids, batch_num):
    """Download audio for videos"""
    batch_dir = f"data/audio_comedy/audio/batch{batch_num}"
    os.makedirs(batch_dir, exist_ok=True)
    
    for vid in video_ids:
        out_path = f"{batch_dir}/{vid}.mp3"
        if os.path.exists(out_path):
            print(f"  SKIP {vid}: exists")
            continue
        print(f"  Downloading {vid}...")
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
            "-o", out_path,
            "--", f"https://www.youtube.com/watch?v={vid}"
        ]
        success, _, _ = run_cmd(cmd, timeout=900)
        if success:
            print(f"    OK: {vid}")
        else:
            print(f"    FAIL: {vid}")

def download_vtt(video_ids):
    """Download VTT subtitles"""
    vtt_dir = "data/audio_comedy/vtt_subtitles/en"
    os.makedirs(vtt_dir, exist_ok=True)
    
    for vid in video_ids:
        vtt_path = f"{vtt_dir}/{vid}.en.vtt"
        if os.path.exists(vtt_path):
            print(f"  SKIP {vid}: VTT exists")
            continue
        print(f"  VTT {vid}...")
        cmd = [
            "yt-dlp", "--write-auto-sub", "--sub-lang", "en", "--sub-format", "vtt",
            "--skip-download", "-o", f"{vtt_dir}/{vid}.%(ext)s", "--",
            f"https://www.youtube.com/watch?v={vid}"
        ]
        success, _, _ = run_cmd(cmd, timeout=120)

def transcribe_whisper(video_ids, batch_num):
    """Transcribe with faster-whisper"""
    from faster_whisper import WhisperModel
    
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    tr_dir = "data/audio_comedy/transcripts/en"
    os.makedirs(tr_dir, exist_ok=True)
    
    for vid in video_ids:
        tr_path = f"{tr_dir}/{vid}_transcript.json"
        if os.path.exists(tr_path):
            print(f"  SKIP {vid}: transcript exists")
            continue
        
        audio_path = f"data/audio_comedy/audio/batch{batch_num}/{vid}.mp3"
        if not os.path.exists(audio_path):
            print(f"  SKIP {vid}: no audio")
            continue
        
        print(f"  Transcribing {vid}...")
        try:
            segments, info = model.transcribe(audio_path, word_timestamps=True)
            seg_list = list(segments)
            word_count = sum(len(s.words) for s in seg_list)
            
            transcript = {
                "video_id": vid, "title": "", "comedian": f"batch{batch_num}",
                "language": "en",
                "segments": [{
                    "id": i, "seek": 0, "start": s.start, "end": s.end,
                    "text": s.text, "tokens": [], "temperature": 0.0,
                    "avg_logprob": getattr(s, "avg_logprob", 0),
                    "compression_ratio": getattr(s, "compression_ratio", 0),
                    "no_speech_prob": getattr(s, "no_speech_prob", 0),
                    "words": [{"word": w.word, "start": w.start, "end": w.end, 
                               "probability": w.probability} for w in s.words]
                } for i, s in enumerate(seg_list)],
                "words": []
            }
            
            with open(tr_path, "w") as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
            print(f"    OK: {word_count} words")
        except Exception as e:
            print(f"    ERROR: {e}")

def align_batch(video_ids, batch_num):
    """Align Whisper words with VTT laughter markers"""
    import re
    
    def parse_timestamp(ts):
        p = ts.replace(',','.').split(':')
        return int(p[0])*3600 + int(p[1])*60 + float(p[2])
    
    def parse_vtt(path):
        with open(path) as f: lines = f.readlines()
        segs, i = [], 0
        while i < len(lines):
            m = re.match(r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})', lines[i].strip())
            if m:
                s, e = parse_timestamp(m.group(1)), parse_timestamp(m.group(2))
                txt = []; i += 1
                while i < len(lines) and lines[i].strip():
                    if re.match(r'\d{2}:\d{2}:\d{2}', lines[i]): break
                    txt.append(lines[i].strip()); i += 1
                t = re.sub(r'<[^>]+>', '', ' '.join(txt)).strip()
                if t: segs.append({"start":s,"end":e,"text":t})
            else: i += 1
        return segs
    
    def extract_laughter(vtt):
        markers = ["[laughter]","[laugh]","[Laugh]","[LAUGHTER]","[applause]","(laughter)","(laugh)","(audience laughs)"]
        return [{"start":s["start"],"end":s["end"]} for s in vtt if any(m.lower() in s["text"].lower() for m in markers)]
    
    def load_words(path):
        with open(path) as f: data = json.load(f)
        return [{"word":w["word"].strip(),"start":w["start"],"end":w["end"]} 
                for seg in data.get("segments",[]) for w in seg.get("words",[])]
    
    def align(words, events, window=3.0):
        if not events: return [{"word":w["word"],"start":w["start"],"end":w["end"],"label":0} for w in words]
        intervals = []
        for e in sorted(events, key=lambda x: x["start"]):
            if not intervals or e["start"] > intervals[-1][1]+1.0:
                intervals.append((e["start"], e["end"]))
            else:
                intervals[-1] = (intervals[-1][0], max(intervals[-1][1], e["end"]))
        aligned = [{"word":w["word"],"start":w["start"],"end":w["end"],"label":0} for w in words]
        for i,w in enumerate(aligned):
            for ls,le in intervals:
                if 0<=ls-w["end"]<=window or (w["start"]>=ls-0.5 and w["end"]<=le+0.5): aligned[i]["label"]=1
        labels=[a["label"] for a in aligned]
        for i,a in enumerate(aligned):
            if a["label"]==1:
                for j in range(max(0,i-2),i):
                    if labels[j]==0: labels[j]=1
        for i in range(len(aligned)): aligned[i]["label"]=labels[i]
        return aligned
    
    all_segs = []
    for vid in video_ids:
        tr_path = f"data/audio_comedy/transcripts/en/{vid}_transcript.json"
        vtt_path = f"data/audio_comedy/vtt_subtitles/en/{vid}.en.vtt"
        
        if not os.path.exists(tr_path) or not os.path.exists(vtt_path):
            continue
        
        words = load_words(tr_path)
        events = extract_laughter(parse_vtt(vtt_path))
        aligned = align(words, events)
        
        pos = sum(1 for w in aligned if w["label"]==1)
        print(f"  {vid}: {len(aligned)} words, {pos} pos")
        
        audio_file = f"data/audio_comedy/audio/batch{batch_num}/{vid}.mp3"
        for i,w in enumerate(aligned):
            cs,ce = max(0,i-3),min(len(aligned),i+4)
            all_segs.append({
                "video_id":vid,"comedian":f"batch{batch_num}","audio_file":audio_file,
                "word":w["word"],"start":round(w["start"],3),"end":round(w["end"],3),
                "label":w["label"],
                "context_words":[aligned[j]["word"] for j in range(cs,ce)],
                "context_labels":[aligned[j]["label"] for j in range(cs,ce)]
            })
    
    return all_segs

def append_to_main(batch_segs, batch_num):
    """Append aligned segments to main file"""
    batch_file = f"data/audio_comedy/aligned_segments_batch{batch_num}.jsonl"
    
    with open(batch_file, "w") as f:
        for seg in batch_segs:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")
    
    # Append to main
    main_file = "data/audio_comedy/aligned_segments.jsonl"
    with open(main_file, "a") as f:
        for seg in batch_segs:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")
    
    return len(batch_segs)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--videos", type=str, default="")
    parser.add_argument("--step", type=str, default="all")  # download, vtt, transcribe, align, all
    args = parser.parse_args()
    
    batch = args.batch
    videos = [v.strip() for v in args.videos.split() if v.strip()] if args.videos else []
    
    if not videos:
        print("No videos specified. Use --videos \"vid1 vid2 ...\"")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Batch {batch} Pipeline: {len(videos)} videos")
    print(f"Step: {args.step}")
    print(f"{'='*60}\n")
    
    if args.step in ["download", "all"]:
        print("=== DOWNLOAD AUDIO ===")
        download_audio(videos, batch)
    
    if args.step in ["vtt", "all"]:
        print("\n=== DOWNLOAD VTT ===")
        download_vtt(videos)
    
    if args.step in ["transcribe", "all"]:
        print("\n=== WHISPER TRANSCRIBE ===")
        transcribe_whisper(videos, batch)
    
    if args.step in ["align", "all"]:
        print("\n=== ALIGN ===")
        segs = align_batch(videos, batch)
        count = append_to_main(segs, batch)
        print(f"\nAdded {count} segments to aligned_segments.jsonl")
    
    print("\n=== DONE ===")
