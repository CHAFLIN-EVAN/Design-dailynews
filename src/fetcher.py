"""
设计日报 - 新闻抓取模块
支持 RSS 订阅 + 网页爬取两种方式
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS, SCRAPE_TARGETS, MAX_ARTICLES_PER_SOURCE

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 15


class Article:
    """新闻文章数据结构"""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        category: str,
        summary: str = "",
        published: Optional[datetime] = None,
        image_url: str = "",
    ):
        self.title = title.strip()
        self.url = url.strip()
        self.source = source
        self.category = category
        self.summary = summary.strip()[:500]
        self.published = published
        self.image_url = image_url.strip()

    def __repr__(self):
        return f"<Article: {self.title[:30]}... from {self.source}>"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "summary": self.summary,
            "published": self.published.isoformat() if self.published else None,
            "image_url": self.image_url,
        }


# ============================================================
# RSS 抓取
# ============================================================

def _parse_feed_date(date_str: str) -> Optional[datetime]:
    """解析 RSS 日期字段为 datetime"""
    if not date_str:
        return None
    try:
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _extract_image_from_entry(entry) -> str:
    """从 RSS entry 中提取图片 URL"""
    # 1. media_content
    if hasattr(entry, "media_content"):
        for media in entry.media_content:
            url = media.get("url", "")
            if url and any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                return url
            if "image" in media.get("type", ""):
                return url

    # 2. media_thumbnail
    if hasattr(entry, "media_thumbnail"):
        for thumb in entry.media_thumbnail:
            url = thumb.get("url", "")
            if url:
                return url

    # 3. enclosures (common for podcasts but sometimes images)
    if hasattr(entry, "enclosures"):
        for enc in entry.enclosures:
            enc_type = enc.get("type", "")
            if enc_type.startswith("image"):
                return enc.get("href", "") or enc.get("url", "")

    # 4. Extract from summary/description HTML
    content = ""
    if hasattr(entry, "summary"):
        content = entry.summary
    elif hasattr(entry, "description"):
        content = entry.description

    if content:
        soup = BeautifulSoup(content, "lxml")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

    return ""


def fetch_rss_source(name: str, feed_url: str, category: str = "") -> list[Article]:
    """抓取单个 RSS 源"""
    articles = []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            summary = ""
            if hasattr(entry, "summary"):
                # 去除 HTML 标签
                summary = BeautifulSoup(entry.summary, "lxml").get_text()
            elif hasattr(entry, "description"):
                summary = BeautifulSoup(entry.description, "lxml").get_text()

            published = _parse_feed_date(
                entry.get("published", "") or entry.get("updated", "")
            )

            image_url = _extract_image_from_entry(entry)

            # 从 feed 分类或 URL 推断类别
            feed_category = category
            if not feed_category:
                feed_category = _infer_category(name)

            articles.append(Article(
                title=title,
                url=link,
                source=name,
                category=feed_category,
                summary=summary,
                published=published,
                image_url=image_url,
            ))

        logger.info(f"[RSS] {name}: 获取 {len(articles)} 篇文章")
    except Exception as e:
        logger.warning(f"[RSS] {name} 抓取失败: {e}")

    return articles


def _infer_category(source_name: str) -> str:
    """根据来源名称推断设计类别"""
    ux_sources = {"smashing_magazine", "ux_collective", "nngroup", "creative_bloc"}
    industrial_sources = {"yanko_design", "core77", "dezeen"}
    graphic_sources = {"design_week", "its_nice_that", "brand_identity"}

    if source_name in ux_sources:
        return "UI/UX"
    elif source_name in industrial_sources:
        return "工业/产品设计"
    elif source_name in graphic_sources:
        return "平面视觉"
    return "设计综合"


def fetch_all_rss() -> list[Article]:
    """抓取所有 RSS 源"""
    all_articles = []
    for name, url in RSS_FEEDS.items():
        articles = fetch_rss_source(name, url)
        all_articles.extend(articles)
    return all_articles


# ============================================================
# 网页爬取
# ============================================================

def _extract_image_from_page(url: str) -> str:
    """从文章页面提取主图（og:image）"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # 优先 og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        # 其次 twitter:image
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"]

        # 最后取文章内第一张图
        article = soup.find("article") or soup.find("main") or soup
        img = article.find("img")
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("/"):
                from urllib.parse import urljoin
                src = urljoin(url, src)
            return src

    except Exception:
        pass
    return ""


def scrape_source(target: dict) -> list[Article]:
    """爬取单个网站"""
    articles = []
    name = target["name"]
    url = target["url"]
    selector = target["selector"]
    encoding = target.get("encoding", "utf-8")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = encoding
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        elements = soup.select(selector)[:MAX_ARTICLES_PER_SOURCE]

        for el in elements:
            title = el.get_text(strip=True)
            link = el.get("href", "")

            if not title or not link:
                continue

            # 处理相对链接
            if link.startswith("/"):
                from urllib.parse import urljoin
                link = urljoin(url, link)

            if not link.startswith("http"):
                continue

            # 提取文章配图
            image_url = _extract_image_from_page(link)

            articles.append(Article(
                title=title,
                url=link,
                source=name,
                category="中文设计",
                summary="",
                image_url=image_url,
            ))

        logger.info(f"[爬取] {name}: 获取 {len(articles)} 篇文章")
    except Exception as e:
        logger.warning(f"[爬取] {name} 抓取失败: {e}")

    return articles


def scrape_all() -> list[Article]:
    """爬取所有目标网站"""
    all_articles = []
    for target in SCRAPE_TARGETS:
        articles = scrape_source(target)
        all_articles.extend(articles)
    return all_articles


# ============================================================
# 统一接口
# ============================================================

def fetch_all_news() -> list[Article]:
    """获取所有新闻（RSS + 爬取）"""
    logger.info("开始抓取新闻...")
    rss_articles = fetch_all_rss()
    scraped_articles = scrape_all()

    all_articles = rss_articles + scraped_articles
    logger.info(f"总计获取 {len(all_articles)} 篇文章")

    # 去重（基于 URL）
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)

    logger.info(f"去重后剩余 {len(unique_articles)} 篇")
    return unique_articles


def filter_recent(articles: list[Article], hours: int = 48) -> list[Article]:
    """过滤出最近 N 小时内的文章（有发布日期的才过滤）"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for a in articles:
        if a.published is None:
            recent.append(a)  # 没有日期的保留
        elif a.published >= cutoff:
            recent.append(a)
    return recent
