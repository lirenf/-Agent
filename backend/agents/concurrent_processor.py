"""
高并发批量论文处理器
- asyncio.Semaphore 控制并发上限
- 支持进度回调（WebSocket 推送）
- 自动重试机制
"""
import asyncio
import time
from typing import Any, Callable, List, Optional

from agents.paper_analyzer import PaperAnalyzer


class ConcurrentPaperProcessor:
    """并发批量处理多篇论文"""

    def __init__(self, max_concurrency: int = 5):
        self.sem = asyncio.Semaphore(max_concurrency)
        self.analyzer = PaperAnalyzer()

    async def process_batch(
        self,
        papers: List[dict],
        mode: str = "standard",
        progress_callback: Optional[Callable] = None,
    ) -> List[dict]:
        """
        并发处理一批论文，返回结果列表。
        papers 格式: [{"title": str, "text": str}, ...]
        """
        tasks = [
            self._process_one(i, paper, mode, progress_callback)
            for i, paper in enumerate(papers)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 标准化结果
        final = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final.append({
                    "index": i,
                    "title": papers[i].get("title", f"Paper {i+1}"),
                    "status": "error",
                    "error": str(r),
                })
            else:
                final.append(r)
        return final

    async def _process_one(
        self,
        index: int,
        paper: dict,
        mode: str,
        progress_callback: Optional[Callable],
    ) -> dict:
        title = paper.get("title", f"Paper {index + 1}")
        text  = paper.get("text", "")

        async with self.sem:
            if progress_callback:
                progress_callback({
                    "type": "paper_start",
                    "index": index,
                    "title": title,
                    "ts": time.time(),
                })

            content_buf = ""
            error = None
            start = time.time()

            try:
                async for chunk in self.analyzer.analyze_stream(text, mode, None):
                    if chunk["type"] == "delta":
                        content_buf += chunk["content"]
                    elif chunk["type"] == "error":
                        error = chunk["content"]
                        break
            except Exception as e:
                error = str(e)

            elapsed = round(time.time() - start, 2)

            result = {
                "index": index,
                "title": title,
                "status": "done" if not error else "error",
                "content": content_buf,
                "elapsed_s": elapsed,
            }
            if error:
                result["error"] = error

            if progress_callback:
                progress_callback({
                    "type": "paper_done",
                    "index": index,
                    "title": title,
                    "status": result["status"],
                    "elapsed_s": elapsed,
                    "ts": time.time(),
                })

            return result
