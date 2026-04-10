#!/usr/bin/env python3
"""
LinkedIn Post & Comment Scraper
Scrapes all posts and comments from a LinkedIn profile for the last 5 years
Creates an organized markdown database grouped by topics
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
import time
from dateutil import parser as date_parser

class LinkedInScraper:
    def __init__(self, email: str, password: str, profile_url: str):
        self.email = email
        self.password = password
        self.profile_url = profile_url
        self.posts = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize_browser(self, headless: bool = False):
        """Initialize browser with Chrome channel if available, else Chromium"""
        playwright = await async_playwright().start()

        browser = None
        # Try Chrome channel first (if installed), then fallback to Chromium
        try:
            browser = await playwright.chromium.launch(
                channel='chrome',
                headless=headless,
                args=['--start-maximized']
            )
            print("✅ Using Chrome channel")
        except Exception as e:
            print(f"⚠️ Chrome channel unavailable, falling back to Chromium: {e}")
            browser = await playwright.chromium.launch(
                headless=headless,
                args=['--start-maximized']
            )
            print("✅ Using bundled Chromium")

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        self.browser = browser
        self.page = await context.new_page()
        
        # Set longer timeout for slow pages
        self.page.set_default_timeout(120000)  # 2 minutes
        
    async def login(self):
        """Login to LinkedIn"""
        print("🔐 Logging into LinkedIn...")
        
        await self.page.goto("https://www.linkedin.com/login", wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        # Fill email
        email_selector = 'input[id="username"], input[name="session_key"]'
        try:
            await self.page.wait_for_selector(email_selector, timeout=15000)
            await self.page.fill(email_selector, self.email)
        except Exception as e:
            print(f"⚠️ Email field issue: {e}")
            # Try alternative approach
            await self.page.fill('input[type="text"]', self.email)
        
        # Fill password
        password_selector = 'input[id="password"], input[name="session_password"]'
        try:
            await self.page.wait_for_selector(password_selector, timeout=15000)
            await self.page.fill(password_selector, self.password)
        except Exception as e:
            print(f"⚠️ Password field issue: {e}")
            await self.page.fill('input[type="password"]', self.password)
        
        # Click login button
        login_button = 'button[type="submit"], button.btn-primary'
        await asyncio.sleep(1)
        await self.page.click(login_button)
        
        # Wait for navigation with more flexible approach
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
        except:
            # Page might still be loading, continue anyway
            await asyncio.sleep(5)
        
        # Check if login was successful
        current_url = self.page.url
        if 'feed' in current_url or 'linkedin.com/in/' in current_url:
            print("✅ Login successful!")
            return True
        else:
            # Check for security challenges
            if 'challenge' in current_url.lower() or 'checkpoint' in current_url.lower():
                print("⚠️ LinkedIn security check detected.")
                print("⏳ Waiting up to 2 minutes for automatic resolution or manual completion...")
                # Give time for automatic resolution or manual intervention
                max_wait_seconds = 120  # 2 minutes
                waited = 0
                check_interval = 3
                while waited < max_wait_seconds:
                    await asyncio.sleep(check_interval)
                    waited += check_interval
                    try:
                        url = self.page.url
                        if 'feed' in url or 'linkedin.com/in/' in url or 'recent-activity' in url or 'linkedin.com/feed' in url:
                            print("✅ Navigation successful. Continuing...")
                            await asyncio.sleep(2)
                            return True
                    except:
                        pass
                print("⚠️ Still on checkpoint page. Attempting to proceed anyway...")
                # Try to continue anyway - might work
                await asyncio.sleep(3)
                return True  # Return True to attempt to continue
            else:
                print(f"❌ Login may have failed. Current URL: {current_url}")
                return False
    
    async def navigate_to_profile(self):
        """Navigate to the target profile"""
        print(f"📄 Navigating to profile: {self.profile_url}")
        await self.page.goto(self.profile_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        # Check if we need to handle any prompts or login issues
        current_url = self.page.url
        if 'checkpoint' in current_url.lower() or 'challenge' in current_url.lower():
            print("⚠️ Still on security page. Waiting 30 seconds for manual completion...")
            print("👆 If browser is visible, please complete any security checks now")
            await asyncio.sleep(30)
        
        # Try to navigate to activity/posts section directly
        activity_url = self.profile_url.rstrip('/') + '/recent-activity/all/'
        print(f"📋 Navigating to activity feed: {activity_url}")
        await self.page.goto(activity_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        # Scroll to load profile content
        await self.scroll_page()
    
    async def scroll_page(self, pause_time: float = 1.0):
        """Scroll page to load all content"""
        previous_height = await self.page.evaluate('document.body.scrollHeight')
        scroll_count = 0
        
        while scroll_count < 50:  # Limit scrolls to prevent infinite loops
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(pause_time)
            
            current_height = await self.page.evaluate('document.body.scrollHeight')
            if current_height == previous_height:
                break
            
            previous_height = current_height
            scroll_count += 1
    
    async def extract_posts(self) -> List[Dict]:
        """Extract all posts from the profile activity section"""
        print("📝 Extracting posts...")
        
        posts = []
        
        # Navigate to activity section
        try:
            # Try to find and click "Posts" or "Activity" tab
            activity_selectors = [
                'button[aria-label*="Show all posts"]',
                'a[href*="/recent-activity/"]',
                'button:has-text("Posts")',
                'a:has-text("Posts")',
                '[data-control-name="profile_tab_posts"]'
            ]
            
            activity_found = False
            for selector in activity_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await asyncio.sleep(2)
                        activity_found = True
                        break
                except:
                    continue
            
            if not activity_found:
                # Try direct URL
                activity_url = self.profile_url.rstrip('/') + '/recent-activity/all/'
                await self.page.goto(activity_url)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
            
            # Scroll to load all posts
            await self.scroll_page(pause_time=2.0)
            
        except Exception as e:
            print(f"⚠️ Could not navigate to activity section: {e}")
            # Continue with current page
            
        # Extract posts using various selectors
        post_selectors = [
            'div.feed-shared-update-v2',
            'article[data-id]',
            'div[data-urn*="activity"]',
            '.feed-shared-update-v2',
            'div.update-components-text'
        ]
        
        extracted_count = 0
        for selector in post_selectors:
            try:
                post_elements = await self.page.query_selector_all(selector)
                print(f"Found {len(post_elements)} potential posts with selector: {selector}")
                
                for element in post_elements:
                    try:
                        post_data = await self.extract_post_data(element)
                        if post_data and post_data not in posts:
                            posts.append(post_data)
                            extracted_count += 1
                    except Exception as e:
                        continue
                        
                if extracted_count > 0:
                    break
            except Exception as e:
                continue
        
        # Alternative: Extract from page content using JavaScript
        if len(posts) == 0:
            posts = await self.extract_posts_via_js()
        
        print(f"✅ Extracted {len(posts)} posts")
        return posts
    
    async def extract_post_data(self, element) -> Optional[Dict]:
        """Extract data from a single post element"""
        try:
            # Extract text content
            text_content = await element.inner_text()
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # Extract timestamp
            timestamp = None
            time_elements = await element.query_selector_all('time, [class*="time"], [data-test-id="timestamp"]')
            for time_elem in time_elements:
                try:
                    datetime_attr = await time_elem.get_attribute('datetime')
                    if datetime_attr:
                        timestamp = datetime_attr
                        break
                    else:
                        time_text = await time_elem.inner_text()
                        timestamp = self.parse_relative_time(time_text)
                except:
                    continue
            
            # Extract engagement metrics
            reactions = 0
            comments = 0
            shares = 0
            
            engagement_selectors = [
                '[class*="reaction"]',
                '[class*="engagement"]',
                'span:has-text("reaction")',
                'span:has-text("comment")'
            ]
            
            for sel in engagement_selectors:
                try:
                    eng_elements = await element.query_selector_all(sel)
                    for eng in eng_elements:
                        text = await eng.inner_text()
                        # Extract numbers
                        numbers = re.findall(r'\d+', text.replace(',', ''))
                        if numbers:
                            if 'reaction' in text.lower():
                                reactions = max(reactions, int(numbers[0]))
                            elif 'comment' in text.lower():
                                comments = max(comments, int(numbers[0]))
                except:
                    continue
            
            # Check if post is within last 5 years
            if timestamp:
                post_date = self.parse_date(timestamp)
                five_years_ago = datetime.now() - timedelta(days=5*365)
                if post_date and post_date < five_years_ago:
                    return None  # Skip posts older than 5 years
            
            return {
                'text': text_content.strip(),
                'timestamp': timestamp or 'Unknown',
                'reactions': reactions,
                'comments': comments,
                'shares': shares,
                'date': post_date.isoformat() if timestamp else None
            }
            
        except Exception as e:
            return None
    
    async def extract_posts_via_js(self) -> List[Dict]:
        """Extract posts using JavaScript injection"""
        print("📝 Trying JavaScript-based extraction...")
        
        script = """
        () => {
            const posts = [];
            const selectors = [
                'div.feed-shared-update-v2',
                'article[data-id]',
                'div[data-urn*="activity"]'
            ];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    const text = el.innerText || el.textContent || '';
                    if (text.length > 50) {
                        const timeEl = el.querySelector('time') || el.querySelector('[datetime]');
                        const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;
                        
                        posts.push({
                            text: text.trim(),
                            timestamp: timestamp,
                            html: el.outerHTML.substring(0, 1000)
                        });
                    }
                }
            }
            
            return posts.filter((p, i, arr) => 
                arr.findIndex(pp => pp.text.substring(0, 100) === p.text.substring(0, 100)) === i
            );
        }
        """
        
        try:
            posts_data = await self.page.evaluate(script)
            posts = []
            
            for post_data in posts_data:
                if post_data.get('text'):
                    post_date = self.parse_date(post_data.get('timestamp', ''))
                    five_years_ago = datetime.now() - timedelta(days=5*365)
                    
                    if not post_date or post_date >= five_years_ago:
                        posts.append({
                            'text': post_data['text'],
                            'timestamp': post_data.get('timestamp', 'Unknown'),
                            'date': post_date.isoformat() if post_date else None,
                            'reactions': 0,
                            'comments': 0,
                            'shares': 0
                        })
            
            return posts
            
        except Exception as e:
            print(f"⚠️ JavaScript extraction failed: {e}")
            return []
    
    async def extract_comments_for_post(self, post_element) -> List[Dict]:
        """Extract top comments for a post"""
        comments = []
        
        try:
            # Wait a bit for comments to load if they were just expanded
            await asyncio.sleep(1.5)
            
            # Multiple strategies to extract comments
            comment_selectors = [
                'div.comments-post-meta__main-content',
                'div.comment__main-content',
                'div.comments-comment-item__main-content',
                '[class*="comment"]',
                'div.feed-shared-comment',
                'div.comments-comment-item',
                'li.comments-comment-item'
            ]
            
            all_comment_elements = []
            for selector in comment_selectors:
                try:
                    elements = await post_element.query_selector_all(selector)
                    all_comment_elements.extend(elements)
                except:
                    continue
            
            # Also try extracting from parent container
            try:
                parent = await post_element.query_selector('..')
                if parent:
                    for selector in comment_selectors:
                        try:
                            elements = await parent.query_selector_all(selector)
                            all_comment_elements.extend(elements)
                        except:
                            continue
            except:
                pass
            
            # Remove duplicates by checking inner text similarity
            seen_texts = set()
            for comment_el in all_comment_elements[:20]:  # Limit to first 20
                try:
                    comment_text = await comment_el.inner_text()
                    if not comment_text or len(comment_text.strip()) < 10:
                        continue
                    
                    # Check for duplicates
                    text_hash = comment_text.strip()[:100]
                    if text_hash in seen_texts:
                        continue
                    seen_texts.add(text_hash)
                    
                    # Try to extract likes/reactions using multiple methods
                    likes = 0
                    
                    # Method 1: Look for like button/reaction count
                    like_selectors = [
                        '[class*="like"]',
                        '[class*="reaction"]',
                        'button[aria-label*="like"]',
                        'span[class*="reactions-count"]'
                    ]
                    
                    for like_sel in like_selectors:
                        try:
                            like_el = await comment_el.query_selector(like_sel)
                            if like_el:
                                like_text = await like_el.inner_text()
                                numbers = re.findall(r'\d+', like_text.replace(',', ''))
                                if numbers:
                                    likes = max(likes, int(numbers[0]))
                        except:
                            continue
                    
                    # Method 2: Extract from aria-label
                    try:
                        aria_label = await comment_el.get_attribute('aria-label')
                        if aria_label:
                            numbers = re.findall(r'(\d+)\s*like', aria_label.lower())
                            if numbers:
                                likes = max(likes, int(numbers[0]))
                    except:
                        pass
                    
                    # Clean comment text (remove extra whitespace, "like" buttons text, etc.)
                    clean_text = re.sub(r'\s+', ' ', comment_text.strip())
                    clean_text = re.sub(r'^\d+\s*like[s]?\s*', '', clean_text, flags=re.IGNORECASE)
                    
                    if len(clean_text) > 10:
                        comments.append({
                            'text': clean_text,
                            'likes': likes
                        })
                except Exception as e:
                    continue
            
            # If no comments found with selectors, try JavaScript extraction
            if not comments:
                comments = await self.extract_comments_via_js(post_element)
                        
        except Exception as e:
            print(f"  ⚠️ Error extracting comments: {e}")
        
        # Remove duplicates again and sort by likes
        unique_comments = []
        seen = set()
        for comment in comments:
            text_key = comment['text'][:150].lower()
            if text_key not in seen:
                seen.add(text_key)
                unique_comments.append(comment)
        
        # Sort by likes and return top 3
        unique_comments.sort(key=lambda x: x['likes'], reverse=True)
        return unique_comments[:3]
    
    async def extract_comments_via_js(self, post_element) -> List[Dict]:
        """Extract comments using JavaScript"""
        try:
            script = """
            (element) => {
                const comments = [];
                const commentSelectors = [
                    'div.comments-post-meta__main-content',
                    'div.comment__main-content',
                    'div.comments-comment-item__main-content',
                    'div.comments-comment-item'
                ];
                
                for (const selector of commentSelectors) {
                    const elements = element.querySelectorAll(selector);
                    for (const el of elements) {
                        const text = el.innerText || el.textContent || '';
                        if (text.length > 10) {
                            // Extract likes
                            let likes = 0;
                            const likeEl = el.querySelector('[class*="like"], [class*="reaction"]');
                            if (likeEl) {
                                const likeText = likeEl.innerText || '';
                                const match = likeText.match(/(\\d+)/);
                                if (match) {
                                    likes = parseInt(match[1]);
                                }
                            }
                            
                            comments.push({
                                text: text.trim(),
                                likes: likes
                            });
                        }
                    }
                }
                
                return comments;
            }
            """
            
            comments_data = await self.page.evaluate(script, post_element)
            return comments_data[:3] if comments_data else []
            
        except:
            return []
    
    def parse_relative_time(self, time_str: str) -> Optional[str]:
        """Parse relative time strings like '2 days ago', '1 month ago'"""
        if not time_str:
            return None
        
        time_str = time_str.lower()
        now = datetime.now()
        
        # Match patterns like "2 days ago", "1 month ago"
        patterns = [
            (r'(\d+)\s*years?\s*ago', 365),
            (r'(\d+)\s*months?\s*ago', 30),
            (r'(\d+)\s*weeks?\s*ago', 7),
            (r'(\d+)\s*days?\s*ago', 1),
            (r'(\d+)\s*hours?\s*ago', 1/24),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, time_str)
            if match:
                value = int(match.group(1))
                days_ago = value * multiplier
                date = now - timedelta(days=days_ago)
                return date.isoformat()
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try dateutil parser (more flexible)
        try:
            return date_parser.parse(date_str)
        except:
            pass
        
        # Try common formats
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19], fmt)
            except:
                continue
        
        # Try relative time parsing
        rel_date = self.parse_relative_time(date_str)
        if rel_date:
            try:
                return datetime.fromisoformat(rel_date)
            except:
                pass
        
        return None
    
    def categorize_posts(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Intelligently categorize posts by topics"""
        print("📊 Categorizing posts by topics...")
        
        # Keywords for different topics
        topic_keywords = {
            'Technology & AI': ['ai', 'artificial intelligence', 'machine learning', 'tech', 'software', 'coding', 'programming', 'developer', 'innovation', 'digital', 'automation', 'algorithm'],
            'Career & Professional Development': ['career', 'professional', 'work', 'job', 'interview', 'resume', 'leadership', 'management', 'skills', 'growth', 'success', 'opportunity'],
            'Business & Strategy': ['business', 'strategy', 'entrepreneurship', 'startup', 'investment', 'finance', 'market', 'industry', 'company', 'organization'],
            'Networking & Relationships': ['network', 'connection', 'relationship', 'collaboration', 'team', 'community', 'partnership'],
            'Thought Leadership': ['insight', 'perspective', 'thought', 'opinion', 'view', 'belief', 'philosophy'],
            'Education & Learning': ['learn', 'education', 'course', 'training', 'knowledge', 'skill', 'teaching', 'mentor'],
            'Industry Updates & News': ['announcement', 'update', 'news', 'launch', 'release', 'event', 'conference'],
            'Personal Reflections': ['journey', 'experience', 'story', 'challenge', 'grateful', 'thankful', 'reflection']
        }
        
        categorized = {topic: [] for topic in topic_keywords.keys()}
        categorized['Other'] = []
        
        for post in posts:
            post_text_lower = post['text'].lower()
            assigned = False
            
            # Score each topic
            topic_scores = {}
            for topic, keywords in topic_keywords.items():
                score = sum(1 for keyword in keywords if keyword in post_text_lower)
                if score > 0:
                    topic_scores[topic] = score
            
            # Assign to highest scoring topic
            if topic_scores:
                best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
                categorized[best_topic].append(post)
                assigned = True
            
            if not assigned:
                categorized['Other'].append(post)
        
        # Remove empty categories
        categorized = {k: v for k, v in categorized.items() if v}
        
        print(f"✅ Categorized {len(posts)} posts into {len(categorized)} topics")
        return categorized
    
    async def extract_comments_for_all_posts(self):
        """Extract comments for all posts by navigating and clicking"""
        print("💬 Extracting comments for posts...")
        
        # Navigate to activity feed if not already there
        activity_url = self.profile_url.rstrip('/') + '/recent-activity/all/'
        await self.page.goto(activity_url)
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Get all post elements again
        post_elements = await self.page.query_selector_all('div.feed-shared-update-v2, article[data-id]')
        
        print(f"Found {len(post_elements)} post elements to process")
        
        for i, post_element in enumerate(post_elements[:len(self.posts)]):
            try:
                print(f"Processing comments for post {i+1}/{min(len(post_elements), len(self.posts))}...")
                
                # Scroll post into view
                await post_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # Try to find and click "Show comments" or "X comments"
                comment_button_selectors = [
                    'button[aria-label*="comment"]',
                    'button:has-text("comment")',
                    'a[data-test-id="comments-button"]',
                    'button.feed-shared-social-action-bar__comment-button'
                ]
                
                comments = []
                for selector in comment_button_selectors:
                    try:
                        comment_btn = await post_element.query_selector(selector)
                        if comment_btn:
                            await comment_btn.click()
                            await asyncio.sleep(2)  # Wait for comments to load
                            
                            # Extract comments
                            comments = await self.extract_comments_for_post(post_element)
                            break
                    except:
                        continue
                
                # If no comments button found, try to extract directly
                if not comments:
                    comments = await self.extract_comments_for_post(post_element)
                
                # Assign comments to corresponding post
                if i < len(self.posts):
                    self.posts[i]['comments'] = comments
                    self.posts[i]['comment_count'] = len(comments)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Error extracting comments for post {i+1}: {e}")
                if i < len(self.posts):
                    self.posts[i]['comments'] = []
                    self.posts[i]['comment_count'] = 0
                continue
    
    async def scrape_all_data(self):
        """Main scraping function"""
        try:
            # Use visible mode so user can complete LinkedIn checkpoint if needed
            await self.initialize_browser(headless=False)
            print("✅ Running in visible mode - you can interact if needed")
            
            login_success = await self.login()
            if not login_success:
                print("⚠️ Login had issues, but continuing anyway...")
            
            await self.navigate_to_profile()
            
            posts = await self.extract_posts()
            self.posts = posts
            
            # Save progress after posts extraction
            if len(self.posts) > 0:
                print(f"💾 Saving progress: {len(self.posts)} posts extracted so far...")
                self.generate_markdown('linkedin_jagadeesh_posts_database_partial.md')
            
            # Extract comments for all posts
            if len(self.posts) > 0:
                await self.extract_comments_for_all_posts()
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            # Save whatever we have
            if len(self.posts) > 0:
                print(f"💾 Saving partial results: {len(self.posts)} posts...")
                self.generate_markdown('linkedin_jagadeesh_posts_database_error_recovery.md')
            import traceback
            traceback.print_exc()
        finally:
            if self.browser:
                await self.browser.close()
    
    def generate_markdown(self, output_file: str = 'linkedin_posts_database.md'):
        """Generate organized markdown database"""
        print(f"📄 Generating markdown database: {output_file}")
        
        categorized = self.categorize_posts(self.posts)
        
        md_content = []
        md_content.append("# LinkedIn Posts Database")
        md_content.append(f"\n**Profile:** {self.profile_url}")
        md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"**Total Posts:** {len(self.posts)}")
        md_content.append(f"**Date Range:** Last 5 years\n")
        md_content.append("---\n")
        
        # Table of contents
        md_content.append("## Table of Contents\n")
        for topic in sorted(categorized.keys()):
            count = len(categorized[topic])
            anchor = topic.lower().replace(' ', '-').replace('&', '')
            md_content.append(f"- [{topic}](#{anchor}) ({count} posts)")
        md_content.append("\n---\n")
        
        # Content by category
        for topic, posts in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            md_content.append(f"\n## {topic}\n")
            md_content.append(f"*{len(posts)} posts*\n")
            
            for idx, post in enumerate(posts, 1):
                md_content.append(f"\n### Post {idx}\n")
                md_content.append(f"**Date:** {post.get('date', post.get('timestamp', 'Unknown'))}\n")
                md_content.append(f"**Engagement:** {post.get('reactions', 0)} reactions, {post.get('comments', 0)} comments, {post.get('shares', 0)} shares\n")
                md_content.append(f"\n**Content:**\n")
                md_content.append(f"{post['text']}\n")
                
                # Add top 3 comments
                post_comments = post.get('comments', [])
                # Ensure post_comments is a list, not an int
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
                    md_content.append(f"*No comments extracted or comments not available*\n")
                
                md_content.append("\n---\n")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        # Also save JSON backup
        json_file = output_file.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'profile_url': self.profile_url,
                'generated_at': datetime.now().isoformat(),
                'total_posts': len(self.posts),
                'categories': {k: len(v) for k, v in categorized.items()},
                'posts_by_category': categorized
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Markdown database saved to {output_file}")
        print(f"✅ JSON backup saved to {json_file}")
        
        # Print summary
        print("\n📊 Summary:")
        print(f"  Total Posts: {len(self.posts)}")
        print(f"  Categories: {len(categorized)}")
        for topic, posts_list in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    - {topic}: {len(posts_list)} posts")


