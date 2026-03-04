import requests
import feedparser
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import BLOG_ID, BLOG_RSS, BLOG_URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://m.blog.naver.com/"
}

def fetch_posts(days_back: int = 1) -> list[dict]:
    """
    Fetch blog posts from the past N days.
    Uses RSS as primary method (most reliable for Naver).
    Returns list of {title, url, date, category, content}
    """
    since = datetime.now() - timedelta(days=days_back)
    posts = _fetch_via_rss(since)

    if not posts:
        print("[WARN] RSS empty, trying direct scrape...")
        posts = _fetch_via_direct(since)

    print(f"[SCRAPER] Found {len(posts)} posts since {since.strftime('%Y-%m-%d')}")
    return posts


def _fetch_via_rss(since: datetime) -> list[dict]:
    try:
        feed = feedparser.parse(BLOG_RSS)
        posts = []
        for entry in feed.entries:
            dp = entry.get("published_parsed")
            if not dp:
                continue
            post_date = datetime(*dp[:6])
            if post_date < since:
                continue
            url = entry.get("link", "")
            content = _fetch_content(url)
            posts.append({
                "title":    entry.get("title", ""),
                "url":      url,
                "date":     post_date.strftime("%Y-%m-%d"),
                "category": entry.get("tags", [{"term": "Unknown"}])[0]["term"] if entry.get("tags") else "Unknown",
                "content":  content
            })
            time.sleep(0.8)
        return posts
    except Exception as e:
        print(f"[RSS ERROR] {e}")
        return []


def _fetch_via_direct(since: datetime) -> list[dict]:
    posts = []
    try:
        for page in range(1, 6):
            url = f"https://m.blog.naver.com/PostList.naver?blogId={BLOG_ID}&currentPage={page}&postListSize=20"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("li[data-log-no]") or soup.select(".post_item")
            if not items:
                break
            for item in items:
                log_no = item.get("data-log-no", "")
                title_el = item.select_one(".title, .tit_post, strong")
                date_el  = item.select_one(".date, .se_publishDate")
                title    = title_el.get_text(strip=True) if title_el else ""
                date_str = date_el.get_text(strip=True) if date_el else ""
                post_date = _parse_date(date_str)
                if post_date and post_date < since:
                    return posts
                post_url = f"https://m.blog.naver.com/{BLOG_ID}/{log_no}"
                content  = _fetch_content(post_url)
                posts.append({
                    "title":    title,
                    "url":      post_url,
                    "date":     post_date.strftime("%Y-%m-%d") if post_date else date_str,
                    "category": "Unknown",
                    "content":  content
                })
                time.sleep(0.8)
    except Exception as e:
        print(f"[DIRECT ERROR] {e}")
    return posts


def _fetch_content(url: str) -> str:
    if not url:
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Strategy 1: Smart Editor
        el = soup.select_one(".se-main-container, .post_ct, #postViewArea")
        if el:
            return _clean(el.get_text("\n", strip=True))

        # Strategy 2: iframe
        iframe = soup.select_one("iframe#mainFrame")
        if iframe and iframe.get("src"):
            r2 = requests.get("https://blog.naver.com" + iframe["src"], headers=HEADERS, timeout=20)
            r2.encoding = "utf-8"
            s2 = BeautifulSoup(r2.text, "lxml")
            el2 = s2.select_one(".se-main-container, .post_ct, #postViewArea")
            if el2:
                return _clean(el2.get_text("\n", strip=True))

        # Strategy 3: all paragraphs
        paras = soup.select("p, .se-text-paragraph")
        if paras:
            return _clean("\n".join(p.get_text(strip=True) for p in paras))

        # Strategy 4: body fallback
        body = soup.find("body")
        return _clean(body.get_text("\n", strip=True)) if body else ""

    except Exception as e:
        print(f"[CONTENT ERROR] {url}: {e}")
        return ""


def _clean(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def _parse_date(s: str) -> datetime | None:
    s = s.strip()
    for fmt in ["%Y. %m. %d.", "%Y.%m.%d", "%Y-%m-%d", "%Y. %m. %d"]:
        try:
            return datetime.strptime(s, fmt)
        except:
            continue
    if "일 전" in s:
        try:
            return datetime.now() - timedelta(days=int(re.search(r'\d+', s).group()))
        except:
            pass
    return None
