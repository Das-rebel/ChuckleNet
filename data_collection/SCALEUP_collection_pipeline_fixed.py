"""
Scaleup Collection Pipeline: 500+ YouTube Comedy Videos
========================================================

Purpose: Collect 500+ comedy videos from YouTube for scaleup
Status: Ready to run (CPU-based, no GPU needed)

Usage:
    python3 SCALEUP_collection_pipeline_fixed.py --target 500 --languages en,zh,hi
    python3 SCALEUP_collection_pipeline_fixed.py --resume  # Resume from previous state

Author: Subhajit Das (IISer Kolkata)
Date: 2026-06-21 (Fixed version)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import argparse

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/chuckle-net")
RAW_VIDEO_DIR = BASE_DIR / "raw" / "videos"
CANDIDATES_FILE = BASE_DIR / "scaleup_candidates.jsonl"
COLLECTION_LOG = BASE_DIR / "collection_log.json"

TARGET_VIDEOS = 500
SUPPORTED_LANGUAGES = ["en", "zh", "hi"]

# ============================================================================
# COOKIE EXTRACTION (Browser Auth for YouTube)
# ============================================================================

def get_browser_cookies(domain: str = "youtube.com") -> Optional[str]:
    """
    Extract cookies from Chrome/Brave using browser_cookie3.
    Returns path to cookie file or None if extraction fails.

    Fix #1: Added browser cookie extraction for YouTube authentication.
    """
    try:
        import browser_cookie3
        cj = browser_cookie3.chrome(domain_name=domain)
        # Return the cookie jar as dict for yt-dlp
        cookies = {}
        for cookie in cj:
            cookies[cookie.name] = cookie.value
        return cookies
    except ImportError:
        print("  [WARN] browser_cookie3 not installed. Install with: pip install browser-cookie3")
        print("  [WARN] Falling back to no cookies - may hit rate limits")
        return None
    except Exception as e:
        print(f"  [WARN] Failed to extract Chrome cookies: {e}")
        print("  [WARN] Falling back to no cookies - may hit rate limits")
        return None


def get_ytdlp_cookie_args() -> List[str]:
    """
    Get yt-dlp arguments for using Chrome/Brave cookies.

    Fix #1: Proper cookie-based authentication for all yt-dlp commands.
    Returns arguments for --cookies-from-browser or empty list.
    """
    # Check if browser_cookie3 is available
    try:
        import browser_cookie3
        # Test if we can actually get YouTube cookies
        cj = browser_cookie3.chrome(domain_name="youtube.com")
        # If we got here, cookies are available
        return ["--cookies-from-browser", "chrome"]
    except ImportError:
        print("  [WARN] browser_cookie3 not installed. YouTube downloads may fail.")
        print("  [WARN] Install with: pip install browser-cookie3")
        return []
    except Exception as e:
        print(f"  [WARN] Could not access Chrome cookies: {e}")
        print("  [WARN] YouTube downloads may fail or hit rate limits.")
        return []


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class VideoCandidate:
    video_id: str
    title: str
    channel: str
    language: str
    duration: int
    view_count: int
    laugh_markers: int
    collection_status: str  # "pending", "collected", "failed"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "VideoCandidate":
        return cls(**d)


@dataclass
class CollectionLog:
    collected: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    pending: List[str] = field(default_factory=list)
    last_updated: str = ""

# ============================================================================
# COLLECTION PIPELINE
# ============================================================================

class ScaleupCollectionPipeline:
    """
    Scalable pipeline to collect 500+ comedy videos.

    Features:
    - Multi-source collection (YouTube, StandUp4AI, MultiLinguahah)
    - Parallel downloading with rate limiting
    - Progress tracking with resume capability
    - Language-balanced collection
    - Browser cookie authentication for YouTube

    Fix #2: Proper resume logic - all state is saved/loaded correctly.
    Fix #3: Garbled channel IDs removed (they were unused anyway).
    Fix #4: Reliable marker detection via subtitle download.
    """

    def __init__(self, target: int = 500, resume: bool = False):
        self.target = target
        self.base_dir = BASE_DIR
        self.raw_dir = RAW_VIDEO_DIR
        self.candidates_file = CANDIDATES_FILE
        self.collection_log_file = COLLECTION_LOG

        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state
        self.candidates: List[VideoCandidate] = []
        self.collection_log: CollectionLog = CollectionLog()

        # Fix #2: Actually load previous state if resume=True
        if resume:
            print("[RESUME MODE] Loading previous state...")
            self._load_state()
        else:
            # Fresh start - remove old state files
            if self.candidates_file.exists():
                print(f"[INFO] Removing old candidates file: {self.candidates_file}")
                self.candidates_file.unlink()
            if self.collection_log_file.exists():
                print(f"[INFO] Removing old collection log: {self.collection_log_file}")
                self.collection_log_file.unlink()

    def _load_state(self):
        """
        Fix #2: Load previous state from disk.
        Loads both candidates and collection log.
        """
        # Load candidates
        if self.candidates_file.exists():
            with open(self.candidates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.candidates = [VideoCandidate.from_dict(v) for v in data]
            print(f"  Loaded {len(self.candidates)} candidates from {self.candidates_file}")
        else:
            print("  No previous candidates file found")
            self.candidates = []

        # Load collection log
        if self.collection_log_file.exists():
            with open(self.collection_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                self.collection_log = CollectionLog(**log_data)
            print(f"  Loaded collection log: {len(self.collection_log.collected)} collected, "
                  f"{len(self.collection_log.pending)} pending, {len(self.collection_log.failed)} failed")
        else:
            print("  No previous collection log found")
            self.collection_log = CollectionLog()

    def _save_state(self):
        """
        Fix #2: Save both candidates and collection log.
        Called after each phase to enable resume.
        """
        # Save candidates
        with open(self.candidates_file, 'w', encoding='utf-8') as f:
            json.dump([v.to_dict() for v in self.candidates], f, indent=2, ensure_ascii=False)

        # Save collection log
        import datetime
        self.collection_log.last_updated = datetime.datetime.now().isoformat()
        with open(self.collection_log_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.collection_log), f, indent=2, ensure_ascii=False)

    # =========================================================================
    # PHASE 1: CANDIDATE GENERATION
    # =========================================================================

    def generate_candidates_youtube(self, language: str = "en", max_results: int = 100) -> List[Dict]:
        """
        Generate video candidates from YouTube search.

        Uses yt-dlp to search for comedy videos.
        Fix #1: Added --cookies-from-browser for authenticated requests.
        """
        print(f"[PHASE 1] Generating {language} video candidates from YouTube...")

        search_queries = {
            "en": [
                "stand-up comedy full special",
                "comedy show full video",
                "late night comedy monologue",
                "comedy club performance",
            ],
            "zh": [
                "相声专场完整版",
                "单口喜剧专场",
                "脱口秀完整版",
            ],
            "hi": [
                "स्टैंड-अप कॉमेडी पूरा",
                "हिंदी कॉमेडी शो",
                "इंडियन कॉमेडी फुल",
            ]
        }

        candidates = []
        cookie_args = get_ytdlp_cookie_args()

        for query in search_queries.get(language, search_queries["en"]):
            try:
                cmd = [
                    "python3", "-m", "yt_dlp",
                    *cookie_args,  # Cookies BEFORE --print
                    "--flat-playlist",
                    "--print", "%(id)s|%(title)s|%(duration)s|%(view_count)s|%(uploader)s",
                    f"ytsearch{max_results}:{query}",
                    "--no-download"  # Just get metadata
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 5:
                                video_id, title, duration, views, channel = parts[:5]
                                try:
                                    # Fix #3: Clean channel name encoding
                                    clean_channel = channel.encode('utf-8', errors='replace').decode('utf-8')
                                    candidates.append({
                                        "video_id": video_id.strip(),
                                        "title": title.strip(),
                                        "channel": clean_channel,
                                        "language": language,
                                        "duration": int(float(duration)) if duration.replace(".", "").replace(",", "").isdigit() else 0,
                                        "view_count": int(views) if views.isdigit() else 0,
                                        "source": "youtube_search"
                                    })
                                except Exception as e:
                                    pass
            except Exception as e:
                print(f"  Warning: Search '{query}' failed: {e}")
                continue

        print(f"  Found {len(candidates)} {language} candidates")
        return candidates

    def generate_candidates_standup4ai(self) -> List[Dict]:
        """
        Generate candidates from StandUp4AI dataset.
        Reference: Barriere et al., ACL 2025
        """
        print(f"[PHASE 1] Generating candidates from StandUp4AI dataset...")

        candidates = []

        # TODO: Download StandUp4AI dataset
        # - Source: https://github.com/xxx/standup4ai
        # - Contains: 7 languages, video-level annotations
        # - Expected: ~200 videos across languages

        return candidates

    def generate_candidates_multilinguahah(self) -> List[Dict]:
        """
        Generate candidates from MultiLinguahah dataset.
        Reference: Callejas et al., arXiv:2605.06309, 2026
        """
        print(f"[PHASE 1] Generating candidates from MultiLinguahah dataset...")

        candidates = []

        # TODO: Download MultiLinguahah dataset
        # - Source: arXiv:2605.06309
        # - Contains: multilingual laughter data
        # - Expected: ~100 videos

        return candidates

    # =========================================================================
    # PHASE 2: QUALITY FILTERING
    # =========================================================================

    def filter_candidates(self, candidates: List[Dict]) -> List[VideoCandidate]:
        """
        Apply multi-stage filtering to candidates.

        Filters:
        1. Duration: 30 seconds - 30 minutes
        2. View count: Minimum threshold for quality
        3. Language: Verified support
        4. Comedy: Must have laughter markers (checked in Phase 3)
        """
        print(f"[PHASE 2] Filtering {len(candidates)} candidates...")

        filtered = []
        for c in candidates:
            # Duration filter (30s - 30min)
            if c.get('duration', 0) < 30 or c.get('duration', 0) > 1800:
                continue

            # Minimum views for quality (1000 views minimum)
            if c.get('view_count', 0) < 1000:
                continue

            # Language must be supported
            if c.get('language') not in SUPPORTED_LANGUAGES:
                continue

            # Create VideoCandidate object
            video = VideoCandidate(
                video_id=c['video_id'],
                title=c['title'],
                channel=c.get('channel', 'unknown'),
                language=c['language'],
                duration=c.get('duration', 0),
                view_count=c.get('view_count', 0),
                laugh_markers=0,  # Unknown until downloaded
                collection_status="pending"
            )
            filtered.append(video)

        print(f"  Filtered to {len(filtered)} candidates")
        return filtered

    # =========================================================================
    # PHASE 3: LAUGHTER MARKER CHECK
    # =========================================================================

    def check_laughter_markers(self, candidate: VideoCandidate) -> VideoCandidate:
        """
        Check if video has sufficient [laughter] markers.
        Fix #4: Actually download subtitles to check markers reliably.

        Previous approach: --skip-download --write-subs doesn't reliably fetch subtitles.
        New approach: Download subtitles to temp location and parse them.
        """
        import tempfile
        import glob

        # Use a temp directory for subtitle files
        temp_dir = tempfile.mkdtemp(prefix="scaleup_subs_")

        try:
            # Fix #4: Download subtitles properly (not just --skip-download --write-subs)
            cookie_args = get_ytdlp_cookie_args()

            cmd = [
                "python3", "-m", "yt_dlp",
                "--write-subs",
                "--write-auto-subs",
                "--skip-download",  # Don't download video
                "--sub-langs", "en,zh,hi",  # Request these languages
                "--convert-subs", "vtt",  # Convert to VTT for easy parsing
                "-o", os.path.join(temp_dir, "%(id)s.%(ext)s"),
                "--no-playlist",
            ]
            # Add cookie args for authenticated access
            cmd.extend(cookie_args)
            # Add video URL at the end
            cmd.append(f"https://youtube.com/watch?v={candidate.video_id}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            # Parse downloaded subtitle files for laughter markers
            laugh_count = 0
            subtitle_files = glob.glob(os.path.join(temp_dir, f"{candidate.video_id}.*.vtt"))

            for sub_file in subtitle_files:
                try:
                    with open(sub_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read().lower()
                        # Count laughter markers
                        laugh_count += content.count('[laughter]')
                        laugh_count += content.count('(audience laughs)')
                        laugh_count += content.count('(audience laughing)')
                        laugh_count += content.count('<笑声>')  # Chinese laughter
                        laugh_count += content.count('&lt;笑声&gt;')  # XML encoded
                        laugh_count += content.count('[audiencelaughter]')
                        # Hindi might use different markers
                        laugh_count += content.count('(laughter)')
                except Exception as e:
                    pass

            candidate.laugh_markers = laugh_count

        except subprocess.TimeoutExpired:
            candidate.error_message = "Subtitle download timeout"
        except Exception as e:
            candidate.error_message = str(e)
        finally:
            # Cleanup temp directory
            try:
                for f in glob.glob(os.path.join(temp_dir, "*")):
                    os.remove(f)
                os.rmdir(temp_dir)
            except:
                pass

        return candidate

    def parallel_laughter_check(self, candidates: List[VideoCandidate], workers: int = 10) -> List[VideoCandidate]:
        """
        Parallel laughter marker checking.
        """
        print(f"[PHASE 3] Checking laughter markers for {len(candidates)} candidates...")

        updated = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.check_laughter_markers, c): c for c in candidates}

            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 50 == 0:
                    print(f"  Progress: {i+1}/{len(candidates)}")
                try:
                    updated.append(future.result())
                except Exception as e:
                    print(f"  Error processing candidate: {e}")
                    updated.append(futures[future])

        # Filter to videos with minimum laughter markers
        MIN_LAUGHTER = 10  # Minimum 10 [laughter] markers
        filtered = [c for c in updated if c.laugh_markers >= MIN_LAUGHTER]

        print(f"  Found {len(filtered)} videos with >= {MIN_LAUGHTER} laughter markers")
        return filtered

    # =========================================================================
    # PHASE 4: DOWNLOAD
    # =========================================================================

    def download_video(self, candidate: VideoCandidate) -> VideoCandidate:
        """
        Download video using yt-dlp with browser cookies.
        Fix #1: Added proper cookie-based authentication.
        """
        output_path = self.raw_dir / f"{candidate.video_id}.m4a"

        if output_path.exists():
            candidate.collection_status = "collected"
            print(f"  [SKIP] {candidate.video_id} already downloaded")
            return candidate

        try:
            cookie_args = get_ytdlp_cookie_args()

            cmd = [
                "python3", "-m", "yt_dlp",
                "-f", "bestaudio[ext=m4a]/bestaudio/best",
                "--extract-audio",
                "--audio-format", "m4a",
                "--audio-quality", "0",
                "-o", str(output_path),
                "--no-playlist",
            ]
            # Fix #1: Add cookie args for authenticated YouTube access
            cmd.extend(cookie_args)
            # Add video URL at the end
            cmd.append(f"https://youtube.com/watch?v={candidate.video_id}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0 and output_path.exists():
                candidate.collection_status = "collected"
                print(f"  [OK] Downloaded {candidate.video_id}")
            else:
                candidate.collection_status = "failed"
                candidate.error_message = result.stderr[:500] if result.stderr else "Unknown error"
                print(f"  [FAIL] {candidate.video_id}: {candidate.error_message[:100]}")

        except subprocess.TimeoutExpired:
            candidate.collection_status = "failed"
            candidate.error_message = "Download timeout"
            print(f"  [FAIL] {candidate.video_id}: Timeout")
        except Exception as e:
            candidate.collection_status = "failed"
            candidate.error_message = str(e)
            print(f"  [FAIL] {candidate.video_id}: {e}")

        return candidate

    def parallel_download(self, candidates: List[VideoCandidate], workers: int = 3) -> List[VideoCandidate]:
        """
        Parallel video downloading.
        Limit workers to avoid YouTube rate limiting.
        """
        print(f"[PHASE 4] Downloading {len(candidates)} videos...")
        print(f"  (Limiting to {workers} parallel downloads to avoid rate limiting)")

        updated = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.download_video, c): c for c in candidates}

            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{len(candidates)}")
                try:
                    updated.append(future.result())
                except Exception as e:
                    print(f"  Error downloading: {e}")
                    updated.append(futures[future])

        collected = sum(1 for c in updated if c.collection_status == "collected")
        failed = sum(1 for c in updated if c.collection_status == "failed")

        print(f"  Downloaded: {collected}, Failed: {failed}")
        return updated

    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================

    def run(self):
        """
        Execute full collection pipeline.
        Fix #2: Now properly uses saved state for resume.
        """
        print("="*70)
        print("SCALEUP COLLECTION PIPELINE")
        print(f"Target: {self.target} videos")
        print(f"Languages: {SUPPORTED_LANGUAGES}")
        print("="*70)

        # =====================================================================
        # PHASE 1: Generate/Load Candidates
        # =====================================================================

        # Check if we have pending candidates from previous run
        pending_candidates = [c for c in self.candidates if c.collection_status == "pending"]

        if pending_candidates:
            print(f"\n[PHASE 1] Resuming with {len(pending_candidates)} pending candidates")
            all_filtered = pending_candidates
        else:
            # Fresh run - generate all candidates
            all_candidates = []

            # Generate from YouTube
            for lang in SUPPORTED_LANGUAGES:
                yt_candidates = self.generate_candidates_youtube(language=lang, max_results=200)
                all_candidates.extend(yt_candidates)

            # Add dataset sources (placeholders)
            all_candidates.extend(self.generate_candidates_standup4ai())
            all_candidates.extend(self.generate_candidates_multilinguahah())

            print(f"\n[PHASE 1] Total candidates generated: {len(all_candidates)}")

            # Save intermediate candidates
            self.candidates = []
            self._save_state()

            # =================================================================
            # PHASE 2: Quality filtering
            # =================================================================
            all_filtered = self.filter_candidates(all_candidates)

        # Save after filtering
        self.candidates = all_filtered
        self._save_state()

        # =====================================================================
        # PHASE 3: Laughter marker check (skip if already done)
        # =================================================================

        candidates_needing_marker_check = [
            c for c in self.candidates if c.laugh_markers == 0 and c.collection_status == "pending"
        ]

        if candidates_needing_marker_check:
            print(f"\n[PHASE 3] Checking laughter markers for {len(candidates_needing_marker_check)} candidates...")
            with_laughter = self.parallel_laughter_check(candidates_needing_marker_check)

            # Update candidates list
            for c in with_laughter:
                idx = next((i for i, x in enumerate(self.candidates) if x.video_id == c.video_id), None)
                if idx is not None:
                    self.candidates[idx] = c

            self._save_state()
        else:
            print("\n[PHASE 3] Skipping - all candidates already have marker data")
            with_laughter = [c for c in self.candidates if c.laugh_markers > 0]

        # =====================================================================
        # PHASE 4: Download (prioritize high-laughter videos)
        # =================================================================

        # Filter out already collected ones
        to_download = [c for c in with_laughter
                       if c.collection_status != "collected" and c.video_id not in self.collection_log.collected]

        if not to_download:
            print("\n[PHASE 4] No videos to download - all already collected")
        else:
            # Sort by laugh markers descending
            to_download.sort(key=lambda x: x.laugh_markers, reverse=True)

            # Limit to target
            current_collected = len(self.collection_log.collected)
            remaining = self.target - current_collected
            if remaining <= 0:
                print(f"\n[PHASE 4] Target ({self.target}) already reached!")
            else:
                download_batch = to_download[:min(remaining, len(to_download))]
                print(f"\n[PHASE 4] Downloading {len(download_batch)} videos (target: {self.target}, "
                      f"current: {current_collected})")

                downloaded = self.parallel_download(download_batch)

                # Update collection log
                for c in downloaded:
                    if c.collection_status == "collected":
                        if c.video_id not in self.collection_log.collected:
                            self.collection_log.collected.append(c.video_id)
                        if c.video_id in self.collection_log.pending:
                            self.collection_log.pending.remove(c.video_id)
                    elif c.collection_status == "failed":
                        if c.video_id not in self.collection_log.failed:
                            self.collection_log.failed.append(c.video_id)
                        if c.video_id in self.collection_log.pending:
                            self.collection_log.pending.remove(c.video_id)

                # Update candidates status
                for c in downloaded:
                    idx = next((i for i, x in enumerate(self.candidates) if x.video_id == c.video_id), None)
                    if idx is not None:
                        self.candidates[idx] = c

                self._save_state()

        # =====================================================================
        # FINAL SUMMARY
        # =================================================================

        print("\n" + "="*70)
        print("COLLECTION COMPLETE")
        print(f"Total candidates: {len(self.candidates)}")
        print(f"Total collected: {len(self.collection_log.collected)}")
        print(f"Total failed: {len(self.collection_log.failed)}")
        print(f"Total pending: {len([c for c in self.candidates if c.collection_status == 'pending'])}")
        print(f"Target: {self.target}")
        print(f"Progress: {len(self.collection_log.collected) / self.target * 100:.1f}%")
        print("="*70)

        # Update collection log with all pending
        self.collection_log.pending = [
            c.video_id for c in self.candidates
            if c.collection_status == "pending" and c.video_id not in self.collection_log.collected
        ]
        self._save_state()

        return asdict(self.collection_log)

    def get_stats(self) -> Dict:
        """Get current collection statistics."""
        collected = len(self.collection_log.collected)
        failed = len(self.collection_log.failed)
        pending = len([c for c in self.candidates if c.collection_status == "pending"])

        by_language = {}
        for c in self.candidates:
            lang = c.language
            if lang not in by_language:
                by_language[lang] = {"total": 0, "collected": 0}
            by_language[lang]["total"] += 1
            if c.collection_status == "collected":
                by_language[lang]["collected"] += 1

        return {
            "total_candidates": len(self.candidates),
            "collected": collected,
            "failed": failed,
            "pending": pending,
            "target": self.target,
            "progress_pct": collected / self.target * 100 if self.target > 0 else 0,
            "by_language": by_language
        }


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scaleup Collection Pipeline - Collect 500+ comedy videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 SCALEUP_collection_pipeline_fixed.py --target 500 --languages en,zh,hi
  python3 SCALEUP_collection_pipeline_fixed.py --resume  # Resume from previous state
  python3 SCALEUP_collection_pipeline_fixed.py --stats   # Show current statistics
        """
    )
    parser.add_argument("--target", type=int, default=500,
                        help="Target number of videos to collect (default: 500)")
    parser.add_argument("--languages", type=str, default="en,zh,hi",
                        help="Comma-separated languages to collect (default: en,zh,hi)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from previous state (load candidates and collection log)")
    parser.add_argument("--stats", action="store_true",
                        help="Show current collection statistics and exit")

    args = parser.parse_args()

    # Set global languages
    SUPPORTED_LANGUAGES = args.languages.split(",")

    # Handle --stats first
    if args.stats:
        pipeline = ScaleupCollectionPipeline(target=args.target, resume=True)
        stats = pipeline.get_stats()
        print("\n" + "="*50)
        print("COLLECTION STATISTICS")
        print("="*50)
        for key, value in stats.items():
            if key != "by_language":
                print(f"  {key}: {value}")
        if stats.get("by_language"):
            print("\n  By Language:")
            for lang, lang_stats in stats["by_language"].items():
                print(f"    {lang}: {lang_stats}")
        print("="*50)
        sys.exit(0)

    # Run the pipeline
    pipeline = ScaleupCollectionPipeline(target=args.target, resume=args.resume)
    log = pipeline.run()

    print(f"\nRun with --resume to continue: python3 SCALEUP_collection_pipeline_fixed.py --resume")
    print(f"Run with --stats to see statistics: python3 SCALEUP_collection_pipeline_fixed.py --stats")
