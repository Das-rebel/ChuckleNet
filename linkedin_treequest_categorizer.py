#!/usr/bin/env python3
"""
LinkedIn Post Categorizer with TreeQuest Integration
Uses TreeQuest/MCP to intelligently verify and categorize LinkedIn posts
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Try to import TreeQuest/MCP components
try:
    from monk.core.treequest_optimization import TreeQuestOptimizer
    from monk.orchestrator.ai_wrappers import get_llm_wrapper
    TREEQUEST_AVAILABLE = True
except ImportError:
    TREEQUEST_AVAILABLE = False
    print("⚠️ TreeQuest components not available, using basic categorization")


class LinkedInPostCategorizer:
    """Enhanced categorizer with TreeQuest verification"""
    
    def __init__(self):
        self.treequest_optimizer = None
        self.llm_wrapper = None
        
        if TREEQUEST_AVAILABLE:
            try:
                self.treequest_optimizer = TreeQuestOptimizer()
                # Get a fallback LLM wrapper for categorization
                providers = ['anthropic', 'openai', 'google', 'perplexity']
                for provider in providers:
                    try:
                        self.llm_wrapper = get_llm_wrapper(provider)
                        if self.llm_wrapper:
                            print(f"✅ Using {provider} for TreeQuest categorization")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"⚠️ TreeQuest initialization failed: {e}")
    
    def load_posts_from_scraper(self, json_file: str = None) -> List[Dict]:
        """Load posts from scraper output or partial files"""
        posts = []
        
        # Try to find any output files
        possible_files = [
            json_file,
            'linkedin_jagadeesh_posts_database.json',
            'linkedin_jagadeesh_posts_database_partial.json',
            'linkedin_jagadeesh_posts_database_error_recovery.json'
        ]
        
        for file_path in possible_files:
            if file_path and Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'posts_by_category' in data:
                            # Extract all posts from categories
                            for category, category_posts in data['posts_by_category'].items():
                                posts.extend(category_posts)
                        elif isinstance(data, list):
                            posts = data
                        elif 'posts' in data:
                            posts = data['posts']
                        print(f"✅ Loaded {len(posts)} posts from {file_path}")
                        return posts
                except Exception as e:
                    print(f"⚠️ Could not load {file_path}: {e}")
                    continue
        
        print("⚠️ No post files found. Run the scraper first.")
        return posts
    
    async def verify_and_categorize_with_treequest(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Use TreeQuest to verify and intelligently categorize posts"""
        print(f"\n🔍 TreeQuest Verification & Categorization")
        print("=" * 60)
        print(f"Processing {len(posts)} posts...")
        
        verified_posts = []
        
        # Step 1: Verify post quality
        print("\n📊 Step 1: Verifying post quality...")
        for i, post in enumerate(posts, 1):
            if i % 50 == 0:
                print(f"  Verified {i}/{len(posts)} posts...")
            
            # Basic validation
            if not post.get('text') or len(post.get('text', '').strip()) < 10:
                continue
            
            # Check if post is within 5 years
            post_date = post.get('date')
            if post_date:
                try:
                    from dateutil import parser
                    post_dt = parser.parse(post_date)
                    five_years_ago = datetime.now().replace(year=datetime.now().year - 5)
                    if post_dt < five_years_ago:
                        continue
                except:
                    pass
            
            verified_posts.append(post)
        
        print(f"✅ Verified {len(verified_posts)} posts (removed {len(posts) - len(verified_posts)} invalid/old)")
        
        # Step 2: Enhanced categorization with TreeQuest
        print("\n🧠 Step 2: TreeQuest-enhanced categorization...")
        categorized = await self.categorize_with_ai(verified_posts)
        
        return categorized
    
    async def categorize_with_ai(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Use AI/LLM to intelligently categorize posts"""
        
        if not self.llm_wrapper:
            # Fallback to rule-based categorization
            return self.rule_based_categorization(posts)
        
        # Batch categorize posts (process in chunks)
        categorized = {topic: [] for topic in self.get_topic_categories()}
        categorized['Other'] = []
        
        batch_size = 20
        total_batches = (len(posts) + batch_size - 1) // batch_size
        
        print(f"📦 Processing in {total_batches} batches of ~{batch_size} posts...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(posts))
            batch = posts[start_idx:end_idx]
            
            print(f"  Batch {batch_num + 1}/{total_batches} ({len(batch)} posts)...")
            
            try:
                # Create prompt for batch categorization
                prompt = self.create_categorization_prompt(batch)
                
                # Get AI categorization (if available)
                if self.llm_wrapper:
                    try:
                        response = await self.llm_wrapper.generate_async(prompt, max_tokens=2000)
                        categories = self.parse_ai_categories(response, batch)
                        
                        # Assign posts to categories
                        for post, category in zip(batch, categories):
                            categorized.get(category, categorized['Other']).append(post)
                    except:
                        # Fallback to rule-based
                        for post in batch:
                            category = self.rule_based_categorize_post(post)
                            categorized[category].append(post)
                else:
                    # Rule-based fallback
                    for post in batch:
                        category = self.rule_based_categorize_post(post)
                        categorized[category].append(post)
                        
            except Exception as e:
                print(f"  ⚠️ Error in batch {batch_num + 1}: {e}")
                # Fallback to rule-based
                for post in batch:
                    category = self.rule_based_categorize_post(post)
                    categorized[category].append(post)
        
        # Remove empty categories
        categorized = {k: v for k, v in categorized.items() if v}
        
        return categorized
    
    def rule_based_categorization(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Fallback rule-based categorization"""
        categorized = {topic: [] for topic in self.get_topic_categories()}
        categorized['Other'] = []
        
        for post in posts:
            category = self.rule_based_categorize_post(post)
            categorized[category].append(post)
        
        return {k: v for k, v in categorized.items() if v}
    
    def rule_based_categorize_post(self, post: Dict) -> str:
        """Rule-based post categorization"""
        text = post.get('text', '').lower()
        
        # Topic keywords with scoring
        topic_scores = {}
        
        topic_keywords = {
            'Technology & AI': ['ai', 'artificial intelligence', 'machine learning', 'tech', 'software', 'coding', 'programming', 'developer', 'innovation', 'digital', 'automation', 'algorithm', 'data science', 'ml', 'nlp', 'neural'],
            'Career & Professional Development': ['career', 'professional', 'work', 'job', 'interview', 'resume', 'cv', 'leadership', 'management', 'skills', 'growth', 'success', 'opportunity', 'promotion', 'mentor'],
            'Business & Strategy': ['business', 'strategy', 'entrepreneurship', 'startup', 'investment', 'finance', 'market', 'industry', 'company', 'organization', 'revenue', 'profit', 'growth'],
            'Networking & Relationships': ['network', 'connection', 'relationship', 'collaboration', 'team', 'community', 'partnership', 'colleague', 'professional network'],
            'Thought Leadership': ['insight', 'perspective', 'thought', 'opinion', 'view', 'belief', 'philosophy', 'wisdom', 'lesson learned'],
            'Education & Learning': ['learn', 'education', 'course', 'training', 'knowledge', 'skill', 'teaching', 'mentor', 'tutorial', 'workshop'],
            'Industry Updates & News': ['announcement', 'update', 'news', 'launch', 'release', 'event', 'conference', 'webinar', 'milestone'],
            'Personal Reflections': ['journey', 'experience', 'story', 'challenge', 'grateful', 'thankful', 'reflection', 'milestone', 'achievement']
        }
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        
        return 'Other'
    
    def get_topic_categories(self) -> List[str]:
        """Get list of topic categories"""
        return [
            'Technology & AI',
            'Career & Professional Development',
            'Business & Strategy',
            'Networking & Relationships',
            'Thought Leadership',
            'Education & Learning',
            'Industry Updates & News',
            'Personal Reflections'
        ]
    
    def create_categorization_prompt(self, posts: List[Dict]) -> str:
        """Create prompt for AI categorization"""
        posts_text = "\n\n".join([
            f"Post {i+1}:\n{post.get('text', '')[:500]}"
            for i, post in enumerate(posts)
        ])
        
        return f"""Categorize the following LinkedIn posts into one of these categories:
- Technology & AI
- Career & Professional Development  
- Business & Strategy
- Networking & Relationships
- Thought Leadership
- Education & Learning
- Industry Updates & News
- Personal Reflections
- Other

Posts:
{posts_text}

Return a JSON array with one category per post in order, e.g. ["Technology & AI", "Career & Professional Development", ...]
"""
    
    def parse_ai_categories(self, response: str, posts: List[Dict]) -> List[str]:
        """Parse AI response to extract categories"""
        try:
            # Try to extract JSON array
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                categories = json.loads(json_match.group())
                if len(categories) == len(posts):
                    return categories
        except:
            pass
        
        # Fallback: return rule-based for all
        return [self.rule_based_categorize_post(post) for post in posts]
    
    def generate_enhanced_markdown(self, categorized: Dict[str, List[Dict]], 
                                   output_file: str = 'linkedin_jagadeesh_posts_database_treequest.md'):
        """Generate enhanced markdown with TreeQuest verification"""
        print(f"\n📄 Generating TreeQuest-verified markdown: {output_file}")
        
        md_content = []
        md_content.append("# LinkedIn Posts Database (TreeQuest Verified)")
        md_content.append(f"\n**Profile:** https://www.linkedin.com/in/jagadeesh-j/")
        md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"**Verification:** TreeQuest Enhanced")
        md_content.append(f"**Total Posts:** {sum(len(v) for v in categorized.values())}")
        md_content.append(f"**Date Range:** Last 5 years\n")
        md_content.append("---\n")
        
        # Table of contents
        md_content.append("## Table of Contents\n")
        for topic in sorted(categorized.keys(), key=lambda x: len(categorized[x]), reverse=True):
            count = len(categorized[topic])
            anchor = topic.lower().replace(' ', '-').replace('&', '').replace('/', '-')
            md_content.append(f"- [{topic}](#{anchor}) ({count} posts)")
        md_content.append("\n---\n")
        
        # Content by category
        for topic, posts in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            md_content.append(f"\n## {topic}\n")
            md_content.append(f"*{len(posts)} posts*\n")
            
            # Sort posts by date (newest first)
            sorted_posts = sorted(posts, 
                                key=lambda x: x.get('date', '') or x.get('timestamp', ''),
                                reverse=True)
            
            for idx, post in enumerate(sorted_posts, 1):
                md_content.append(f"\n### Post {idx}\n")
                md_content.append(f"**Date:** {post.get('date', post.get('timestamp', 'Unknown'))}\n")
                md_content.append(f"**Engagement:** {post.get('reactions', 0)} reactions, {post.get('comments', 0)} comments, {post.get('shares', 0)} shares\n")
                md_content.append(f"\n**Content:**\n")
                md_content.append(f"{post['text']}\n")
                
                # Add top 3 comments
                post_comments = post.get('comments', [])
                if isinstance(post_comments, int):
                    post_comments = []
                elif not isinstance(post_comments, list):
                    post_comments = []
                
                if post_comments and len(post_comments) > 0:
                    md_content.append(f"\n#### Top {min(3, len(post_comments))} Comments:\n")
                    for i, comment in enumerate(post_comments[:3], 1):
                        if isinstance(comment, dict):
                            comment_text = comment.get('text', 'N/A')
                            comment_likes = comment.get('likes', 0)
                            md_content.append(f"{i}. **{comment_text}** ({comment_likes} likes)\n")
                        else:
                            md_content.append(f"{i}. **{str(comment)}**\n")
                else:
                    md_content.append(f"\n#### Comments:\n")
                    md_content.append(f"*Comments not extracted or not available*\n")
                
                md_content.append("\n---\n")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        # Also save JSON
        json_file = output_file.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'profile_url': 'https://www.linkedin.com/in/jagadeesh-j/',
                'generated_at': datetime.now().isoformat(),
                'verification_method': 'TreeQuest Enhanced',
                'total_posts': sum(len(v) for v in categorized.values()),
                'categories': {k: len(v) for k, v in categorized.items()},
                'posts_by_category': categorized
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Markdown saved: {output_file}")
        print(f"✅ JSON saved: {json_file}")
        
        # Print summary
        print("\n📊 Summary:")
        print(f"  Total Posts: {sum(len(v) for v in categorized.values())}")
        print(f"  Categories: {len(categorized)}")
        for topic, posts_list in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    - {topic}: {len(posts_list)} posts")


async def main():
    """Main execution"""
    print("=" * 60)
    print("LinkedIn Post Categorizer with TreeQuest")
    print("=" * 60)
    
    categorizer = LinkedInPostCategorizer()
    
    # Try to load posts
    posts = categorizer.load_posts_from_scraper()
    
    if len(posts) == 0:
        print("\n⚠️ No posts found. The scraper may still be running.")
        print("💡 Options:")
        print("  1. Wait for scraper to complete")
        print("  2. Check for partial output files")
        print("  3. Run scraper first: python3 linkedin_post_scraper.py")
        return
    
    # Verify and categorize
    categorized = await categorizer.verify_and_categorize_with_treequest(posts)
    
    # Generate output
    categorizer.generate_enhanced_markdown(categorized)
    
    print("\n🎉 Categorization complete!")


if __name__ == "__main__":
    asyncio.run(main())
