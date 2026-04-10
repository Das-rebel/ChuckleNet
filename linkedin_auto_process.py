#!/usr/bin/env python3
"""
Auto-process LinkedIn scraper results with TreeQuest verification
Monitors scraper output and processes results automatically
"""

import json
import time
import asyncio
from pathlib import Path
from linkedin_treequest_categorizer import LinkedInPostCategorizer

async def monitor_and_process():
    """Monitor scraper and process when ready"""
    print("🔍 Monitoring LinkedIn scraper output...")
    print("=" * 60)
    
    categorizer = LinkedInPostCategorizer()
    
    # Wait for scraper to finish or find partial results
    max_wait = 600  # 10 minutes
    check_interval = 30  # Check every 30 seconds
    waited = 0
    
    output_files = [
        'linkedin_jagadeesh_posts_database.json',
        'linkedin_jagadeesh_posts_database_partial.json',
        'linkedin_jagadeesh_posts_database_error_recovery.json'
    ]
    
    while waited < max_wait:
        # Check for output files
        for file_path in output_files:
            if Path(file_path).exists():
                print(f"\n✅ Found output file: {file_path}")
                print("🚀 Starting TreeQuest categorization...")
                
                posts = categorizer.load_posts_from_scraper(file_path)
                if len(posts) > 0:
                    categorized = await categorizer.verify_and_categorize_with_treequest(posts)
                    categorizer.generate_enhanced_markdown(categorized)
                    print("\n🎉 Processing complete!")
                    return True
        
        # Check if scraper is still running
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'linkedin_post_scraper'], 
                              capture_output=True)
        if result.returncode != 0:
            print("\n⚠️ Scraper process not found. Checking for any output...")
            # Final check for files
            for file_path in output_files:
                if Path(file_path).exists():
                    posts = categorizer.load_posts_from_scraper(file_path)
                    if len(posts) > 0:
                        categorized = await categorizer.verify_and_categorize_with_treequest(posts)
                        categorizer.generate_enhanced_markdown(categorized)
                        print("\n🎉 Processing complete!")
                        return True
            print("❌ No output files found. Scraper may have failed.")
            return False
        
        print(f"⏳ Waiting... ({waited}/{max_wait}s) - Scraper still running...")
        await asyncio.sleep(check_interval)
        waited += check_interval
    
    print("\n⏰ Timeout reached. Processing any available data...")
    posts = categorizer.load_posts_from_scraper()
    if len(posts) > 0:
        categorized = await categorizer.verify_and_categorize_with_treequest(posts)
        categorizer.generate_enhanced_markdown(categorized)
        return True
    
    return False

if __name__ == "__main__":
    asyncio.run(monitor_and_process())
