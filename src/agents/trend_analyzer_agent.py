from abc import abstractmethod
from google.adk.agents import LlmAgent
import os
import logging
from playwright.async_api import Page, async_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
import asyncio
from functools import wraps
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom exceptions
class SocialMediaError(Exception):
    """Base exception for social media related errors."""
    pass

class LoginError(SocialMediaError):
    """Exception raised when login fails."""
    pass

class DataCollectionError(SocialMediaError):
    """Exception raised when data collection fails."""
    pass

# Configuration
@dataclass
class SocialMediaConfig:
    """Configuration for social media data collection."""
    scroll_timeout: int = 3000
    max_retries: int = 3
    retry_delay: int = 2
    max_posts: int = 1000
    cache_dir: Path = Path("data/cache")
    cache_expiry: int = 3600  # 1 hour

# Rate limiting decorator
def rate_limit(calls: int, period: int):
    """Rate limiting decorator."""
    def decorator(func):
        last_reset = time.time()
        calls_made = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            current_time = time.time()
            if current_time - last_reset >= period:
                last_reset = current_time
                calls_made = 0
                
            if calls_made >= calls:
                wait_time = period - (current_time - last_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    last_reset = time.time()
                    calls_made = 0
                    
            calls_made += 1
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class SocialMediaDataGathererBase:
    """Base class for social media data gatherer."""
    
    def __init__(self, config: Optional[SocialMediaConfig] = None):
        self.config = config or SocialMediaConfig()
        self.cache_dir = self.config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def _login(self, page: Page) -> bool:
        """Login to the social media platform."""
        return True
    
    @abstractmethod
    async def _scroll_and_collect_posts(self, page: Page, number_of_posts: int) -> List[Dict]:
        """Scroll and collect posts from the social media platform."""
        return []

    @abstractmethod
    async def _analyze_engagement(self, page: Page) -> Dict:
        """Analyze engagement patterns of recent posts."""
        return {}
    
    @abstractmethod
    def _get_top_performing_posts(self, posts: List[Dict], number_of_top_performing_posts: int) -> List[Dict]:
        """Get the top performing posts from the list of posts."""
        return []
    
    async def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if available and not expired."""
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if time.time() - data['timestamp'] < self.config.cache_expiry:
                    return data['content']
        except Exception as e:
            logger.warning(f"Error reading cache: {str(e)}")
        return None
    
    async def _save_to_cache(self, key: str, data: Dict) -> None:
        """Save data to cache."""
        try:
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'content': data
                }, f)
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")
    
    @abstractmethod
    async def run(self, number_of_posts: int, number_of_top_performing_posts: int) -> List[Dict]:
        """Run the data gatherer."""
        return []

class LinkedInDataGatherer(SocialMediaDataGathererBase):
    def __init__(self, config: Optional[SocialMediaConfig] = None):
        super().__init__(config)
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not found in environment variables")
    
    @rate_limit(calls=5, period=60)  # 5 calls per minute
    async def _login(self, page: Page) -> bool:
        """Login to LinkedIn with retry mechanism."""
        for attempt in range(self.config.max_retries):
            try:
                logger.info("Attempting to login to LinkedIn...")
                await page.goto("https://www.linkedin.com/login")
                await page.fill("#username", self.email)
                await page.fill("#password", self.password)
                await page.click("button[type='submit']")
                
                try:
                    await page.wait_for_selector(".feed-shared-update-v2", timeout=30000)
                    logger.info("Successfully logged in!")
                    return True
                except PlaywrightTimeoutError:
                    logger.warning(f"Login attempt {attempt + 1} timed out")
                    
            except Exception as e:
                logger.error(f"Login attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    
        raise LoginError("Failed to login after maximum retries")
    
    async def _scroll_and_collect_posts(self, page: Page, num_posts: int = 100) -> List[Dict]:
        """Scroll through feed and collect post data with improved error handling."""
        try:
            posts_data = []
            last_height = await page.evaluate('document.body.scrollHeight')
            scroll_count = 0
            no_new_posts_count = 0
            
            logger.info("Starting to scroll and collect posts...")
            while len(posts_data) < num_posts and no_new_posts_count < 3:
                scroll_count += 1
                logger.info(f"Scroll attempt {scroll_count}")
                
                previous_count = len(posts_data)
                
                # Get all visible posts
                posts = await page.query_selector_all(".feed-shared-update-v2")
                logger.info(f"Found {len(posts)} posts on current scroll")
                
                for post in posts:
                    if len(posts_data) >= num_posts:
                        break
                        
                    try:
                        post_data = await self._extract_post_data(post)
                        if post_data and not any(p["content"] == post_data["content"] for p in posts_data):
                            posts_data.append(post_data)
                            logger.info(f"Collected post {len(posts_data)}/{num_posts}")
                            
                    except Exception as e:
                        logger.error(f"Error processing post: {str(e)}")
                        continue
                
                # Check if we got new posts
                if len(posts_data) == previous_count:
                    no_new_posts_count += 1
                else:
                    no_new_posts_count = 0
                
                # Scroll down
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(self.config.scroll_timeout)
                
                # Check if we've reached the bottom
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    logger.info("Reached end of feed")
                    break
                last_height = new_height
            
            return posts_data
            
        except Exception as e:
            logger.error(f"Failed to scroll and collect posts: {str(e)}")
            raise DataCollectionError(f"Failed to collect posts: {str(e)}")
    
    async def _extract_post_data(self, post: Any) -> Optional[Dict]:
        """Extract data from a single post."""
        try:
            content = await post.query_selector(".update-components-text")
            content_text = await content.inner_text() if content else ""
            
            likes = await post.query_selector(".social-details-social-counts__reactions-count")
            comments = await post.query_selector(".social-details-social-counts__comments")
            
            likes_count = await likes.inner_text() if likes else "0"
            comments_count = await comments.inner_text() if comments else "0"
            
            return {
                "content": content_text,
                "likes": likes_count,
                "comments": comments_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting post data: {str(e)}")
            return None
    
    async def _analyze_engagement(self, page: Page) -> Dict:
        """Analyze engagement patterns of recent posts."""
        try:
            posts = await page.query_selector_all(".feed-shared-update-v2")
            engagement_data = []
            
            for post in posts[:5]:
                try:
                    post_data = await self._extract_post_data(post)
                    if post_data:
                        engagement_data.append(post_data)
                except Exception as e:
                    logger.error(f"Error analyzing post engagement: {str(e)}")
                    continue
                    
            return {"engagement_data": engagement_data}
            
        except Exception as e:
            logger.error(f"Failed to analyze engagement: {str(e)}")
            return {"error": str(e)}
    
    def _get_top_performing_posts(self, posts_data: List[Dict], num_top: int = 10) -> List[Dict]:
        """Get top performing posts based on total engagement."""
        try:
            for post in posts_data:
                try:
                    likes = int(post["likes"].replace(",", ""))
                except ValueError:
                    likes = 0
                    
                try:
                    comments = int(post["comments"].replace(",", "").replace(" comments", "").replace(" comment", ""))
                except ValueError:
                    comments = 0
                
                post["total_engagement"] = likes + comments
            
            sorted_posts = sorted(posts_data, key=lambda x: x["total_engagement"], reverse=True)
            return sorted_posts[:num_top]
            
        except Exception as e:
            logger.error(f"Failed to get top performers: {str(e)}")
            return []
    
    async def run(self, number_of_posts: int, number_of_top_performing_posts: int) -> List[Dict]:
        """Run the LinkedIn data gatherer with caching."""
        cache_key = f"linkedin_posts_{number_of_posts}_{number_of_top_performing_posts}"
        cached_data = await self._get_cached_data(cache_key)
        
        if cached_data:
            logger.info("Returning cached data")
            return cached_data
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    if await self._login(page):
                        posts_data = await self._scroll_and_collect_posts(page, num_posts=number_of_posts)
                        logger.info(f"Collected data for {len(posts_data)} posts")
                        
                        top_posts = self._get_top_performing_posts(posts_data, number_of_top_performing_posts)
                        await self._save_to_cache(cache_key, top_posts)
                        
                        return top_posts
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Error in run: {str(e)}")
            raise DataCollectionError(f"Failed to run data collection: {str(e)}")
        
        return []

async def gather_social_media_data(platform: str, number_of_posts: int, number_of_top_performing_posts: int) -> List[Dict]:
    """Gather social media data from a given platform."""
    try:
        if platform.lower() == "linkedin":
            gatherer = LinkedInDataGatherer()
            return await gatherer.run(number_of_posts, number_of_top_performing_posts)
        
        raise ValueError(f"Platform {platform} not supported")
        
    except Exception as e:
        logger.error(f"Error gathering social media data: {str(e)}")
        return []

root_agent = LlmAgent(
    name="trend_analyzer_agent",
    description="An expert agent that analyzes social media trends and engagement patterns to identify successful content strategies.",
    model="gemini-2.0-flash",
    instruction="""You are an expert social media trend analyzer with deep expertise in content performance analysis.
        When user consults about current social media trends, you will:
        1. Identify which platform you need to analyze
        2. Gather data from the platform using the gather_social_media_data tool
        3. Analyze the posts returned by the tool
        4. Provide data-driven recommendations for content creation

        Your goal is to help users understand what content performs best on social media and why, enabling them to create more engaging and effective content. 

        To collect data, use the gather_social_media_data tool with the following parameters:
        - platform: The social media platform to analyze (currently supports "linkedin")
        - number_of_posts: Number of posts to collect for analysis
        - number_of_top_performing_posts: Number of top posts to focus on

        When analyzing trends, focus on:
        - Content themes and topics that drive engagement
        - Content format effectiveness
        - Platform-specific best practices""",
    tools=[gather_social_media_data],
    output_key="trends"
)
