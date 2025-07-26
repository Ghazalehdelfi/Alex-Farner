import os
import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from newspaper import Article
from dotenv import load_dotenv
import openai
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import uuid
import time

from src.utils.utils import (
    setup_logging,
    setup_environment,
    ensure_directory,
    load_or_create_dataframe,
    save_dataframe,
    validate_config,
    with_retry,
    with_cache,
    truncate_text,
    handle_api_error
)

# --- CONFIG ---
RSS_FEEDS = [
    "https://www.deepmind.com/blog/rss.xml",
    "https://www.infoq.com/mlops/rss/",
    "https://towardsdatascience.com/feed",
    "https://netflixtechblog.com/feed",
    "https://engineering.atspotify.com/feed/",
    "https://eng.uber.com/feed/",
    "https://stackoverflow.blog/feed/",
    "https://www.ben-evans.com/benedictevans?format=rss",
    "https://huggingface.co/blog/rss.xml",
    "https://engineering.fb.com/feed/",
    "https://research.facebook.com/blog/rss/",
    "https://aws.amazon.com/blogs/architecture/feed/",
    "https://www.amazon.science/rss.xml",
    "https://research.google/blog/rss/",
    "https://engineering.quora.com/rss",
    "https://databricks.com/feed",
    "https://medium.com/feed/@Pinterest_Engineering",
    "https://engineering.blackrock.com/feed/",
    "https://eng.lyft.com/feed",
    "https://engineering.salesforce.com/feed/",
]

GITHUB_TRENDING_URL = "https://github.com/trending/python?since=daily"
OUTPUT_SOURCES = "data/articles.csv"
FINAL_OUTPUT = "data/posts.csv"
MAX_WORKERS = 5
MAX_RETRIES = 3
CACHE_SIZE = 1000

# Initialize environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize environment and logging
setup_logging("data/logs/tech_news.log")
setup_environment()
ensure_directory("data/news_posts")

@dataclass
class Config:
    """Configuration settings for the tech news generator."""
    output_file: str = "data/articles.csv"
    posts_dir: str = "data/news_posts"
    model: str = "gpt-4"
    temperature: float = 0.8
    max_retries: int = 3
    batch_size: int = 5


@with_retry(max_tries=MAX_RETRIES)
@handle_api_error
def fetch_article_content(url: str, title: str = None) -> Dict:
    """Fetch and parse article content with retry logic."""
    article = Article(url)
    article.download()
    article.parse()
    return {
        "title": title or article.title,
        "link": url,
        "content": truncate_text(article.text)
    }

@with_cache(maxsize=CACHE_SIZE)
def fetch_rss_feed(url: str) -> List[Dict]:
    """Fetch and parse RSS feed with caching."""
    feed = feedparser.parse(url)
    return [
        {
            "title": entry.title,
            "link": entry.link,
            "source": url,
        }
        for entry in feed.entries[:5]
    ]

def fetch_rss_articles() -> List[Dict]:
    """Fetch articles from all RSS feeds in parallel."""
    logging.info("Fetching RSS articles...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(fetch_rss_feed, url): url 
            for url in RSS_FEEDS
        }
        
        articles = []
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                feed_articles = future.result()
                for article in feed_articles:
                    try:
                        content = fetch_article_content(article["link"], article["title"])
                        articles.append({
                            **article,
                            "content": content["content"]
                        })
                    except Exception as e:
                        logging.error(f"Failed to process article from {url}: {str(e)}")
            except Exception as e:
                logging.error(f"Failed to process feed {url}: {str(e)}")
    
    logging.info(f"Fetched {len(articles)} articles from RSS feeds.")
    return articles

