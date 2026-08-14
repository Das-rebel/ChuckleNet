#!/usr/bin/env python3
"""
Collection Monitor
==================
Monitors the 1000 video collection pipeline progress.
Shows real-time stats and quality distribution.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/quality_checkpoint.json'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'

# ============================================================================
# LOAD STATE
# ============================================================================

def load_state():
    """Load current collection state."""
    state = {
        'checkpoint': None,
        'processed_count': 0,
        'audio_count': 0,
        'wavlm_count': 0,
    }
    
    # Load checkpoint
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            state['checkpoint'] = json.load(f)
    
    # Count processed files
    if os.path.exists(PROCESSED_DIR):
        state['processed_count'] = len([f for f in os.listdir(PROCESSED_DIR) if f.endswith('.json')])
    
    # Count audio files
    if os.path.exists(AUDIO_DIR):
        state['audio_count'] = len([f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')])
    
    # Count WavLM embeddings
    if os.path.exists(WAVLM_DIR):
        state['wavlm_count'] = len([f for f in os.listdir(WAVLM_DIR) if f.endswith('.json')])
    
    return state

# ============================================================================
# DISPLAY
# ============================================================================

def print_dashboard(state):
    """Print monitoring dashboard."""
    cp = state['checkpoint']
    
    print("\n" + "=" * 70)
    print(" 1000 VIDEO COLLECTION MONITOR")
    print("=" * 70)
    print(f" Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    if cp:
        total = cp.get('total_collected', 0)
        assessed = len(cp.get('assessed_videos', {}))
        stats = cp.get('quality_stats', {})
        
        # Progress bar
        progress = total / 1000 * 100
        bar_len = 40
        filled = int(bar_len * progress / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        print(f"\n Progress: [{bar}] {progress:.1f}%")
        print(f" Collected: {total} / 1000 videos")
        print(f" Assessed: {assessed} videos")
        
        # Quality distribution
        print(f"\n Quality Distribution:")
        total_q = sum(stats.values())
        for tier in ['excellent', 'good', 'acceptable', 'low', 'rejected']:
            count = stats.get(tier, 0)
            pct = count / total_q * 100 if total_q > 0 else 0
            emoji = {'excellent': '🌟', 'good': '✅', 'acceptable': '👍', 
                    'low': '⚠️', 'rejected': '❌'}.get(tier, '•')
            print(f"   {emoji} {tier:<12}: {count:>5} ({pct:>5.1f}%)")
        
        # Collection rate
        collected = cp.get('collected_videos', {})
        if collected:
            tiers = {'excellent': 0, 'good': 0, 'acceptable': 0}
            for v in collected.values():
                t = v.get('quality_tier', 'unknown')
                if t in tiers:
                    tiers[t] += 1
            print(f"\n To-Process Breakdown:")
            print(f"   🌟 Excellent: {tiers['excellent']} (priority 1)")
            print(f"   ✅ Good: {tiers['good']} (priority 2)")
            print(f"   👍 Acceptable: {tiers['acceptable']} (priority 3)")
    else:
        print("\n No checkpoint found - collection not started")
    
    # File counts
    print(f"\n Files on Disk:")
    print(f"   Processed metadata: {state['processed_count']}")
    print(f"   Audio files: {state['audio_count']}")
    print(f"   WavLM embeddings: {state['wavlm_count']}")
    
    print("\n" + "=" * 70)

# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    print("Starting collection monitor (Ctrl+C to stop)...")
    
    last_total = -1
    while True:
        state = load_state()
        cp = state['checkpoint']
        
        current_total = cp.get('total_collected', 0) if cp else 0
        
        # Only print if changed
        if current_total != last_total:
            print_dashboard(state)
            last_total = current_total
        
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitor stopped")
