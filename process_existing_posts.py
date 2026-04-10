#!/usr/bin/env python3
"""
Process existing scraped posts with all enhancements
Use this to reprocess existing JSON files with combined answers
"""

import json
import asyncio
from datetime import datetime
from linkedin_post_scraper_enhanced import EnhancedLinkedInScraper

async def process_existing_posts():
    """Process existing posts from JSON file"""
    scraper = EnhancedLinkedInScraper("sdas22@gmail.com", "Abfl@321", "https://www.linkedin.com/in/jagadeesh-j/")
    
    # Try to load existing posts
    json_files = [
        'linkedin_jagadeesh_posts_database_error_recovery.json',
        'linkedin_jagadeesh_posts_database_partial.json',
        'linkedin_jagadeesh_posts_database_treequest.json'
    ]
    
    posts = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract posts
            if 'posts_by_category' in data:
                for cat, post_list in data['posts_by_category'].items():
                    posts.extend(post_list)
            elif isinstance(data, list):
                posts = data
            elif 'posts' in data:
                posts = data['posts']
            
            if posts:
                print(f"✅ Loaded {len(posts)} posts from {json_file}")
                scraper.posts = posts
                break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️ Error loading {json_file}: {e}")
            continue
    
    if not posts:
        print("❌ No posts found in existing files")
        return
    
    # Generate markdown with all enhancements
    await scraper.generate_markdown('linkedin_jagadeesh_posts_database_enhanced.md')
    
    print("\n🎉 Processing complete!")

if __name__ == "__main__":
    asyncio.run(process_existing_posts())
