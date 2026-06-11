"""
AI 重写 - 调用 sangwoozen API 将英文新闻重写为中文和英文版本
重写策略: 保留核心技术信息, 改变表述方式, 避免直接翻译
"""
import os
import re
import logging
import asyncio
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "https://sangwoozen.com/v1")
AI_MODEL = os.getenv("AI_MODEL", "qwen3.6-27b")


def _api_headers() -> dict:
    return {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }


async def rewrite_article(
    title: str,
    content: str,
    source: str = "",
    categories: list[str] | None = None,
    max_retries: int = 3,
) -> dict:
    """
    Call AI API to rewrite an English article into:
    - Chinese version (title_zh, content_zh)
    - English rewritten version (title_en, content_en)
    
    Returns dict with title_zh, content_zh, title_en, content_en, slug
    """
    if not AI_API_KEY:
        logger.warning("AI_API_KEY not set, skipping AI rewrite")
        return _fallback_rewrite(title, content)

    prompt = f"""You are a technology news editor for a Korean food import company's website that also covers tech hardware news.

Original article from {source or "unknown source"}:
Title: {title}
Content: {content[:3000]}

Your task:
1. Rewrite the article in BOTH Chinese and English with YOUR OWN WORDS
2. Keep all technical facts, specs, and data accurate
3. Make it concise (300-500 words per language)
4. Add a brief connection to why this matters for PC gamers/enthusiasts who might use their systems for food-related content creation
5. Generate a URL-friendly slug based on the English title

Return ONLY valid JSON in this format:
{{
  "title_zh": "中文标题",
  "content_zh": "中文内容 (300-500字, 可以包含HTML标签如<p>, <strong>, <a>)",
  "title_en": "English title",
  "content_en": "English content (300-500 words, can include HTML tags)",
  "slug": "url-friendly-slug"
}}

Categories: {', '.join(categories or [])}"""

    last_error = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_API_BASE_URL}/chat/completions",
                    headers=_api_headers(),
                    json={
                        "model": AI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a helpful tech news editor. Return ONLY valid JSON, no markdown, no explanation."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"].strip()

            # Extract JSON from response
            result = _extract_json(raw)
            if result:
                logger.info(f"AI rewrite successful: {title[:50]}...")
                return result
            else:
                logger.warning(f"AI returned non-JSON: {raw[:200]}")
                last_error = ValueError("No valid JSON in response")

        except Exception as e:
            last_error = e
            logger.warning(f"AI rewrite attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)

    logger.error(f"AI rewrite failed after {max_retries} attempts: {last_error}")
    return _fallback_rewrite(title, content)


def _fallback_rewrite(title: str, content: str) -> dict:
    """Fallback when AI is unavailable - use original content."""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:80]
    return {
        "title_zh": title,  # Will need manual translation later
        "content_zh": content[:2000] if content else "",
        "title_en": title,
        "content_en": content[:2000] if content else "",
        "slug": slug or "news-article",
    }


def _extract_json(text: str) -> dict | None:
    """Extract JSON object from AI response."""
    # Try direct parse first
    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    match = re.search(r'```(?:json)?\s*\n([\s\S]*?)\n```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find { ... } pattern
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


async def rewrite_batch(articles: list[dict], concurrency: int = 3) -> list[dict]:
    """Rewrite multiple articles with concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def _rewrite_one(article: dict) -> dict:
        async with semaphore:
            rewritten = await rewrite_article(
                title=article["title"],
                content=article.get("content_preview", ""),
                source=article.get("source", ""),
                categories=article.get("categories", []),
            )
            rewritten["original_url"] = article.get("url", "")
            rewritten["original_source"] = article.get("source", "")
            return rewritten

    tasks = [_rewrite_one(a) for a in articles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid = []
    for r in results:
        if isinstance(r, dict):
            valid.append(r)
        else:
            logger.error(f"Rewrite task failed: {r}")

    return valid


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    async def main():
        # Read articles from stdin or test
        if not sys.stdin.isatty():
            articles = json.loads(sys.stdin.read())
        else:
            articles = [{
                "title": "Test Article: New GPU Released",
                "content_preview": "A new graphics card has been announced with improved performance.",
                "source": "Test",
                "url": "https://example.com/test",
                "categories": ["GPU"],
            }]

        results = await rewrite_batch(articles)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    asyncio.run(main())
