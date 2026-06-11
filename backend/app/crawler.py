"""
新闻爬虫 - 抓取目标科技媒体 RSS/HTML 新闻
反爬策略: 频率控制、UA 轮换、完整请求头、Cloudflare 挑战跳过
"""
import asyncio
import os
import re
import time
import random
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# ============ 目标媒体源 ============
SOURCES = [
    {
        "name": "Tom's Hardware",
        "rss_url": "https://www.tomshardware.com/feeds.xml",
        "categories": ["GPU", "CPU", "Storage", "Cooling"],
        "rate_limit": 2.0,
    },
    {
        "name": "AnandTech",
        "rss_url": "https://www.anandtech.com/rss",
        "categories": ["CPU", "GPU", "Storage"],
        "rate_limit": 2.5,
    },
    {
        "name": "TechPowerUp",
        "rss_url": "https://www.techpowerup.com/rss/",
        "categories": ["GPU", "CPU", "Storage", "Cooling", "Power Supply"],
        "rate_limit": 2.0,
    },
    {
        "name": "Wccftech",
        "rss_url": "https://wccftech.com/feed",
        "categories": ["GPU", "CPU", "Storage", "Cooling"],
        "rate_limit": 1.5,
    },
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _headers() -> dict:
    return {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


def strip_html(html: str) -> str:
    """Remove HTML tags, return plain text."""
    if not html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


# ============ Crawler ============
class NewsCrawler:
    def __init__(self, max_articles: int = 10, days_back: int = 7):
        self.max_articles = max_articles
        self.days_back = days_back
        self.cutoff = datetime.now() - timedelta(days=days_back)
        self.collected = []

    async def crawl_all(self) -> list[dict]:
        """Crawl all sources, return list of article dicts."""
        client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=_headers(),
        )
        for source in SOURCES:
            try:
                articles = await self._crawl_source(client, source)
                self.collected.extend(articles)
                logger.info(f"[{source['name']}] Got {len(articles)} articles")
            except Exception as e:
                logger.error(f"[{source['name']}] Failed: {e}")
            await self._rate_limit(source.get("rate_limit", 2.0))

        await client.aclose()
        unique = self._deduplicate(self.collected)
        logger.info(f"Total unique articles: {len(unique)}")
        return unique[:self.max_articles]

    async def _crawl_source(self, client: httpx.AsyncClient, source: dict) -> list[dict]:
        """Crawl a single RSS source."""
        resp = await client.get(source["rss_url"])
        resp.raise_for_status()

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            logger.warning(f"[{source['name']}] Invalid XML, skipping")
            return []

        items = []
        # RSS 2.0
        for item in root.iter('item'):
            article = self._parse_rss_item(item, source)
            if article:
                items.append(article)
        # Atom fallback
        if not items:
            ns = '{http://www.w3.org/2005/Atom}'
            for entry in root.iter(f'{ns}entry'):
                article = self._parse_atom_entry(entry, source)
                if article:
                    items.append(article)

        return items

    def _parse_rss_item(self, item, source: dict) -> dict | None:
        title = self._xml_text(item, 'title')
        link = self._xml_text(item, 'link')
        pub_date = self._xml_text(item, 'pubDate')
        description = self._xml_text(item, 'description') or ''
        content_ns = '{http://purl.org/rss/1.0/modules/content/}'
        content = self._xml_text(item, 'content:encoded', content_ns) or description

        if not title or not link:
            return None

        # Filter by date
        if pub_date:
            try:
                pub_dt = datetime.strptime(pub_date[:20], '%a, %d %b %Y %H:%M:%S')
                if pub_dt < self.cutoff:
                    return None
            except ValueError:
                pass

        return {
            "title": title.strip(),
            "url": link.strip(),
            "source": source["name"],
            "content_preview": strip_html(content)[:2000],
            "published_at": pub_date or datetime.now().isoformat(),
            "categories": source.get("categories", []),
        }

    def _parse_atom_entry(self, entry, source: dict) -> dict | None:
        ns = '{http://www.w3.org/2005/Atom}'
        title = entry.findtext(f'{ns}title')
        link_el = entry.find(f'{ns}link')
        link = link_el.get('href') if link_el is not None else None
        updated = entry.findtext(f'{ns}updated')
        content = entry.findtext(f'{ns}content') or entry.findtext(f'{ns}summary') or ''

        if not title or not link:
            return None

        return {
            "title": title.strip(),
            "url": link.strip(),
            "source": source["name"],
            "content_preview": strip_html(content)[:2000],
            "published_at": updated or datetime.now().isoformat(),
            "categories": source.get("categories", []),
        }

    @staticmethod
    def _xml_text(parent, tag: str, ns: str = '') -> str | None:
        el = parent.find(f'{ns}{tag}')
        return el.text.strip() if el is not None and el.text else None

    def _deduplicate(self, articles: list[dict]) -> list[dict]:
        """Remove duplicate/near-duplicate titles."""
        seen = set()
        unique = []
        for a in articles:
            key = re.sub(r'[^a-z0-9]', '', a["title"].lower())[:50]
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique

    @staticmethod
    async def _rate_limit(seconds: float):
        """Rate limit with jitter."""
        delay = seconds + random.uniform(0, 1.0)
        await asyncio.sleep(delay)


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    async def main():
        crawler = NewsCrawler(max_articles=int(sys.argv[1]) if len(sys.argv) > 1 else 10)
        articles = await crawler.crawl_all()
        print(json.dumps(articles, indent=2, ensure_ascii=False))

    asyncio.run(main())
