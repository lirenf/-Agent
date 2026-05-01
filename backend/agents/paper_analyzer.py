"""
论文分析核心 Agent
- 基于 Anthropic SDK 流式输出
- 支持 quick / standard / deep 三种分析深度
- 支持多论文对比
"""
import asyncio
import os
import time
from typing import AsyncIterator, List, Optional

import anthropic

from agents.prompts import (
    build_quick_prompt,
    build_standard_prompt,
    build_deep_prompt,
    build_compare_prompt,
    build_dimension_prompt,
    SYSTEM_PROMPT,
)

MODEL = "claude-sonnet-4-20250514"
client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


class PaperAnalyzer:
    """单篇论文流式分析器"""

    async def analyze_stream(
        self,
        text: str,
        mode: str = "standard",
        dimensions: Optional[List[str]] = None,
    ) -> AsyncIterator[dict]:
        """
        流式分析论文，逐块 yield 结果。
        chunk 格式: {"type": "delta"|"done"|"error", "content": str, "meta": {...}}
        """
        if not text or len(text.strip()) < 100:
            yield {"type": "error", "content": "论文内容过短，请提供完整文本"}
            return

        # 选择 Prompt
        if mode == "quick":
            prompt = build_quick_prompt(text)
        elif mode == "deep":
            prompt = build_deep_prompt(text)
        else:
            prompt = build_standard_prompt(text)

        yield {"type": "meta", "content": "", "meta": {
            "mode": mode,
            "text_length": len(text),
            "started_at": time.time(),
        }}

        # 主分析流
        async for chunk in self._stream(prompt):
            yield chunk

        # 若指定了额外维度，并发分析
        if dimensions and mode != "quick":
            dim_tasks = [
                self._analyze_dimension(text, dim)
                for dim in dimensions
            ]
            for coro in asyncio.as_completed(dim_tasks):
                result = await coro
                yield {"type": "dimension", "content": result["content"], "meta": {"dimension": result["dim"]}}

        yield {"type": "done", "content": "", "meta": {"finished_at": time.time()}}

    async def _analyze_dimension(self, text: str, dimension: str) -> dict:
        prompt = build_dimension_prompt(text, dimension)
        buf = ""
        async for chunk in self._stream(prompt):
            if chunk["type"] == "delta":
                buf += chunk["content"]
        return {"dim": dimension, "content": buf}

    async def _stream(self, prompt: str) -> AsyncIterator[dict]:
        try:
            async with client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield {"type": "delta", "content": text}
        except anthropic.APIError as e:
            yield {"type": "error", "content": f"API 错误: {str(e)}"}
        except Exception as e:
            yield {"type": "error", "content": f"分析失败: {str(e)}"}

    async def compare_stream(self, papers: list) -> AsyncIterator[dict]:
        """多论文对比流式分析"""
        if len(papers) < 2:
            yield {"type": "error", "content": "对比分析至少需要2篇论文"}
            return

        yield {"type": "meta", "content": "", "meta": {
            "paper_count": len(papers),
            "started_at": time.time(),
        }}

        prompt = build_compare_prompt(papers)
        async for chunk in self._stream(prompt):
            yield chunk

        yield {"type": "done", "content": "", "meta": {"finished_at": time.time()}}
