import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

import logging
import asyncio
from typing import List, Dict, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv
import openai
from src.utils.utils import setup_logging
import pandas as pd

# --- SETUP ---
load_dotenv()
setup_logging("data/logs/linkedin_agents.log")
openai.api_key = os.getenv("OPENAI_API_KEY")

class LinkedInAgent:
    """Base class for LinkedIn automation agents."""
    
    def __init__(self):
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        
    async def login(self, page: Page) -> bool:
        """Login to LinkedIn."""
        try:
            print("Attempting to login to LinkedIn...")
            await page.goto("https://www.linkedin.com/login")
            print("Filling login credentials...")
            await page.fill("#username", self.email)
            await page.fill("#password", self.password)
            await page.click("button[type='submit']")
            print("Waiting for feed to load...")
            await page.wait_for_selector(".feed-shared-update-v2", timeout=30000)
            print("Successfully logged in!")
            return True
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            print(f"Login failed: {str(e)}")
            return False

class ContentStrategyAgent(LinkedInAgent):
    """Agent responsible for content strategy and tone."""
    
    async def scroll_and_collect_posts(self, page: Page, num_posts: int = 100) -> List[Dict]:
        """Scroll through feed and collect post data."""
        try:
            posts_data = []
            last_height = await page.evaluate('document.body.scrollHeight')
            scroll_count = 0
            
            print("Starting to scroll and collect posts...")
            while len(posts_data) < num_posts:
                scroll_count += 1
                print(f"\nScroll attempt {scroll_count}")
                
                # Get all visible posts
                posts = await page.query_selector_all(".feed-shared-update-v2")
                print(f"Found {len(posts)} posts on current scroll")
                
                for post in posts:
                    if len(posts_data) >= num_posts:
                        break
                        
                    try:
                        # Get post content directly from .update-components-text
                        content = await post.query_selector(".update-components-text")
                        content_text = await content.inner_text() if content else ""
                        
                        # Get engagement metrics
                        likes = await post.query_selector(".social-details-social-counts__reactions-count")
                        comments = await post.query_selector(".social-details-social-counts__comments")
                        
                        likes_count = await likes.inner_text() if likes else "0"
                        comments_count = await comments.inner_text() if comments else "0"
                        
                        post_data = {
                            "content": content_text,
                            "likes": likes_count,
                            "comments": comments_count,
                        }
                        
                        # Only add if we haven't seen this post before
                        if not any(p["content"] == content_text for p in posts_data):
                            posts_data.append(post_data)
                            print(f"Collected post {len(posts_data)}/{num_posts}")
                            
                    except Exception as e:
                        logging.error(f"Error processing post: {str(e)}")
                        print(f"Error processing post: {str(e)}")
                        continue
                
                # Scroll down
                print("Scrolling down...")
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(3000)  # Increased wait time
                
                # Check if we've reached the bottom
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    print("Reached end of feed")
                    break
                last_height = new_height
            
            return posts_data
            
        except Exception as e:
            logging.error(f"Failed to scroll and collect posts: {str(e)}")
            print(f"Failed to scroll and collect posts: {str(e)}")
            return []

    async def analyze_engagement(self, page: Page) -> Dict:
        """Analyze engagement patterns of recent posts."""
        try:
            # Get recent posts and their engagement
            posts = await page.query_selector_all(".feed-shared-update-v2")
            engagement_data = []
            
            for post in posts[:5]:  # Analyze last 5 posts
                likes = await post.query_selector(".social-details-social-counts__reactions-count")
                comments = await post.query_selector(".social-details-social-counts__comments")
                
                likes_count = await likes.inner_text() if likes else "0"
                comments_count = await comments.inner_text() if comments else "0"
                
                content = await post.query_selector(".feed-shared-update-v2__description")
                content_text = await content.inner_text() if content else ""
                
                engagement_data.append({
                    "content": content_text,
                    "likes": likes_count,
                    "comments": comments_count
                })
            print(engagement_data)
            return engagement_data
        except Exception as e:
            logging.error(f"Failed to analyze engagement: {str(e)}")
            return []

    def optimize_prompt(self, engagement_data: List[Dict], content_type: str) -> str:
        """Optimize the content generation prompt based on engagement data."""
        try:
            # Analyze what works best - handle comma-separated numbers
            successful_posts = []
            for post in engagement_data:
                likes = post["likes"].replace(",", "")  # Remove commas
                if likes.isdigit() and int(likes) > 10:
                    successful_posts.append(post)
            
            # Create a prompt to analyze the successful posts
            analysis_prompt = f"""
            Analyze these successful LinkedIn posts and identify patterns:
            {successful_posts}
            
            Based on this analysis, suggest improvements to our content strategy for {content_type} posts.
            Focus on:
            1. Tone and style
            2. Content structure
            3. Engagement triggers
            4. Hashtag usage
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a social media strategy expert."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Failed to optimize prompt: {str(e)}")
            return ""

    def get_top_performers(self, posts_data: List[Dict], num_top: int = 10) -> List[Dict]:
        """Get top performing posts based on total engagement (likes + comments)."""
        try:
            # Convert engagement numbers to integers, handling comma-separated values and text
            for post in posts_data:
                # Handle likes (remove commas)
                likes = post["likes"].replace(",", "")
                
                # Handle comments (remove 'comments' text and commas)
                comments = post["comments"].replace(",", "").replace(" comments", "").replace(" comment", "")
                
                # Convert to integers, defaulting to 0 if conversion fails
                try:
                    likes_int = int(likes)
                except ValueError:
                    likes_int = 0
                    
                try:
                    comments_int = int(comments)
                except ValueError:
                    comments_int = 0
                
                post["total_engagement"] = likes_int + comments_int
            
            # Sort by total engagement in descending order
            sorted_posts = sorted(posts_data, key=lambda x: x["total_engagement"], reverse=True)
            
            # Get top performers
            top_posts = sorted_posts[:num_top]
            
            # Print summary
            print("\nTop 10 Performing Posts:")
            for i, post in enumerate(top_posts, 1):
                print(f"\n{i}. Engagement: {post['total_engagement']} (Likes: {post['likes']}, Comments: {post['comments']})")
                print(f"Content: {post['content'][:200]}...")
            
            return top_posts
            
        except Exception as e:
            logging.error(f"Failed to get top performers: {str(e)}")
            print(f"Error in get_top_performers: {str(e)}")
            return []

class EngagementAgent(LinkedInAgent):
    """Agent responsible for engaging with other posts."""
    
    async def find_relevant_posts(self, page: Page, keywords: List[str]) -> List[Dict]:
        """Find relevant posts to engage with."""
        try:
            # Search for posts with keywords
            for keyword in keywords:
                await page.goto(f"https://www.linkedin.com/search/results/content/?keywords={keyword}")
                await page.wait_for_selector(".search-results__content")
                
                # Get posts
                posts = await page.query_selector_all(".search-results__content-item")
                relevant_posts = []
                
                for post in posts[:5]:  # Get top 5 posts
                    content = await post.query_selector(".feed-shared-update-v2__description")
                    if content:
                        content_text = await content.inner_text()
                        relevant_posts.append({
                            "content": content_text,
                            "url": await post.get_attribute("href")
                        })
                
                return relevant_posts
        except Exception as e:
            logging.error(f"Failed to find relevant posts: {str(e)}")
            return []

    async def generate_comment(self, post_content: str) -> str:
        """Generate a thoughtful comment for a post."""
        try:
            prompt = f"""
            Generate a thoughtful, professional comment for this LinkedIn post:
            {post_content}
            
            The comment should:
            1. Add value to the discussion
            2. Be specific and relevant
            3. Show expertise without being condescending
            4. Be concise (max 2-3 sentences)
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional ML engineer engaging in thoughtful discussion."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Failed to generate comment: {str(e)}")
            return ""

    async def post_comment(self, page: Page, post_url: str, comment: str) -> bool:
        """Post a comment on a specific post."""
        try:
            await page.goto(post_url)
            await page.wait_for_selector(".comments-comment-box")
            
            # Click comment box
            await page.click(".comments-comment-box")
            await page.wait_for_selector(".ql-editor")
            
            # Enter comment
            await page.fill(".ql-editor", comment)
            
            # Post comment
            await page.click("button.comments-comment-box__submit-button")
            await page.wait_for_selector(".comments-comment-item")
            
            return True
        except Exception as e:
            logging.error(f"Failed to post comment: {str(e)}")
            return False

async def main():
    """Main function to test the LinkedIn agents."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Test content strategy
        strategy_agent = ContentStrategyAgent()
        if await strategy_agent.login(page):
            # Scroll and collect posts
            posts_data = await strategy_agent.scroll_and_collect_posts(page, num_posts=100)
            print(f"\nCollected data for {len(posts_data)} posts")
            
            # Get top performing posts
            top_posts = strategy_agent.get_top_performers(posts_data)
            
            # Save only top performers to CSV
            df_top = pd.DataFrame(top_posts)
            df_top.to_csv("data/top_performing_posts.csv", index=False)
            print("\nSaved top 10 performing posts to data/top_performing_posts.csv")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())