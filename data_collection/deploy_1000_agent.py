#!/usr/bin/env python3
"""
Deploy Parallel Collection Agents
================================
Launches multiple collection agents in parallel using different
search strategies to collect 1000 YouTube comedy videos.

Usage:
    python3 deploy_1000_agent.py --agents 5
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# ============================================================================
# CONFIG
# ============================================================================

TARGET_VIDEOS = 1000
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/collection_checkpoint.json'
COLLECTION_SCRIPT = '/Users/Subho/autonomous_laughter_prediction/data_collection/collect_youtube_fast.py'

os.makedirs(PROCESSED_DIR, exist_ok=True)

# ============================================================================
# SEARCH STRATEGIES (per agent)
# ============================================================================

AGENT_CONFIGS = [
    {
        'name': 'US_UK_Comedy',
        'queries': [
            'stand up comedy full special 2024',
            'stand up comedy Netflix 2023',
            'comedy central stand up full show',
            'late night comedy special',
            '宋飞正传 全集',
            'stand up comedy HBO full',
        ]
    },
    {
        'name': 'CrowdWork',
        'queries': [
            'stand up crowd work全场爆笑',
            'comedy crowd work interaction',
            'stand up comedy improvisation',
            'crowd work stand up Netflix',
        ]
    },
    {
        'name': 'APAC_Comedy',
        'queries': [
            'Australian stand up comedy full',
            'Irish stand up comedy full special',
            'British comedy stand up full show',
            'Canadian stand up comedy full',
            '新加坡脱口秀全场笑声',
            '马来西亚华人喜剧 full',
        ]
    },
    {
        'name': 'Indian_Comedy',
        'queries': [
            'Indian stand up comedy full special',
            'Bollywood comedy roast full',
            'Indian comedy Netflix special',
            'vir das comedy full show',
        ]
    },
    {
        'name': 'Clean_Podcast',
        'queries': [
            'clean stand up comedy full',
            'family friendly comedy special',
            'comedy podcast full episode',
            'late night comedy monologue',
        ]
    },
]

# ============================================================================
# CHECKPOINT
# ============================================================================

def load_checkpoint() -> Dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'collected_videos': {},
        'total_collected': 0,
        'total_processed': 0,
        'agents_completed': [],
        'last_updated': datetime.now().isoformat()
    }

def save_checkpoint(cp: Dict):
    cp['last_updated'] = datetime.now().isoformat()
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2)

# ============================================================================
# SINGLE AGENT COLLECTION
# ============================================================================

def run_collection_agent(config: Dict, agent_id: int) -> Dict:
    """Run a single collection agent."""
    print(f"\n{'='*60}")
    print(f"AGENT {agent_id}: {config['name']}")
    print(f"{'='*60}")
    
    result = {
        'agent_id': agent_id,
        'name': config['name'],
        'started': datetime.now().isoformat(),
        'queries': len(config['queries']),
        'videos_collected': 0,
        'status': 'running'
    }
    
    collected = []
    
    for query in config['queries']:
        print(f"\n  Query: {query[:50]}...")
        
        # Run collection
        try:
            cmd_result = subprocess.run(
                ['python3', COLLECTION_SCRIPT, '--query', query, '--max', '30'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse output
            for line in cmd_result.stdout.split('\n'):
                if 'video_id:' in line:
                    vid = line.split('video_id:')[1].strip()
                    collected.append(vid)
            
            print(f"    Collected: {len(collected)} videos so far")
            
        except subprocess.TimeoutExpired:
            print(f"    Timeout for query")
        except Exception as e:
            print(f"    Error: {e}")
    
    result['videos_collected'] = len(collected)
    result['completed'] = datetime.now().isoformat()
    result['status'] = 'completed'
    
    return result

# ============================================================================
# PARALLEL DEPLOYMENT
# ============================================================================

def deploy_parallel_agents(n_agents: int):
    """Deploy multiple collection agents in parallel."""
    
    print("=" * 70)
    print(f"DEPLOYING {n_agents} PARALLEL COLLECTION AGENTS")
    print("=" * 70)
    
    # Select agents
    agents_to_run = AGENT_CONFIGS[:n_agents]
    print(f"\nRunning {len(agents_to_run)} agents:")
    for i, a in enumerate(agents_to_run):
        print(f"  {i}: {a['name']} ({len(a['queries'])} queries)")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    
    # Run agents sequentially (for now, since we don't have true parallel execution)
    # TODO: Use threading/multiprocessing for true parallelism
    
    results = []
    for i, config in enumerate(agents_to_run):
        result = run_collection_agent(config, i)
        results.append(result)
        
        # Update checkpoint
        checkpoint['agents_completed'].append(config['name'])
        save_checkpoint(checkpoint)
        
        print(f"\n  Agent {i} complete: {result['videos_collected']} videos")
    
    # Summary
    total = sum(r['videos_collected'] for r in results)
    
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total videos collected: {total}")
    
    for r in results:
        print(f"  {r['name']}: {r['videos_collected']} videos")
    
    return results

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Deploy Parallel Collection')
    parser.add_argument('--agents', type=int, default=5, help='Number of parallel agents')
    args = parser.parse_args()
    
    results = deploy_parallel_agents(args.agents)
    
    # Save final results
    with open('/tmp/collection_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to /tmp/collection_results.json")

if __name__ == '__main__':
    main()
