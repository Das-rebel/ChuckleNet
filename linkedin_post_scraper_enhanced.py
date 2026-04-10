#!/usr/bin/env python3
"""
LinkedIn Post & Comment Scraper - Enhanced Version
Includes all improvements: date extraction, comment extraction, AI categorization, metadata
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser
import time
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

# Try to import AI wrappers for categorization
try:
    import sys
    sys.path.insert(0, '/Users/Subho/monk')
    # Try different import methods
    try:
        from orchestrator.ai_wrappers import AIWrapperFactory, ModelProvider, BaseAIWrapper
        AI_AVAILABLE = True
    except:
        try:
            from monk.orchestrator.ai_wrappers import AIWrapperFactory, ModelProvider, BaseAIWrapper
            AI_AVAILABLE = True
        except:
            AI_AVAILABLE = False
except ImportError:
    AI_AVAILABLE = False


class EnhancedLinkedInScraper:
    def __init__(self, email: str, password: str, profile_url: str, session_file: str = 'linkedin_session.json'):
        self.email = email
        self.password = password
        self.profile_url = profile_url
        self.session_file = session_file
        self.posts = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.llm_wrapper = None
        
        if AI_AVAILABLE:
            try:
                # Try to get LLM wrapper for AI categorization using factory
                providers = [ModelProvider.ANTHROPIC, ModelProvider.OPENAI, ModelProvider.GEMINI]
                for provider in providers:
                    try:
                        self.llm_wrapper = AIWrapperFactory.create_wrapper(provider)
                        if self.llm_wrapper:
                            print(f"✅ Using {provider.value} for AI categorization")
                            break
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"⚠️ Could not initialize LLM: {e}")
        
    async def initialize_browser(self, headless: bool = False):
        """Initialize browser with session persistence"""
        playwright = await async_playwright().start()

        browser = None
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

        # Try to load saved session
        storage_state = None
        if Path(self.session_file).exists():
            try:
                storage_state = self.session_file
                print(f"📂 Loading saved session from {self.session_file}")
            except:
                pass

        self.context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            storage_state=storage_state
        )

        self.browser = browser
        self.page = await self.context.new_page()
        self.page.set_default_timeout(120000)
        
    async def login(self):
        """Login to LinkedIn with improved navigation"""
        print("🔐 Logging into LinkedIn...")
        
        # Try multiple login page URLs
        login_urls = [
            "https://www.linkedin.com/login",
            "https://www.linkedin.com/uas/login",
            "https://www.linkedin.com/login?fromSignIn=true"
        ]
        
        login_successful = False
        for login_url in login_urls:
            try:
                print(f"  Trying: {login_url}")
                await self.page.goto(login_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(3)
                
                # Check if already logged in
                current_url = self.page.url
                if 'feed' in current_url or '/in/' in current_url:
                    print("✅ Already logged in!")
                    await self.context.storage_state(path=self.session_file)
                    return True
                
                # Try to find email field with multiple selectors
                email_selectors = [
                    'input#username',
                    'input[name="session_key"]',
                    'input[autocomplete="username"]',
                    'input[type="text"][id*="user"]',
                    'input[type="email"]'
                ]
                
                email_filled = False
                for selector in email_selectors:
                    try:
                        email_field = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                        if email_field:
                            await email_field.fill('')
                            await email_field.fill(self.email)
                            email_filled = True
                            print(f"  ✅ Email filled using: {selector}")
                            break
                    except:
                        continue
                
                if not email_filled:
                    print("  ⚠️ Could not find email field, trying alternative...")
                    # Try clicking first and filling
                    try:
                        await self.page.click('body')
                        await asyncio.sleep(1)
                        await self.page.keyboard.type(self.email, delay=100)
                    except:
                        pass
                
                # Try to find password field
                password_selectors = [
                    'input#password',
                    'input[name="session_password"]',
                    'input[type="password"]',
                    'input[autocomplete="current-password"]'
                ]
                
                password_filled = False
                for selector in password_selectors:
                    try:
                        password_field = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                        if password_field:
                            await password_field.fill('')
                            await password_field.fill(self.password)
                            password_filled = True
                            print(f"  ✅ Password filled using: {selector}")
                            break
                    except:
                        continue
                
                if not password_filled:
                    print("  ⚠️ Could not find password field")
                    continue
                
                # Click login button with multiple strategies
                login_selectors = [
                    'button[type="submit"]',
                    'button.btn-primary',
                    'input[type="submit"]',
                    'button:has-text("Sign in")',
                    'button:has-text("Log in")'
                ]
                
                login_clicked = False
                for selector in login_selectors:
                    try:
                        login_btn = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                        if login_btn:
                            await login_btn.click()
                            login_clicked = True
                            print(f"  ✅ Login button clicked using: {selector}")
                            break
                    except:
                        continue
                
                if not login_clicked:
                    # Try pressing Enter
                    try:
                        await self.page.keyboard.press('Enter')
                        print("  ✅ Pressed Enter to submit")
                    except:
                        pass
                
                # Wait for navigation
                await asyncio.sleep(5)
                
                # Check if login was successful
                current_url = self.page.url
                if 'feed' in current_url or '/in/' in current_url or 'linkedin.com/feed' in current_url:
                    print("✅ Login successful!")
                    await self.context.storage_state(path=self.session_file)
                    return True
                
                # Check for security challenge
                if 'challenge' in current_url.lower() or 'checkpoint' in current_url.lower():
                    print("⚠️ LinkedIn security check detected.")
                    print("⏳ Waiting up to 2 minutes for resolution...")
                    max_wait = 120
                    waited = 0
                    while waited < max_wait:
                        await asyncio.sleep(5)
                        waited += 5
                        url = self.page.url
                        if 'feed' in url or '/in/' in url or 'linkedin.com/feed' in url:
                            print("✅ Security check completed. Continuing...")
                            await self.context.storage_state(path=self.session_file)
                            return True
                    print("⚠️ Still on security page, but continuing...")
                    return True
                
                # If we got here and it's still the login page, try next URL
                if 'login' in current_url.lower():
                    print(f"  ⚠️ Still on login page, trying next URL...")
                    continue
                
                # Might have succeeded
                await self.context.storage_state(path=self.session_file)
                return True
                
            except Exception as e:
                print(f"  ⚠️ Error with {login_url}: {e}")
                continue
        
        # If all URLs failed, return False
        print("❌ Could not login with any login URL")
        return False
        
        current_url = self.page.url
        if 'feed' in current_url or 'linkedin.com/in/' in current_url:
            print("✅ Login successful!")
            # Save session after successful login
            await self.context.storage_state(path=self.session_file)
            print(f"💾 Session saved to {self.session_file}")
            return True
        else:
            if 'challenge' in current_url.lower() or 'checkpoint' in current_url.lower():
                print("⚠️ LinkedIn security check detected.")
                print("⏳ Waiting up to 2 minutes for automatic resolution or manual completion...")
                max_wait_seconds = 120
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
                            await self.context.storage_state(path=self.session_file)
                            return True
                    except:
                        pass
                print("⚠️ Still on checkpoint page. Attempting to proceed anyway...")
                await asyncio.sleep(3)
                return True
            else:
                print(f"❌ Login may have failed. Current URL: {current_url}")
                return False
    
    def extract_metadata(self, text: str) -> Dict:
        """Extract hashtags, mentions, and links from post text"""
        hashtags = list(set(re.findall(r'#\w+', text)))
        mentions = list(set(re.findall(r'@[\w\-]+', text)))
        links = list(set(re.findall(r'https?://[^\s\)]+', text)))
        
        return {
            'hashtags': hashtags,
            'mentions': mentions,
            'links': links
        }
    
    async def extract_post_date_enhanced(self, element) -> Optional[datetime]:
        """Enhanced date extraction with multiple strategies"""
        try:
            # Strategy 1: Get from time element with datetime attribute
            time_elem = await element.query_selector('time[datetime]')
            if time_elem:
                dt_str = await time_elem.get_attribute('datetime')
                if dt_str:
                    parsed = self.parse_date(dt_str)
                    if parsed:
                        return parsed
            
            # Strategy 2: Get from time element inner text
            time_text_elems = await element.query_selector_all(
                'time, [class*="time"], [class*="timestamp"], [data-test-id="timestamp"]'
            )
            for time_elem in time_text_elems:
                try:
                    # Try datetime attribute first
                    dt_str = await time_elem.get_attribute('datetime')
                    if dt_str:
                        parsed = self.parse_date(dt_str)
                        if parsed:
                            return parsed
                    
                    # Try inner text
                    text = await time_elem.inner_text()
                    if text:
                        parsed = self.parse_relative_time_enhanced(text)
                        if parsed:
                            return parsed
                except:
                    continue
            
            # Strategy 3: Extract from post text content
            post_text = await element.inner_text()
            if post_text:
                # Look for relative time patterns in text
                patterns = [
                    r'(\d+)\s*(hour|hr)s?\s*ago',
                    r'(\d+)\s*(day|days?)\s*ago',
                    r'(\d+)\s*(week|weeks?|wk)\s*ago',
                    r'(\d+)\s*(month|months?|mo)\s*ago',
                    r'(\d+)\s*(year|years?|yr)\s*ago',
                    r'(\d+)(h|d|w|mo|yr)\s*ago',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, post_text, re.IGNORECASE)
                    if match:
                        value = int(match.group(1))
                        unit = match.group(2).lower() if len(match.groups()) > 1 else match.group(2)
                        parsed = self.calculate_date_from_relative(value, unit)
                        if parsed:
                            return parsed
            
            return None
        except Exception as e:
            return None
    
    def parse_relative_time_enhanced(self, time_str: str) -> Optional[datetime]:
        """Enhanced relative time parsing"""
        if not time_str:
            return None
        
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        patterns = [
            (r'(\d+)\s*(hour|hr)s?\s*ago', lambda v: now - timedelta(hours=v)),
            (r'(\d+)\s*(day|days?)\s*ago', lambda v: now - timedelta(days=v)),
            (r'(\d+)\s*(week|weeks?|wk)\s*ago', lambda v: now - timedelta(weeks=v)),
            (r'(\d+)\s*(month|months?|mo)\s*ago', lambda v: now - relativedelta(months=v)),
            (r'(\d+)\s*(year|years?|yr)\s*ago', lambda v: now - relativedelta(years=v)),
            (r'(\d+)h\s*ago', lambda v: now - timedelta(hours=v)),
            (r'(\d+)d\s*ago', lambda v: now - timedelta(days=v)),
            (r'(\d+)w\s*ago', lambda v: now - timedelta(weeks=v)),
            (r'(\d+)mo\s*ago', lambda v: now - relativedelta(months=v)),
            (r'(\d+)yr\s*ago', lambda v: now - relativedelta(years=v)),
        ]
        
        for pattern, calc_func in patterns:
            match = re.search(pattern, time_str)
            if match:
                value = int(match.group(1))
                try:
                    return calc_func(value)
                except:
                    continue
        
        return None
    
    def calculate_date_from_relative(self, value: int, unit: str) -> Optional[datetime]:
        """Calculate date from relative time"""
        now = datetime.now()
        unit = unit.lower()
        
        try:
            if unit in ['hour', 'hr', 'h']:
                return now - timedelta(hours=value)
            elif unit in ['day', 'days', 'd']:
                return now - timedelta(days=value)
            elif unit in ['week', 'weeks', 'wk', 'w']:
                return now - timedelta(weeks=value)
            elif unit in ['month', 'months', 'mo']:
                return now - relativedelta(months=value)
            elif unit in ['year', 'years', 'yr']:
                return now - relativedelta(years=value)
        except:
            pass
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass

        try:
            return date_parser.parse(date_str)
        except:
            pass

        formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19], fmt)
            except:
                continue

        return None

    async def extract_post_url(self, element) -> Optional[str]:
        """Extract the direct URL to the individual post"""
        try:
            # Strategy 1: Try to get from data attributes
            post_id = None

            # Try multiple data attributes that might contain the post ID
            data_selectors = [
                'data-id',
                'data-urn',
                'data-activity-id',
                'data-id',
                'id'
            ]

            for attr in data_selectors:
                try:
                    value = await element.get_attribute(attr)
                    if value:
                        # Extract post ID from various formats
                        if 'urn:li:activity:' in value:
                            post_id = value.split(':')[-1]
                        elif 'activity-' in value:
                            post_id = value.split('-')[-1]
                        elif value.isdigit():
                            post_id = value
                        elif len(value) > 10:  # Likely a full ID
                            post_id = value

                        if post_id and post_id.isdigit():
                            break
                except:
                    continue

            # Strategy 2: Look for link elements within the post
            if not post_id:
                try:
                    link_elements = await element.query_selector_all('a[href*="/posts/"], a[href*="/activity/"], a[href*="/update/"]')
                    for link_el in link_elements:
                        href = await link_el.get_attribute('href')
                        if href and ('/posts/' in href or '/activity/' in href or '/update/' in href):
                            # Extract post ID from URL
                            import re as regex_module
                            match = regex_module.search(r'/(?:posts|activity|update)/([^/?]+)', href)
                            if match:
                                post_id = match.group(1)
                                break
                except:
                    pass

            # Strategy 3: Try JavaScript extraction
            if not post_id:
                try:
                    script = """
                    (element) => {
                        // Try to find the post ID from various sources
                        let postId = null;

                        // Check data attributes
                        const dataAttrs = ['data-id', 'data-urn', 'data-activity-id', 'id'];
                        for (const attr of dataAttrs) {
                            const value = element.getAttribute(attr);
                            if (value) {
                                if (value.includes('urn:li:activity:')) {
                                    postId = value.split(':')[3];
                                    break;
                                } else if (value.includes('activity-')) {
                                    postId = value.split('-').pop();
                                    break;
                                } else if (/^\\d+$/.test(value)) {
                                    postId = value;
                                    break;
                                }
                            }
                        }

                        // Check for links
                        if (!postId) {
                            const links = element.querySelectorAll('a[href*="/posts/"], a[href*="/activity/"]');
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                if (href) {
                                    const match = href.match(/\\/(?:posts|activity)\\/([^/?]+)/);
                                    if (match) {
                                        postId = match[1];
                                        break;
                                    }
                                }
                            }
                        }

                        return postId;
                    }
                    """
                    post_id = await self.page.evaluate(script, element)
                    if post_id:
                        post_id = str(post_id)
                except:
                    pass

            # If we found a post ID, construct the URL
            if post_id:
                post_url = f"https://www.linkedin.com/posts/jagadeesh-j-{post_id}/"

                # Validate the URL format
                if await self.validate_post_url(post_url):
                    return post_url

            return None

        except Exception as e:
            print(f"  ⚠️ Error extracting post URL: {e}")
            return None

    async def validate_post_url(self, url: str) -> bool:
        """Validate that a post URL looks correct"""
        try:
            # Basic URL format validation
            if not url.startswith('https://www.linkedin.com/posts/'):
                return False

            # Extract post ID from URL
            import re as regex_module
            match = regex_module.search(r'/posts/([^/]+)', url)
            if not match:
                return False

            post_id = match.group(1)

            # Post ID should be alphanumeric and reasonable length
            if not post_id or not post_id.replace('-', '').replace('_', '').isalnum():
                return False

            return True

        except:
            return False
    
    async def extract_engagement_enhanced(self, element) -> Dict:
        """Enhanced engagement extraction"""
        reactions = 0
        comments = 0
        shares = 0
        
        try:
            text = await element.inner_text()
            
            # Multiple patterns for each metric
            patterns = {
                'reactions': [
                    r'(\d+)\s*reaction',
                    r'(\d+)\s*like',
                    r'([\d,]+)\s*reaction',
                ],
                'comments': [
                    r'(\d+)\s*comment',
                    r'(\d+)\s*reply',
                ],
                'shares': [
                    r'(\d+)\s*share',
                    r'(\d+)\s*repost',
                    r'(\d+)\s*repost',
                ]
            }
            
            for metric, metric_patterns in patterns.items():
                for pattern in metric_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value_str = match.group(1).replace(',', '')
                        value = int(value_str)
                        if metric == 'reactions':
                            reactions = max(reactions, value)
                        elif metric == 'comments':
                            comments = max(comments, value)
                        else:
                            shares = max(shares, value)
            
            # Also try aria-labels
            try:
                aria_elements = await element.query_selector_all('[aria-label]')
                for elem in aria_elements:
                    aria_label = await elem.get_attribute('aria-label')
                    if aria_label:
                        numbers = re.findall(r'(\d+)', aria_label.replace(',', ''))
                        if numbers and ('reaction' in aria_label.lower() or 'like' in aria_label.lower()):
                            reactions = max(reactions, int(numbers[0]))
                        if numbers and 'comment' in aria_label.lower():
                            comments = max(comments, int(numbers[0]))
            except:
                pass
            
        except Exception as e:
            pass
        
        return {'reactions': reactions, 'comments': comments, 'shares': shares}
    
    async def extract_comments_enhanced(self, post_element, comment_count: int = 0) -> List[Dict]:
        """Enhanced comment extraction with multiple strategies"""
        comments = []
        
        try:
            # Strategy 1: Click to expand comments
            if comment_count > 0:
                comment_button_selectors = [
                    f'button[aria-label*="{comment_count} comment"]',
                    f'button:has-text("{comment_count} comment")',
                    'button[aria-label*="comment"]',
                    'button:has-text("comment")',
                    'a[data-test-id="comments-button"]',
                ]
                
                for btn_sel in comment_button_selectors:
                    try:
                        btn = await post_element.query_selector(btn_sel)
                        if btn:
                            await btn.scroll_into_view_if_needed()
                            await btn.click()
                            await asyncio.sleep(3)  # Wait for comments to load
                            break
                    except:
                        continue
            
            # Strategy 2: Find and scroll to comments section
            comments_section = await post_element.query_selector(
                '[class*="comments"], [class*="comment-list"], [class*="comments-container"]'
            )
            if comments_section:
                await comments_section.scroll_into_view_if_needed()
                await asyncio.sleep(2)
            
            # Strategy 3: Multiple extraction selectors
            comment_selectors = [
                'div.comments-comment-item__main-content',
                'div.comment__main-content',
                'div.comments-post-meta__main-content',
                'li.comments-comment-item',
                'div[class*="comment-item"]',
                'div[class*="comment-content"]',
            ]
            
            all_comment_elements = []
            for selector in comment_selectors:
                try:
                    elements = await post_element.query_selector_all(selector)
                    if elements:
                        all_comment_elements.extend(elements)
                except:
                    continue
            
            # Also try parent container
            try:
                parent = await post_element.evaluate_handle('el => el.parentElement')
                for selector in comment_selectors:
                    try:
                        elements = await post_element.query_selector_all(selector)
                        if elements:
                            all_comment_elements.extend(elements)
                    except:
                        continue
            except:
                pass
            
            # Extract comments from elements
            seen_texts = set()
            for comment_el in all_comment_elements[:20]:  # Top 20
                try:
                    comment_text = await comment_el.inner_text()
                    if not comment_text or len(comment_text.strip()) < 10:
                        continue
                    
                    # Deduplicate
                    text_hash = comment_text.strip()[:150].lower()
                    if text_hash in seen_texts:
                        continue
                    seen_texts.add(text_hash)
                    
                    # Extract likes
                    likes = 0
                    like_selectors = [
                        '[class*="like"]',
                        '[class*="reaction"]',
                        'button[aria-label*="like"]',
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
                    
                    # Clean comment text
                    clean_text = re.sub(r'\s+', ' ', comment_text.strip())
                    clean_text = re.sub(r'^\d+\s*like[s]?\s*', '', clean_text, flags=re.IGNORECASE)
                    
                    if len(clean_text) > 10:
                        comments.append({
                            'text': clean_text,
                            'likes': likes
                        })
                except:
                    continue
            
            # Strategy 4: JavaScript extraction if nothing found
            if not comments:
                comments = await self.extract_comments_via_js_enhanced(post_element)
            
            # Sort by likes and return top 3
            comments.sort(key=lambda x: x.get('likes', 0), reverse=True)
            return comments[:3]
            
        except Exception as e:
            print(f"  ⚠️ Error extracting comments: {e}")
            return []
    
    async def extract_comments_via_js_enhanced(self, post_element) -> List[Dict]:
        """Enhanced JavaScript-based comment extraction"""
        try:
            script = """
            (element) => {
                const comments = [];
                const selectors = [
                    'div.comments-comment-item__main-content',
                    'div.comment__main-content',
                    'div.comments-post-meta__main-content',
                    'li.comments-comment-item',
                    'div[class*="comment-item"]'
                ];
                
                for (const selector of selectors) {
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
            if comments_data:
                # Remove duplicates and sort
                unique = []
                seen = set()
                for c in comments_data:
                    key = c['text'][:150].lower()
                    if key not in seen:
                        seen.add(key)
                        unique.append(c)
                unique.sort(key=lambda x: x.get('likes', 0), reverse=True)
                return unique[:3]
            return []
            
        except:
            return []
    
    async def create_combined_answer(self, comments: List[Dict], post_text: str) -> Optional[str]:
        """Create a combined answer from top 3 comments using AI"""
        if not comments or len(comments) == 0:
            return None
        
        if not self.llm_wrapper:
            # Fallback: simple concatenation
            combined = " ".join([c.get('text', '') for c in comments[:3]])
            return combined
        
        try:
            comments_text = "\n\n".join([
                f"Comment {i+1} ({c.get('likes', 0)} likes):\n{c.get('text', '')}"
                for i, c in enumerate(comments[:3])
            ])
            
            prompt = f"""You are analyzing LinkedIn post comments. Combine the top 3 comments into a single, coherent, comprehensive answer that synthesizes the key insights from all comments.

Original Post Context:
{post_text[:500]}

Top 3 Comments:
{comments_text}

Create a combined answer that:
1. Synthesizes the main points from all comments
2. Removes redundancy
3. Maintains the key insights
4. Is clear and comprehensive
5. Preserves important details from each comment

Combined Answer:"""
            
            # Use execute_task method from BaseAIWrapper
            if hasattr(self.llm_wrapper, 'execute_task'):
                try:
                    # Check if async
                    if asyncio.iscoroutinefunction(self.llm_wrapper.execute_task):
                        result = await self.llm_wrapper.execute_task(prompt)
                    else:
                        result = self.llm_wrapper.execute_task(prompt)
                    
                    # Handle TaskResult object
                    if result and hasattr(result, 'content'):
                        return result.content.strip()
                    elif result and isinstance(result, str):
                        return result.strip()
                except Exception as e:
                    pass
            elif hasattr(self.llm_wrapper, 'generate_async'):
                response = await self.llm_wrapper.generate_async(prompt, max_tokens=500)
                return response.strip() if response else None
            elif hasattr(self.llm_wrapper, 'generate'):
                response = self.llm_wrapper.generate(prompt, max_tokens=500)
                return response.strip() if response else None
            return None
            
        except Exception as e:
            print(f"  ⚠️ Error creating combined answer: {e}")
            # Fallback to simple concatenation
            return " ".join([c.get('text', '') for c in comments[:3]])
    
    async def categorize_with_ai(self, posts_batch: List[Dict]) -> List[str]:
        """Use AI to categorize posts"""
        if not self.llm_wrapper:
            return None
        
        try:
            posts_text = "\n".join([
                f"Post {i+1}: {post.get('text', '')[:400]}"
                for i, post in enumerate(posts_batch)
            ])
            
            prompt = f"""Categorize these LinkedIn posts from a growth marketing professional (Managing Partner, APJ Growth Company, focuses on digital marketing, brand growth, performance campaigns).

Categories:
- Technology & AI: AI, ML, software development, tech innovation
- Marketing & Advertising: Campaigns, branding, digital marketing, performance marketing
- Business & Strategy: Business growth, strategy, operations, entrepreneurship
- Career & Professional Development: Career advice, professional growth, leadership, skills
- Thought Leadership: Insights, perspectives, opinions, industry views
- Education & Learning: Learning resources, courses, knowledge sharing
- Industry Updates & News: News, announcements, industry updates
- Personal Reflections: Personal stories, experiences, journeys

Posts:
{posts_text}

Return ONLY a JSON array of category names, one per post in order. Be specific and accurate - don't put everything in "Business & Strategy". Example: ["Marketing & Advertising", "Technology & AI", "Business & Strategy"]"""
            
            # Use execute_task method from BaseAIWrapper
            response = None
            if hasattr(self.llm_wrapper, 'execute_task'):
                try:
                    # Check if async
                    if asyncio.iscoroutinefunction(self.llm_wrapper.execute_task):
                        result = await self.llm_wrapper.execute_task(prompt)
                    else:
                        result = self.llm_wrapper.execute_task(prompt)
                    
                    # Handle TaskResult object
                    if result and hasattr(result, 'content'):
                        response = result.content
                    elif result and isinstance(result, str):
                        response = result
                except Exception as e:
                    pass
            elif hasattr(self.llm_wrapper, 'generate_async'):
                response = await self.llm_wrapper.generate_async(prompt, max_tokens=1000)
            elif hasattr(self.llm_wrapper, 'generate'):
                response = self.llm_wrapper.generate(prompt, max_tokens=1000)
            
            if not response:
                return None
            
            # Extract JSON array from response
            import json as json_lib
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                categories = json_lib.loads(json_match.group())
                if len(categories) == len(posts_batch):
                    return categories
            
        except Exception as e:
            print(f"  ⚠️ AI categorization failed: {e}")
        
        return None
    
    # Continue with rest of the scraper methods...
    # (Keeping existing methods for navigation, scrolling, post extraction, etc.)
    
    async def navigate_to_profile(self):
        """Navigate to the target profile"""
        print(f"📄 Navigating to profile: {self.profile_url}")
        await self.page.goto(self.profile_url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(5)
        
        current_url = self.page.url
        if 'checkpoint' in current_url.lower() or 'challenge' in current_url.lower():
            print("⚠️ Still on security page. Waiting 30 seconds for manual completion...")
            await asyncio.sleep(30)
        
        # Try multiple activity feed URLs
        activity_urls = [
            self.profile_url.rstrip('/') + '/recent-activity/all/',
            self.profile_url.rstrip('/') + '/recent-activity/',
            self.profile_url.rstrip('/') + '/detail/recent-activity/',
        ]
        
        for activity_url in activity_urls:
            try:
                print(f"📋 Trying activity feed: {activity_url}")
                # Use domcontentloaded instead of networkidle for faster loading
                await self.page.goto(activity_url, wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(5)
                
                # Wait for content to load (more flexible)
                try:
                    # Try multiple wait strategies
                    await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    await asyncio.sleep(3)
                    
                    # Check if content exists (less strict)
                    has_content = await self.page.evaluate("""
                        () => {
                            const selectors = ['div.feed-shared-update-v2', 'article[data-id]', 'div[class*="update"]', 'div[class*="feed"]'];
                            for (const sel of selectors) {
                                if (document.querySelector(sel)) return true;
                            }
                            return false;
                        }
                    """)
                    
                    if has_content:
                        print(f"✅ Found content on: {activity_url}")
                        break
                    else:
                        print(f"  ⚠️ No content found on: {activity_url}, trying next...")
                        continue
                except:
                    # Continue anyway, we'll try to extract what's there
                    print(f"  ⚠️ Wait timeout, but continuing...")
                    break
            except Exception as e:
                print(f"  ⚠️ Error navigating to {activity_url}: {e}")
                # Don't give up, try next URL
                continue
        
        # Scroll multiple times to load lazy content
        print("📜 Scrolling to load all posts...")
        for i in range(10):  # Scroll 10 times
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            # Check if new content loaded
            height = await self.page.evaluate('document.body.scrollHeight')
            if i > 0:
                await self.page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(1)
        
        # Final scroll down
        await self.scroll_page(pause_time=2.0)
    
    async def scroll_page(self, pause_time: float = 1.0):
        """Scroll page to load all content"""
        previous_height = await self.page.evaluate('document.body.scrollHeight')
        scroll_count = 0
        
        while scroll_count < 50:
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(pause_time)
            
            current_height = await self.page.evaluate('document.body.scrollHeight')
            if current_height == previous_height:
                break
            
            previous_height = current_height
            scroll_count += 1
    
    async def extract_posts(self) -> List[Dict]:
        """Extract all posts with enhanced date and engagement extraction"""
        print("📝 Extracting posts...")
        
        posts = []
        
        # Wait a bit for page to fully load
        await asyncio.sleep(3)
        
        # Try JavaScript extraction first (most reliable)
        print("  Trying JavaScript extraction...")
        js_posts = await self.extract_posts_via_js()
        if js_posts:
            posts.extend(js_posts)
            print(f"  ✅ JavaScript extraction found {len(js_posts)} posts")
        
        # Also try DOM selectors
        post_selectors = [
            'div.feed-shared-update-v2',
            'article[data-id]',
            'div[data-urn*="activity"]',
            'div[class*="feed-shared"]',
            'div[class*="update-components"]',
            'div[class*="activity-item"]',
            'li[class*="activity"]',
        ]
        
        extracted_count = 0
        seen_texts = set()
        
        for selector in post_selectors:
            try:
                post_elements = await self.page.query_selector_all(selector)
                print(f"  Found {len(post_elements)} elements with selector: {selector}")
                
                for element in post_elements:
                    try:
                        post_data = await self.extract_post_data_enhanced(element)
                        if post_data:
                            # Deduplicate by text
                            text_hash = post_data['text'][:100].lower()
                            if text_hash not in seen_texts:
                                seen_texts.add(text_hash)
                                posts.append(post_data)
                                extracted_count += 1
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # Remove duplicates
        unique_posts = []
        seen = set()
        for post in posts:
            text_key = post['text'][:150].lower()
            if text_key not in seen:
                seen.add(text_key)
                unique_posts.append(post)
        
        posts = unique_posts
        
        print(f"✅ Extracted {len(posts)} unique posts")
        return posts
    
    async def extract_post_data_enhanced(self, element) -> Optional[Dict]:
        """Extract post data with all enhancements"""
        try:
            text_content = await element.inner_text()
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # Extract date with enhanced method
            post_date = await self.extract_post_date_enhanced(element)
            
            # Filter by 5 years
            five_years_ago = datetime.now() - relativedelta(years=5)
            if post_date and post_date < five_years_ago:
                return None
            
            # Extract engagement
            engagement = await self.extract_engagement_enhanced(element)
            
            # Extract metadata
            metadata = self.extract_metadata(text_content)
            
            # Extract post URL
            post_url = await self.extract_post_url(element)

            return {
                'text': text_content.strip(),
                'timestamp': post_date.isoformat() if post_date else None,
                'date': post_date.isoformat() if post_date else None,
                'reactions': engagement['reactions'],
                'comments': engagement['comments'],
                'shares': engagement['shares'],
                'hashtags': metadata['hashtags'],
                'mentions': metadata['mentions'],
                'links': metadata['links'],
                'post_url': post_url,
            }
            
        except Exception as e:
            return None
    
    async def extract_posts_via_js(self) -> List[Dict]:
        """JavaScript-based post extraction with comprehensive selectors"""
        script = """
        () => {
            const posts = [];
            const selectors = [
                'div.feed-shared-update-v2',
                'article[data-id]',
                'div[data-urn*="activity"]',
                'div[class*="feed-shared-update"]',
                'div[class*="update-components"]',
                'div[class*="activity-item"]',
                'li[class*="activity"]',
                '[data-id^="urn:li:activity"]'
            ];
            
            const seenTexts = new Set();
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    const text = el.innerText || el.textContent || '';
                    if (text.length > 50) {
                        // Deduplicate
                        const textHash = text.substring(0, 100).toLowerCase();
                        if (seenTexts.has(textHash)) continue;
                        seenTexts.add(textHash);
                        
                        // Try multiple ways to get timestamp
                        let timestamp = null;
                        const timeEl = el.querySelector('time[datetime]');
                        if (timeEl) {
                            timestamp = timeEl.getAttribute('datetime');
                        } else {
                            const timeText = el.querySelector('time');
                            if (timeText) {
                                timestamp = timeText.innerText || timeText.getAttribute('title');
                            }
                        }

                        // Extract post URL
                        let postUrl = null;
                        const postLink = el.querySelector('a[href*="/posts/"], a[href*="/activity/"]');
                        if (postLink) {
                            const href = postLink.getAttribute('href');
                            if (href && (href.includes('/posts/') || href.includes('/activity/'))) {
                                // Convert relative to absolute URL
                                postUrl = new URL(href, 'https://www.linkedin.com').toString();
                            }
                        }
                        
                        // Extract engagement from text
                        const textMatch = text.match(/(\\d+)\\s*(reaction|like|comment|share|repost)/gi);
                        let reactions = 0, comments = 0, shares = 0;
                        if (textMatch) {
                            for (const match of textMatch) {
                                const num = parseInt(match);
                                if (match.toLowerCase().includes('reaction') || match.toLowerCase().includes('like')) {
                                    reactions = Math.max(reactions, num);
                                } else if (match.toLowerCase().includes('comment')) {
                                    comments = Math.max(comments, num);
                                } else if (match.toLowerCase().includes('share') || match.toLowerCase().includes('repost')) {
                                    shares = Math.max(shares, num);
                                }
                            }
                        }
                        
                        posts.push({
                            text: text.trim(),
                            timestamp: timestamp,
                            reactions: reactions,
                            comments: comments,
                            shares: shares,
                            post_url: postUrl
                        });
                    }
                }
            }
            
            return posts;
        }
        """
        
        try:
            posts_data = await self.page.evaluate(script)
            posts = []
            
            for post_data in posts_data:
                if post_data.get('text'):
                    post_date = self.parse_date(post_data.get('timestamp', ''))
                    five_years_ago = datetime.now() - relativedelta(years=5)
                    
                    if not post_date or post_date >= five_years_ago:
                        engagement = self.extract_engagement_enhanced_from_text(post_data.get('text', ''))
                        metadata = self.extract_metadata(post_data['text'])
                        
                        posts.append({
                            'text': post_data['text'],
                            'timestamp': post_data.get('timestamp', None),
                            'date': post_date.isoformat() if post_date else None,
                            'reactions': engagement['reactions'],
                            'comments': engagement['comments'],
                            'shares': engagement['shares'],
                            'hashtags': metadata['hashtags'],
                            'mentions': metadata['mentions'],
                            'links': metadata['links'],
                            'post_url': post_data.get('post_url'),
                        })
            
            return posts
            
        except Exception as e:
            print(f"⚠️ JavaScript extraction failed: {e}")
            return []
    
    def extract_engagement_enhanced_from_text(self, text: str) -> Dict:
        """Extract engagement from text string"""
        reactions = 0
        comments = 0
        shares = 0
        
        patterns = {
            'reactions': [r'(\d+)\s*reaction', r'(\d+)\s*like'],
            'comments': [r'(\d+)\s*comment'],
            'shares': [r'(\d+)\s*share', r'(\d+)\s*repost'],
        }
        
        for metric, metric_patterns in patterns.items():
            for pattern in metric_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = int(match.group(1).replace(',', ''))
                    if metric == 'reactions':
                        reactions = max(reactions, value)
                    elif metric == 'comments':
                        comments = max(comments, value)
                    else:
                        shares = max(shares, value)
        
        return {'reactions': reactions, 'comments': comments, 'shares': shares}
    
    async def extract_comments_for_all_posts(self):
        """Extract comments for all posts with combined answers"""
        print("💬 Extracting comments and creating combined answers...")
        
        activity_url = self.profile_url.rstrip('/') + '/recent-activity/all/'
        await self.page.goto(activity_url, wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        post_elements = await self.page.query_selector_all('div.feed-shared-update-v2, article[data-id]')
        
        print(f"Found {len(post_elements)} post elements to process")
        
        for i, post_element in enumerate(post_elements[:len(self.posts)]):
            try:
                if i % 10 == 0:
                    print(f"Processing comments for post {i+1}/{min(len(post_elements), len(self.posts))}...")
                
                await post_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # Get comment count from post data
                comment_count = 0
                if i < len(self.posts):
                    comment_count = self.posts[i].get('comments', 0)
                
                # Extract comments
                comments = await self.extract_comments_enhanced(post_element, comment_count)
                
                # Create combined answer
                combined_answer = None
                if comments and len(comments) > 0:
                    post_text = self.posts[i].get('text', '') if i < len(self.posts) else ''
                    combined_answer = await self.create_combined_answer(comments, post_text)
                
                # Assign to post
                if i < len(self.posts):
                    self.posts[i]['comments'] = comments
                    self.posts[i]['comment_count'] = len(comments)
                    self.posts[i]['combined_answer'] = combined_answer
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Error extracting comments for post {i+1}: {e}")
                if i < len(self.posts):
                    self.posts[i]['comments'] = []
                    self.posts[i]['comment_count'] = 0
                    self.posts[i]['combined_answer'] = None
                continue
    
    async def scrape_all_data(self):
        """Main scraping function"""
        try:
            await self.initialize_browser(headless=False)
            print("✅ Running in visible mode - you can interact if needed")
            
            login_success = await self.login()
            if not login_success:
                print("⚠️ Login had issues, but continuing anyway...")
            
            await self.navigate_to_profile()
            
            posts = await self.extract_posts()
            self.posts = posts
            
            if len(self.posts) > 0:
                print(f"💾 Saving progress: {len(self.posts)} posts extracted so far...")
                await self.generate_markdown('linkedin_jagadeesh_posts_database_partial.md')
            
            await self.extract_comments_for_all_posts()
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            if len(self.posts) > 0:
                print(f"💾 Saving partial results: {len(self.posts)} posts...")
                await self.generate_markdown('linkedin_jagadeesh_posts_database_error_recovery.md')
        finally:
            if self.browser:
                await self.browser.close()
    
    async def categorize_posts_enhanced(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Enhanced categorization with AI"""
        print("📊 Categorizing posts by topics...")
        
        # Try AI categorization in batches
        categorized = {topic: [] for topic in self.get_topic_categories()}
        categorized['Other'] = []
        
        batch_size = 10
        total_batches = (len(posts) + batch_size - 1) // batch_size
        
        print(f"📦 Processing {total_batches} batches with AI categorization...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(posts))
            batch = posts[start_idx:end_idx]
            
            if batch_num % 5 == 0:
                print(f"  Batch {batch_num + 1}/{total_batches}...")
            
            # Try AI categorization
            ai_categories = None
            if self.llm_wrapper:
                try:
                    ai_categories = await self.categorize_with_ai(batch)
                except Exception as e:
                    print(f"  ⚠️ AI categorization failed for batch: {e}")
                    ai_categories = None
            
            # Assign posts to categories
            if ai_categories and len(ai_categories) == len(batch):
                for post, category in zip(batch, ai_categories):
                    categorized.get(category, categorized['Other']).append(post)
            else:
                # Fallback to rule-based
                for post in batch:
                    category = self.rule_based_categorize_post(post)
                    categorized[category].append(post)
        
        return {k: v for k, v in categorized.items() if v}
    
    def get_topic_categories(self) -> List[str]:
        """Get list of topic categories"""
        return [
            'Technology & AI',
            'Marketing & Advertising',
            'Business & Strategy',
            'Career & Professional Development',
            'Thought Leadership',
            'Education & Learning',
            'Industry Updates & News',
            'Personal Reflections'
        ]
    
    def rule_based_categorize_post(self, post: Dict) -> str:
        """Rule-based fallback categorization"""
        text = post.get('text', '').lower()
        
        topic_keywords = {
            'Technology & AI': ['ai', 'artificial intelligence', 'machine learning', 'tech', 'software', 'coding', 'algorithm', 'data science', 'ml', 'nlp'],
            'Marketing & Advertising': ['marketing', 'campaign', 'advertising', 'brand', 'digital marketing', 'performance', 'cac', 'roi', 'ad', 'media plan'],
            'Business & Strategy': ['business', 'strategy', 'startup', 'entrepreneurship', 'investment', 'company', 'organization'],
            'Career & Professional Development': ['career', 'professional', 'job', 'interview', 'leadership', 'skills', 'growth'],
            'Thought Leadership': ['insight', 'perspective', 'opinion', 'view', 'belief'],
            'Education & Learning': ['learn', 'education', 'course', 'training', 'knowledge'],
            'Industry Updates & News': ['announcement', 'update', 'news', 'launch', 'event'],
            'Personal Reflections': ['journey', 'experience', 'story', 'grateful', 'reflection']
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        
        return 'Other'
    
    async def generate_markdown(self, output_file: str = 'linkedin_jagadeesh_posts_database_enhanced.md'):
        """Generate enhanced markdown with all improvements"""
        print(f"📄 Generating enhanced markdown database: {output_file}")
        
        categorized = await self.categorize_posts_enhanced(self.posts)
        
        md_content = []
        md_content.append("# LinkedIn Posts Database (Enhanced)")
        md_content.append(f"\n**Profile:** {self.profile_url}")
        md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append(f"**Verification:** Enhanced with AI categorization, date extraction, comment extraction")
        md_content.append(f"**Total Posts:** {len(self.posts)}")
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
            
            # Sort posts by date (handle None values)
            def sort_key(post):
                date_str = post.get('date') or post.get('timestamp') or ''
                if date_str and date_str != 'Unknown':
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        return datetime.min
                return datetime.min
            
            sorted_posts = sorted(posts, key=sort_key, reverse=True)
            
            for idx, post in enumerate(sorted_posts, 1):
                md_content.append(f"\n### Post {idx}\n")
                
                # Date
                date_str = post.get('date') or post.get('timestamp') or 'Unknown'
                if date_str and date_str != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d')
                    except:
                        pass
                md_content.append(f"**Date:** {date_str}\n")
                
                # Engagement
                md_content.append(f"**Engagement:** {post.get('reactions', 0)} reactions, {post.get('comments', 0)} comments, {post.get('shares', 0)} shares\n")
                
                # Metadata
                if post.get('hashtags'):
                    md_content.append(f"**Hashtags:** {', '.join(post.get('hashtags', []))}\n")
                if post.get('links'):
                    md_content.append(f"**Links:** {len(post.get('links', []))} link(s)\n")
                
                md_content.append(f"\n**Content:**\n")
                md_content.append(f"{post['text']}\n")
                
                # Combined Answer from top 3 comments
                combined_answer = post.get('combined_answer')
                if combined_answer:
                    md_content.append(f"\n#### 💡 Combined Best Answer (from top 3 comments):\n")
                    md_content.append(f"{combined_answer}\n")
                
                # Individual comments
                post_comments = post.get('comments', [])
                if isinstance(post_comments, int):
                    post_comments = []
                elif not isinstance(post_comments, list):
                    post_comments = []
                
                if post_comments and len(post_comments) > 0:
                    md_content.append(f"\n#### Top {min(3, len(post_comments))} Individual Comments:\n")
                    for i, comment in enumerate(post_comments[:3], 1):
                        if isinstance(comment, dict):
                            comment_text = comment.get('text', 'N/A')
                            comment_likes = comment.get('likes', 0)
                            md_content.append(f"{i}. **{comment_text}** ({comment_likes} likes)\n")
                
                md_content.append("\n---\n")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        # Also save JSON
        json_file = output_file.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'profile_url': self.profile_url,
                'generated_at': datetime.now().isoformat(),
                'verification_method': 'Enhanced with AI',
                'total_posts': len(self.posts),
                'categories': {k: len(v) for k, v in categorized.items()},
                'posts_by_category': categorized
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Markdown saved: {output_file}")
        print(f"✅ JSON saved: {json_file}")
        
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
    print("LinkedIn Post & Comment Scraper - ENHANCED VERSION")
    print("=" * 60)
    print(f"\n📧 Email: {email}")
    print(f"👤 Profile: {profile_url}")
    print(f"📅 Time Range: Last 5 years")
    print(f"\n🚀 Starting enhanced scraper with all improvements...\n")
    
    scraper = EnhancedLinkedInScraper(email, password, profile_url)
    
    try:
        await scraper.scrape_all_data()
        
        if len(scraper.posts) == 0:
            print("\n⚠️ No posts found.")
            return
        
        print(f"\n✅ Scraped {len(scraper.posts)} posts!")
        print("📄 Generating enhanced markdown database...")
        
        await scraper.generate_markdown('linkedin_jagadeesh_posts_database_enhanced.md')
        
        print("\n" + "=" * 60)
        print("🎉 Enhanced scraping completed successfully!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  ✅ Total posts scraped: {len(scraper.posts)}")
        print(f"  📁 Enhanced markdown: linkedin_jagadeesh_posts_database_enhanced.md")
        print(f"  📁 Enhanced JSON: linkedin_jagadeesh_posts_database_enhanced.json")
        print(f"\n✨ Features:")
        print(f"  - ✅ Enhanced date extraction")
        print(f"  - ✅ Improved comment extraction")
        print(f"  - ✅ Combined best answer from top 3 comments")
        print(f"  - ✅ AI-powered categorization")
        print(f"  - ✅ Hashtags, mentions, links extracted")
        print(f"  - ✅ Session persistence")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        if len(scraper.posts) > 0:
            await scraper.generate_markdown('linkedin_jagadeesh_posts_database_partial_enhanced.md')
            print(f"✅ Partial database saved ({len(scraper.posts)} posts)")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
