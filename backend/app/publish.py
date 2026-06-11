"""
新闻发布 - 将爬取+AI重写后的新闻写入 SQLite
"""
import asyncio
import logging
import sys
import os

from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from .database import init_db, get_session
from .models import News, SystemLog
from .crawler import NewsCrawler
from .ai_rewrite import rewrite_batch

logger = logging.getLogger(__name__)


async def publish_articles(
    max_articles: int = 10,
    days_back: int = 7,
    rewrite: bool = True,
    auto_publish: bool = True,
) -> dict:
    """
    Full pipeline: crawl -> rewrite -> publish
    
    Returns: {"crawled": N, "rewritten": N, "published": N, "skipped": N}
    """
    init_db()
    stats = {"crawled": 0, "rewritten": 0, "published": 0, "skipped": 0}

    # Step 1: Crawl
    logger.info("Starting news crawl...")
    crawler = NewsCrawler(max_articles=max_articles, days_back=days_back)
    articles = await crawler.crawl_all()
    stats["crawled"] = len(articles)
    logger.info(f"Crawled {len(articles)} articles")

    if not articles:
        _log_system("info", "News crawl: no new articles found")
        return stats

    # Step 2: AI Rewrite
    if rewrite:
        logger.info("Starting AI rewrite...")
        rewritten = await rewrite_batch(articles)
        stats["rewritten"] = len(rewritten)
    else:
        # Use original content
        rewritten = []
        for a in articles:
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', a["title"].lower()).strip('-')[:80]
            rewritten.append({
                "title_zh": a["title"],
                "content_zh": a.get("content_preview", ""),
                "title_en": a["title"],
                "content_en": a.get("content_preview", ""),
                "slug": slug or "news-article",
                "original_url": a.get("url", ""),
                "original_source": a.get("source", ""),
            })

    # Step 3: Publish to DB
    logger.info("Publishing to database...")
    session = next(get_session())
    try:
        for article in rewritten:
            slug = article.get("slug", "")
            title_en = article.get("title_en", "")

            # Check for duplicate by title similarity
            existing = session.query(News).filter(
                News.title_en.ilike(f"%{title_en[:30]}%")
            ).first()

            if existing:
                stats["skipped"] += 1
                logger.info(f"Skipped duplicate: {title_en[:50]}")
                continue

            news = News(
                title_zh=article.get("title_zh", ""),
                title_en=title_en,
                content_zh=article.get("content_zh", ""),
                content_en=article.get("content_en", ""),
                slug=slug,
                status="published" if auto_publish else "draft",
                source="crawler",
                created_at=datetime.now(),
                published_at=datetime.now() if auto_publish else None,
            )
            session.add(news)
            stats["published"] += 1
            logger.info(f"Published: {title_en[:50]}")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        _log_system("error", f"News publish error: {e}")
    finally:
        session.close()

    _log_system("info", f"News pipeline: crawled={stats['crawled']}, published={stats['published']}, skipped={stats['skipped']}")
    return stats


def _log_system(level: str, message: str):
    """Write to system_log table."""
    try:
        init_db()
        session = next(get_session())
        log = SystemLog(level=level, message=message, created_at=datetime.now())
        session.add(log)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"System log error: {e}")


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    async def main():
        max_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        stats = await publish_articles(max_articles=max_articles)
        print(json.dumps(stats, indent=2))

    asyncio.run(main())
