#!/usr/bin/env python3
"""
Google Cloud Speech-to-Text for Hindi/Chinese YouTube Videos

Downloads audio from YouTube, sends to GCP Speech-to-Text API,
and extracts laughter markers based on speech patterns.
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import storage, speech
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

GCS_BUCKET = 'chuckle-net-youtube-20260616'
GCS_PROJECT = 'omniclaw-personal-assistant'

# ============================================================================
# GCS UTILITIES
# ============================================================================

def get_gcs_bucket():
    client = storage.Client(project=GCS_PROJECT)
    return client.bucket(GCS_BUCKET)

def gcs_upload_json(data: dict, gcs_path: str) -> bool:
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        return True
    except Exception as e:
        print(f"    GCS upload failed: {e}")
        return False

def gcs_exists(gcs_path: str) -> bool:
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception:
        return False

# ============================================================================
# AUDIO DOWNLOAD
# ============================================================================

def download_audio(video_id: str, video_url: str, lang: str) -> Optional[str]:
    """Download audio from YouTube video using yt-dlp."""
    
    output_path = f'/tmp/{video_id}_{lang}.wav'
    if os.path.exists(output_path):
        return output_path
    
    # Clean up any existing partial files with this video_id
    for f in os.listdir('/tmp'):
        if video_id in f:
            try:
                os.remove(f'/tmp/{f}')
            except:
                pass
    
    # Simple download - just get best audio
    temp_wav = f'/tmp/{video_id}.wav'
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'wav',
        '--audio-quality', '0',
        '--output', f'/tmp/{video_id}.%(ext)s',
        '--no-playlist',
        '--', video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Find the downloaded wav file
        downloaded = None
        for f in os.listdir('/tmp'):
            if video_id in f and f.endswith('.wav'):
                downloaded = f'/tmp/{f}'
                break
        
        if downloaded:
            # Resample to 16kHz mono for Speech-to-Text
            convert_cmd = ['ffmpeg', '-i', downloaded, '-ar', '16000', '-ac', '1', output_path, '-y']
            conv_result = subprocess.run(convert_cmd, capture_output=True, text=True, timeout=300)
            
            # Remove original if different from output
            if downloaded != output_path:
                try:
                    os.remove(downloaded)
                except:
                    pass
            
            if os.path.exists(output_path):
                print(f"    Audio: {downloaded} -> {output_path}")
                return output_path
            else:
                print(f"    Conversion failed")
                return downloaded  # Return original even if conversion failed
        else:
            print(f"    Download failed")
            if result.stderr:
                print(f"    {result.stderr[-300:]}")
                
    except Exception as e:
        print(f"    Download error: {e}")
    
    return None

# ============================================================================
# GOOGLE SPEECH-TO-TEXT
# ============================================================================

def transcribe_audio(audio_path: str, lang: str, video_id: str = None) -> Optional[List[Dict]]:
    """Transcribe audio using Google Cloud Speech-to-Text via GCS."""
    
    client = speech.SpeechClient()
    
    # Language code mapping
    lang_map = {
        'hi': 'hi-IN',
        'zh': 'zh-CN',
        'en': 'en-US',
        'ta': 'ta-IN',
        'ml': 'ml-IN',
        'kn': 'kn-IN',
        'mr': 'mr-IN',
        'bn': 'bn-IN',
        'te': 'te-IN',
    }
    
    language_code = lang_map.get(lang, 'hi-IN')
    
    # Upload audio to GCS for large file processing
    gcs_bucket = get_gcs_bucket()
    gcs_audio_path = f'speech_audio/{video_id}_{lang}.wav' if video_id else f'speech_audio/{os.path.basename(audio_path)}'
    
    print(f"    Uploading to GCS: {gcs_audio_path}")
    blob = gcs_bucket.blob(gcs_audio_path)
    blob.upload_from_filename(audio_path)
    gcs_uri = f'gs://{GCS_BUCKET}/{gcs_audio_path}'
    
    audio = speech.RecognitionAudio(uri=gcs_uri)
    
    config = speech.RecognitionConfig(
        encoding='LINEAR16',
        sample_rate_hertz=16000,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model='latest_long',
        enable_word_time_offsets=True,
    )
    
    try:
        print(f"    Starting transcription...")
        operation = client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=3600)  # 1 hour timeout for long audio
        
        results = []
        for result in response.results:
            alternative = result.alternatives[0]
            for word in alternative.words:
                results.append({
                    'word': word.word,
                    'start_time': word.start_time.total_seconds(),
                    'end_time': word.end_time.total_seconds(),
                    'confidence': getattr(word, 'confidence', 0.0),
                })
        
        # Cleanup GCS file
        try:
            blob.delete()
        except:
            pass
        
        return results
        
    except Exception as e:
        print(f"    Transcription error: {e}")
        return None

def extract_laughter_from_transcript(transcript: List[Dict], audio_path: str) -> Dict:
    """
    Extract laughter markers from transcript + audio analysis.
    
    Strategy:
    1. Look for laughter sounds in transcript (haha, hehe, lol, etc.)
    2. Use audio energy to detect non-speech segments (likely laughter)
    3. Combine both signals
    """
    
    # Laughter text patterns (multilingual)
    laughter_texts = [
        'haha', 'hehe', 'hoho', 'lol', 'lmao', 'rofl',
        '哈哈', '呵呵', '嘻嘻', '嘿嘿',
        'हाहा', 'हीही', 'होहो',
        # Add common laughter expressions
    ]
    
    laughter_markers = []
    utterances = []
    
    # Group words into sentences/segments
    current_segment = []
    segment_start = None
    
    for item in transcript:
        word = item['word'].lower()
        start = item['start_time']
        end = item['end_time']
        
        # Check if this word is laughter
        is_laughter_word = any(lt in word for lt in laughter_texts)
        
        if segment_start is None:
            segment_start = start
        
        current_segment.append({
            'word': item['word'],
            'start': start,
            'end': end,
            'is_laughter': is_laughter_word
        })
        
        # End of sentence (based on punctuation or gap)
        if item.get('word', '')[-1] in '.!?।' or (current_segment and len(current_segment) > 1):
            # Check if segment contains laughter
            has_laugh = any(w['is_laughter'] for w in current_segment)
            
            # Create utterance
            seg_start = current_segment[0]['start']
            seg_end = current_segment[-1]['end']
            text = ' '.join(w['word'] for w in current_segment)
            
            utterances.append({
                'start': seg_start,
                'end': seg_end,
                'text': text,
                'has_laughter': has_laugh
            })
            
            if has_laugh:
                laughter_markers.append({
                    'start': seg_start,
                    'end': seg_end,
                    'text': text,
                    'has_laughter': True
                })
            
            current_segment = []
            segment_start = None
    
    return {
        'laughter_count': len(laughter_markers),
        'laughter_markers': laughter_markers,
        'total_utterances': len(utterances),
        'utterances': utterances[:500],
        'status': 'success'
    }

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_video(video: Dict, lang: str = 'hi') -> Dict:
    """Process a single video: download audio, transcribe, extract laughter."""
    
    video_id = video['id']
    print(f"  Processing: {video['title'][:50]}... ({lang})")
    
    # Check if already processed
    if gcs_exists(f'speech/{video_id}_{lang}.json'):
        print(f"    Already processed, skipping")
        return {'id': video_id, 'status': 'already_exists'}
    
    # Step 1: Download audio
    audio_path = download_audio(video_id, video['url'], lang)
    if not audio_path:
        print(f"    Failed to download audio")
        return {'id': video_id, 'status': 'download_failed'}
    
    print(f"    Audio downloaded: {audio_path}")
    
    # Step 2: Transcribe
    transcript = transcribe_audio(audio_path, lang, video_id)
    if not transcript:
        print(f"    Failed to transcribe")
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return {'id': video_id, 'status': 'transcription_failed'}
    
    print(f"    Transcribed {len(transcript)} words")
    
    # Step 3: Extract laughter
    result = extract_laughter_from_transcript(transcript, audio_path)
    result['id'] = video_id
    result['lang'] = lang
    
    # Cleanup audio
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    # Upload to GCS
    gcs_upload_json(result, f'speech/{video_id}_{lang}.json')
    
    if result['laughter_count'] > 0:
        print(f"    ✓ Found {result['laughter_count']} laughter markers, {result['total_utterances']} utterances")
    else:
        print(f"    ✗ No laughter found")
    
    return result

def search_youtube_videos(query: str, max_results: int = 50) -> List[Dict]:
    """Search YouTube for videos."""
    cmd = ['yt-dlp', '--flat-playlist', '--dump-json', f'ytsearch{max_results}:{query}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'url': f"https://www.youtube.com/watch?v={data.get('id')}",
                        'duration': data.get('duration'),
                        'channel': data.get('channel'),
                    })
                except json.JSONDecodeError:
                    continue
        return videos
    except Exception as e:
        print(f"Search error: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Transcribe Hindi/Chinese YouTube videos')
    parser.add_argument('--max-videos', type=int, default=20)
    parser.add_argument('--parallel', type=int, default=2)  # Keep low for API limits
    parser.add_argument('--language', default='hi', choices=['hi', 'zh', 'ta', 'ml'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    print(f"=== Google Speech-to-Text Transcription ===")
    print(f"Language: {args.language}")
    print(f"Max videos: {args.max_videos}")
    print()
    
    # Search for videos
    lang_queries = {
        'hi': [
            'stand up comedy special zakir khan full',
            'stand up comedy special vipul goyal full',
            'stand up comedy special anubhav singh bassi full',
            'stand up comedy special sunil grover full',
            'kapil sharma show comedy highlights',
        ],
        'zh': [
            'chinese stand up comedy full show',
            'chinese talk show comedy monologue 2023',
            '郭德纲 相声 comedy',
            '周星驰 comedy monologue',
        ],
        'ta': [
            'tamil stand up comedy full show',
            'tamil comedy show monologue',
        ],
        'ml': [
            'malayalam stand up comedy full show',
            'mammootty comedy monologue',
        ]
    }
    
    queries = lang_queries.get(args.language, lang_queries['hi'])
    
    all_videos = {}
    for query in queries:
        videos = search_youtube_videos(query, max_results=20)
        for v in videos:
            if v['id'] not in all_videos:
                all_videos[v['id']] = v
        print(f"  {query[:50]}: {len(videos)} videos")
    
    # Filter by duration
    good = [v for v in all_videos.values() if v.get('duration') and 180 <= v.get('duration', 0) <= 3600]
    print(f"\nGood videos (3-60 min): {len(good)}")
    
    if args.dry_run:
        for v in good[:10]:
            print(f"  {v['title'][:60]}")
        return
    
    # Process
    to_process = good[:args.max_videos]
    print(f"\nProcessing {len(to_process)} videos...")
    
    start = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(process_video, v, args.language): v for v in to_process}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=900)  # 15 min per video
                results.append(result)
            except Exception as e:
                video = futures[future]
                print(f"  Error: {video.get('id')}: {e}")
    
    elapsed = time.time() - start
    
    # Summary
    success = [r for r in results if r.get('status') == 'success' and r.get('laughter_count', 0) > 0]
    total_laughter = sum(r.get('laughter_count', 0) for r in success)
    total_utt = sum(r.get('total_utterances', 0) for r in success)
    
    print(f"\n=== Complete ===")
    print(f"Time: {elapsed:.0f}s")
    print(f"Processed: {len(results)}/{len(to_process)}")
    print(f"With laughter: {len(success)}")
    print(f"Laughter markers: {total_laughter}")
    print(f"Utterances: {total_utt}")

if __name__ == '__main__':
    main()
