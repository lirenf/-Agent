"""
异步网页文本抓取工具
支持: 普通网页 | arXiv | ACM/IEEE/Springer DOI
"""
import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class WebScraper:
    TIMEOUT = 30

    async def fetch_text(self, url: str) -> Optional[str]:
        """抓取 URL 并提取论文正文文本"""
        url = url.strip()

        # arXiv 特殊处理：转为 abs 页面
        url = self._normalize_arxiv(url)

        try:
            import aiohttp
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; PaperAnalysisBot/1.0; "
                    "+https://github.com/paper-agent)"
                )
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.TIMEOUT)) as resp:
                    if resp.status != 200:
                        logger.warning(f"HTTP {resp.status} for {url}")
                        return None
                    html = await resp.text(errors="replace")

            soup = BeautifulSoup(html, "html.parser")

            # 移除脚本/样式
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # arXiv 摘要页
            if "arxiv.org" in url:
                return self._extract_arxiv(soup)

            # 通用提取
            for selector in ["article", "main", ".paper-body", "#content", "body"]:
                el = soup.select_one(selector)
                if el:
                    text = el.get_text(separator="\n", strip=True)
                    if len(text) > 500:
                        return self._clean(text)

            return self._clean(soup.get_text(separator="\n", strip=True))

        except ImportError:
            logger.error("aiohttp or beautifulsoup4 not installed")
            return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.warning(f"Fetch error for {url}: {e}")
            return None

    def _normalize_arxiv(self, url: str) -> str:
        """arXiv PDF → abs"""
        url = re.sub(r"arxiv\.org/pdf/(\d+\.\d+)(v\d+)?\.pdf", r"arxiv.org/abs/\1", url)
        return url

    def _extract_arxiv(self, soup) -> str:
        title = soup.select_one("h1.title")
        abstract = soup.select_one("blockquote.abstract")
        authors = soup.select_one(".authors")
        parts = []
        if title:
            parts.append(f"Title: {title.get_text(strip=True)}")
        if authors:
            parts.append(f"Authors: {authors.get_text(strip=True)}")
        if abstract:
            parts.append(f"Abstract:\n{abstract.get_text(strip=True)}")
        return "\n\n".join(parts) if parts else ""

    def _clean(self, text: str) -> str:
        lines = [l.strip() for l in text.splitlines()]
        lines = [l for l in lines if l]
        # 合并短行
        result, buf = [], ""
        for l in lines:
            if len(l) < 80 and buf:
                buf += " " + l
            else:
                if buf:
                    result.append(buf)
                buf = l
        if buf:
            result.append(buf)
        return "\n".join(result)