@with_retry(max_tries=MAX_RETRIES)
@handle_api_error
def scrape_github_trending() -> List[Dict]:
    """Scrape GitHub trending repositories with retry logic."""
    logging.info("Scraping GitHub Trending...")
    
    res = requests.get(GITHUB_TRENDING_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    repos = soup.find_all("h2", class_="h3 lh-condensed")
    
    articles = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_repo = {
            executor.submit(
                fetch_article_content,
                "https://github.com" + repo.find("a")["href"],
                repo.text.strip().replace("\n", " ").strip()
            ): repo
            for repo in repos[:5]
        }
        
        for future in as_completed(future_to_repo):
            try:
                content = future.result()
                articles.append({
                    **content,
                    "source": "GitHub Trending"
                })
            except Exception as e:
                logging.error(f"Failed to process GitHub repo: {str(e)}")
    
    logging.info(f"Scraped {len(articles)} repositories from GitHub Trending.")
    return articles

@with_retry(max_tries=MAX_RETRIES)
@handle_api_error
def gpt_score_article(article: Dict) -> Tuple[int, int, int]:
    """Score article using GPT with retry logic."""
    logging.info(f"Scoring article: {article['title']}")
    
    prompt = f"""
    Given the following article title and content, rate the article on three criteria from 1 to 10:

    1. Interest: How novel, exciting, or valuable is it to ML or software engineering professionals?
    2. Accessibility: How approachable and easy to understand is it for a general tech-savvy audience?
    3. Relevance: How aligned is this article with ML engineering concepts or MLOps?

    Respond in the format:
    Interest: <score>
    Accessibility: <score>
    Relevance: <score>

    Title: {article['title']}
    Content: {article['content']}
    url: {article['link']}
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You evaluate and score tech articles for an editorial team.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    
    content = response.choices[0].message.content.strip()
    lines = content.split("\n")
    return (
        int(lines[0].split(":")[-1].strip()),
        int(lines[1].split(":")[-1].strip()),
        int(lines[2].split(":")[-1].strip())
    )

@with_retry(max_tries=MAX_RETRIES)
@handle_api_error
def gpt_generate_post(article: Dict) -> str:
    """Generate LinkedIn post using GPT with retry logic."""
    logging.info(f"Generating LinkedIn post for: {article['title']}")
    
    prompt = f"""
    Based on the title and content below, write a thoughtful LinkedIn post that feels human and conversational.

    - Use 3 relevant emoji for tone.
    - Add 5 relevant hashtags.
    - Sound like a real person sharing something genuinely useful but not too preachy.
    - Do not use phrases like "in my latest article" or "I wrote" - you are sharing someone else's work

    Title: {article['title']}
    content: {article['content']}
    Link: {article['link']}
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are Alex Farner, an experienced machine learning engineer and software architect who shares interesting ideas and takeaways on LinkedIn. You're curious, approachable, and write for both fellow engineers and tech-savvy newcomers.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_tech_news_content():
    """Main function to generate tech news content."""
    logging.info("Starting content generation pipeline...")

    # Load existing data
    articles = load_or_create_dataframe(
        OUTPUT_SOURCES,
        ["title", "postCreated", "link", "source", "interest", "accessibility", "relevance"]
    )
    posts = load_or_create_dataframe(
        FINAL_OUTPUT,
        ["ID", "Posted", "Title", "Link", "Source", "Interest", "Accessibility", "Relevance"]
    )

    # Fetch new articles
    all_articles = fetch_rss_articles() + scrape_github_trending()
    # all_articles = scrape_github_trending()
    fresh_articles = [a for a in all_articles if a["link"] not in articles["link"].values]

    if not fresh_articles:
        logging.info("No new articles to process.")
        return
    fresh_articles_data = []
    for article in fresh_articles:
        try:
            interest, accessibility, relevance = gpt_score_article(article)
            fresh_articles_data.append({
                "title": article["title"],
                "postCreated": False,
                "link": article["link"],
                "source": article["source"],
                "interest": interest,
                "accessibility": accessibility,
                "relevance": relevance
            })
            time.sleep(10)
        except Exception as e:
            logging.error(f"Failed to score article {article['title']}: {str(e)}")

    # Update articles DataFrame
    fresh_articles_df = pd.DataFrame(fresh_articles_data)
    articles = pd.concat([articles, fresh_articles_df])
    
    # Sort and select top articles
    articles["total_score"] = (articles["interest"] + articles["accessibility"] + articles["relevance"]) / 3
    top_articles = articles.nlargest(5, "total_score")

    # Generate posts for top articles
    new_posts = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_article = {
            executor.submit(gpt_generate_post, article): article 
            for _, article in top_articles.iterrows()
        }
        
        for idx, future in enumerate(as_completed(future_to_article)):
            article = future_to_article[future]
            try:
                post = future.result()
                post_id = f"N_POST_{idx + len(posts)}"
                
                # Save post draft
                draft_path = Path("data/news_posts") / f"{post_id}.txt"
                draft_path.write_text(post, encoding="utf-8")
                
                new_posts.append({
                    "ID": post_id,
                    "Posted": False,
                    "Title": article["title"],
                    "Link": article["link"],
                    "Source": article["source"],
                    "Interest": article["interest"],
                    "Accessibility": article["accessibility"],
                    "Relevance": article["relevance"],
                })
                
                articles.loc[articles["link"] == article["link"], "postCreated"] = True
            except Exception as e:
                logging.error(f"Failed to generate post for {article['title']}: {str(e)}")

    # Save results
    posts = pd.concat([posts, pd.DataFrame(new_posts)])
    save_dataframe(posts, FINAL_OUTPUT)
    save_dataframe(articles, OUTPUT_SOURCES)
    
    logging.info("Content generation completed successfully.")

if __name__ == "__main__":
    generate_tech_news_content()
