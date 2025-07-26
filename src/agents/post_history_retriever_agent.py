from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator, Dict, Optional, List
from google.adk.events import Event, EventActions
import json
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostHistoryRetrieverAgent(BaseAgent):
    """A custom agent that retrieves and returns user's previous posts."""
    
    def __init__(self, name: str = "PostHistoryRetriever", posts_dir: Optional[str] = None):
        """Initialize the post history retriever agent.
        
        Args:
            name: The name of the agent
            posts_dir: Directory containing saved posts. Defaults to 'data/posts'
        """
        super().__init__(name=name)
        self.posts_dir = Path(posts_dir or "data/posts")
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Implementation of the agent's main logic.
        
        Args:
            ctx: The invocation context containing session state and other information
            
        Yields:
            Events containing the retrieved posts or error information
        """
        try:
            # Get parameters from context state
            platform = ctx.session.state.get("platform")
            time_range = ctx.session.state.get("time_range", "30d")  # Default to last 30 days
            max_posts = ctx.session.state.get("max_posts", 10)  # Default to 10 posts
            
            if not platform:
                yield Event(
                    author=self.name,
                    content="No platform specified in context state",
                    actions=EventActions(escalate=True)
                )
                return
                
            # Calculate date range
            end_date = datetime.now()
            if time_range.endswith('d'):
                days = int(time_range[:-1])
                start_date = end_date - timedelta(days=days)
            elif time_range.endswith('w'):
                weeks = int(time_range[:-1])
                start_date = end_date - timedelta(weeks=weeks)
            elif time_range.endswith('m'):
                months = int(time_range[:-1])
                start_date = end_date - timedelta(days=months * 30)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
                
            # Get posts
            posts = self._get_posts(platform, start_date, end_date, max_posts)
            
            if not posts:
                yield Event(
                    author=self.name,
                    content=f"No posts found for platform {platform} in the specified time range",
                    actions=EventActions(escalate=True)
                )
                return
                
            # Store posts in session state
            ctx.session.state["retrieved_posts"] = posts
            
            yield Event(
                author=self.name,
                content=f"Successfully retrieved {len(posts)} posts from {platform}",
                actions=EventActions(escalate=False)
            )
            
        except Exception as e:
            logger.error(f"Error retrieving posts: {str(e)}")
            yield Event(
                author=self.name,
                content=f"Error retrieving posts: {str(e)}",
                actions=EventActions(escalate=True)
            )
            
    def _get_posts(self, platform: str, start_date: datetime, end_date: datetime, max_posts: int) -> List[Dict]:
        """Get posts for a specific platform within a date range.
        
        Args:
            platform: The social media platform
            start_date: Start date for post retrieval
            end_date: End date for post retrieval
            max_posts: Maximum number of posts to retrieve
            
        Returns:
            List of post dictionaries
        """
        try:
            platform_dir = self.posts_dir / platform
            if not platform_dir.exists():
                return []
                
            posts = []
            for post_file in platform_dir.glob("*.json"):
                try:
                    with open(post_file, 'r') as f:
                        post = json.load(f)
                        post_date = datetime.fromisoformat(post.get("timestamp", ""))
                        if start_date <= post_date <= end_date:
                            posts.append(post)
                except Exception as e:
                    logger.warning(f"Error reading post file {post_file}: {str(e)}")
                    continue
                    
            # Sort by date and limit to max_posts
            posts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return posts[:max_posts]
            
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []
            
    def save_post(self, platform: str, post_data: Dict) -> bool:
        """Save a post to file.
        
        Args:
            platform: The social media platform
            post_data: The post data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure platform directory exists
            platform_dir = self.posts_dir / platform
            platform_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from timestamp
            timestamp = post_data.get("timestamp", datetime.now().isoformat())
            post_id = post_data.get("id", timestamp.replace(":", "-"))
            post_file = platform_dir / f"{post_id}.json"
            
            # Save post
            with open(post_file, 'w') as f:
                json.dump(post_data, f, indent=2)
            return True
            
        except Exception as e:
            logger.error(f"Error saving post: {str(e)}")
            return False
            
    def get_available_platforms(self) -> List[str]:
        """Get a list of platforms with saved posts.
        
        Returns:
            List of platform names
        """
        try:
            return [
                d.name for d in self.posts_dir.iterdir()
                if d.is_dir()
            ]
        except Exception as e:
            logger.error(f"Error getting available platforms: {str(e)}")
            return [] 