async def main():
    """Main execution function"""
    email = "sdas22@gmail.com"
    password = "Abfl@321"
    profile_url = "https://www.linkedin.com/in/jagadeesh-j/"
    
    print("=" * 60)
    print("LinkedIn Post & Comment Scraper")
    print("=" * 60)
    print(f"\n📧 Email: {email}")
    print(f"👤 Profile: {profile_url}")
    print(f"📅 Time Range: Last 5 years")
    print(f"\n🚀 Starting scraper...\n")
    
    scraper = LinkedInScraper(email, password, profile_url)
    
    try:
        await scraper.scrape_all_data()
        
        if len(scraper.posts) == 0:
            print("\n⚠️ No posts found. Possible reasons:")
            print("  - Profile may not have public posts")
            print("  - Posts may be older than 5 years")
            print("  - LinkedIn structure may have changed")
            print("\n💡 Try manually checking the profile URL first.")
            return
        
        print(f"\n✅ Scraped {len(scraper.posts)} posts!")
        print("📄 Generating markdown database...")
        
        scraper.generate_markdown('linkedin_jagadeesh_posts_database.md')
        
        print("\n" + "=" * 60)
        print("🎉 Scraping completed successfully!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  ✅ Total posts scraped: {len(scraper.posts)}")
        print(f"  📁 Markdown file: linkedin_jagadeesh_posts_database.md")
        print(f"  📁 JSON backup: linkedin_jagadeesh_posts_database.json")
        print("\n💡 You can now view the organized database!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        print("💾 Saving partial data...")
        if len(scraper.posts) > 0:
            scraper.generate_markdown('linkedin_jagadeesh_posts_database_partial.md')
            print(f"✅ Partial database saved ({len(scraper.posts)} posts)")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("  1. Check your internet connection")
        print("  2. Verify LinkedIn credentials")
        print("  3. Ensure Playwright is installed: python3 -m playwright install chromium")
        print("  4. Try running the setup script: ./setup_linkedin_scraper.sh")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
