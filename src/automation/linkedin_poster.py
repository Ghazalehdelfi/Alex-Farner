import os
import logging
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from src.utils.utils import setup_logging
from typing import Optional

# --- SETUP ---
load_dotenv()
setup_logging("data/logs/linkedin_poster.log")

# --- CONFIG ---
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

async def post_to_linkedin(post_id: str, content_type: str) -> bool:
    """
    Post content to LinkedIn using Playwright automation.
    
    Args:
        post_id: The ID of the post to publish (e.g., "N_POST_001" or "TIP_abc123")
        content_type: Type of content ("News" or "Tip")
        
    Returns:
        bool: True if posting was successful, False otherwise
    """
    try:
        # Read post content
        if content_type == "News":
            file_path = Path("data/news_posts") / f"{post_id}.txt"
        else:  # Tips
            file_path = Path("data/tips_posts") / f"{post_id}.txt"
            
        if not file_path.exists():
            logging.error(f"Content file not found for {post_id}")
            return False
            
        content = file_path.read_text(encoding="utf-8")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)  # Show browser
            context = await browser.new_context()
            page = await context.new_page()
            
            # Login to LinkedIn
            await page.goto("https://www.linkedin.com/login")
            await page.fill("#username", LINKEDIN_EMAIL)
            await page.fill("#password", LINKEDIN_PASSWORD)
            await page.click("button[type='submit']")
            
            # Wait for login to complete
            await page.wait_for_selector(".feed-shared-update-v2", timeout=30000)
            
            # Click on "Start a post" button
            await page.click(".share-box-feed-entry__top-bar")
            
            # Wait for post dialog and enter content
            await page.wait_for_selector(".ql-editor")
            await page.fill(".ql-editor", content)
            
            # Click post button
            await page.click("button.artdeco-button--primary")
            
            # Wait for post to be published
            await page.wait_for_selector(".feed-shared-update-v2", timeout=30000)
            
            # Keep browser open for review
            logging.info(f"Successfully posted {post_id} to LinkedIn")
            return True
            
    except Exception as e:
        logging.error(f"Error posting to LinkedIn: {str(e)}")
        return False

async def main():
    """Main function to test LinkedIn posting."""
    post_id = "N_POST_1"  # Example post ID
    success = await post_to_linkedin(post_id, "News")
    if success:
        print("Post published successfully!")
    else:
        print("Failed to publish post.")

if __name__ == "__main__":
    asyncio.run(main()) 