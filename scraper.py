"""
🔱 titan_K v2 — ranto28 Naver Blog Scraper
Fetches posts from ranto28's Naver blog via RSS + direct scraping.
"""
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
import feedparser
from bs4 import BeautifulSoup

from config import NAVER_BLOG_ID, NAVER_RSS_URL

logger = logging.getLogger("titan_k.scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_posts(days_back: int = 1, max_posts: int = 10) -> List[Dict]:
    """
    Fetch recent blog posts from ranto28.
    Strategy: Try RSS first (fast, structured), then fall back to direct scraping.
    """
    posts = []
    cutoff = datetime.now() - timedelta(days=days_back)
    
    # Strategy 1: RSS Feed
    try:
        posts = _fetch_via_rss(cutoff, max_posts)
        if posts:
            logger.info(f"RSS: Found {len(posts)} posts")
    except Exception as e:
        logger.warning(f"RSS failed: {e}")
    
    # Strategy 2: Direct blog page scraping (fallback)
    if not posts:
        try:
            posts = _fetch_via_scrape(cutoff, max_posts)
            logger.info(f"Scrape: Found {len(posts)} posts")
        except Exception as e:
            logger.error(f"Scrape also failed: {e}")
    
    # Fetch full content for each post
    for post in posts:
        if post.get("url") and not post.get("content"):
            try:
                post["content"] = _fetch_post_content(post["url"])
            except Exception as e:
                logger.warning(f"Failed to fetch content for {post.get('title', '?')}: {e}")
                post["content"] = post.get("summary", "")
    
    return posts


def _fetch_via_rss(cutoff: datetime, max_posts: int) -> List[Dict]:
    """Parse RSS feed for recent posts."""
    feed = feedparser.parse(NAVER_RSS_URL)
    posts = []
    
    for entry in feed.entries[:max_posts * 2]:  # fetch extra, filter by date
        # Parse date
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])
        
        if pub_date and pub_date < cutoff:
            continue
        
        # Extract clean URL
        url = entry.get("link", "")
        # Naver RSS sometimes wraps URLs
        if "redirect" in url:
            url = re.sub(r".*redirect.*url=", "", url)
        
        posts.append({
            "title": entry.get("title", "Untitled"),
            "url": url,
            "date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
            "summary": _clean_html(entry.get("summary", "")),
            "content": "",  # will be fetched separately
        })
        
        if len(posts) >= max_posts:
            break
    
    return posts


def _fetch_via_scrape(cutoff: datetime, max_posts: int) -> List[Dict]:
    """Scrape blog page directly for post links."""
    posts = []
    
    # Try the blog's post list page
    list_url = f"https://blog.naver.com/PostList.naver?blogId={NAVER_BLOG_ID}&from=postList&categoryNo=0"
    resp = requests.get(list_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find post links — Naver uses iframes, so try multiple selectors
    links = soup.select("a.pcol2, a[class*='title'], a[href*='logNo']")
    
    if not links:
        # Try mobile version which is simpler
        mobile_url = f"https://m.blog.naver.com/{NAVER_BLOG_ID}"
        resp = requests.get(mobile_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("a[href*='logNo'], a.title_link, a.link__iGhSW")
    
    for link in links[:max_posts]:
        href = link.get("href", "")
        title = link.get_text(strip=True)
        
        if not href:
            continue
        
        # Normalize URL
        if href.startswith("/"):
            href = f"https://blog.naver.com{href}"
        elif not href.startswith("http"):
            href = f"https://blog.naver.com/{NAVER_BLOG_ID}/{href}"
        
        if title and len(title) > 3:
            posts.append({
                "title": title,
                "url": href,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": "",
                "content": "",
            })
    
    return posts


def _fetch_post_content(url: str) -> str:
    """Fetch and extract the text content of a single blog post."""
    # Convert to mobile URL for easier parsing
    mobile_url = url.replace("blog.naver.com", "m.blog.naver.com")
    
    resp = requests.get(mobile_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Try multiple content selectors (Naver changes these periodically)
    content_selectors = [
        "div.se-main-container",       # Smart Editor 3
        "div.__se_component_area",     # Smart Editor 2
        "div.post-view",               # Mobile view
        "div#post-area",               # Legacy
        "div.sect_dsc",                # Another variant
        "div[class*='post_ct']",       # Generic
    ]
    
    content = ""
    for selector in content_selectors:
        el = soup.select_one(selector)
        if el:
            content = el.get_text(separator="\n", strip=True)
            break
    
    if not content:
        # Last resort: grab all paragraph text
        paragraphs = soup.select("p, span.se-text-paragraph")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 10)
    
    # Truncate to reasonable length for GPT analysis (avoid token waste)
    if len(content) > 8000:
        content = content[:8000] + "\n[... truncated for analysis]"
    
    return content


def _clean_html(html_text: str) -> str:
    """Strip HTML tags and clean up whitespace."""
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
