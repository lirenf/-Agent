"""Core Paper Analysis Agent with high-concurrency support"""
import asyncio, json, logging, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import anthropic
from utils.config import settings
from agent.prompts import SYSTEM_PROMPT, DEEP_ANALYSIS_PROMPT, COMPARATIVE_ANALYSIS_PROMPT, QUICK_SUMMARY_PROMPT

logger = logging.getLogger(__name__)

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AnalysisTask:
    task_id: str
    paper_id: str
    paper_title: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    progress: int = 0
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self):
        return {
            "task_id": self.task_id, "paper_id": self.paper_id,
            "paper_title": self.paper_title, "status": self.status.value,
            "progress": self.progress, "result": self.result, "error": self.error,
            "created_at": self.created_at, "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": round(self.completed_at - self.started_at, 2)
                        if self.started_at and self.completed_at else None,
        }

class PaperAnalysisAgent:
    """High-concurrency paper analysis agent backed by Claude.
    Uses asyncio.Semaphore to cap concurrent API calls."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)
        self._tasks: Dict[str, AnalysisTask] = {}
        self._running_futures: Dict[str, asyncio.Task] = {}

    def submit_analysis(self, paper_id, paper_title, paper_content, analysis_type="deep"):
        task_id = str(uuid.uuid4())
        task = AnalysisTask(task_id=task_id, paper_id=paper_id, paper_title=paper_title)
        self._tasks[task_id] = task
        future = asyncio.create_task(self._run_analysis(task, paper_content, analysis_type))
        self._running_futures[task_id] = future
        logger.info(f"Submitted task {task_id} for '{paper_title}'")
        return task_id

    async def submit_batch(self, papers, analysis_type="deep"):
        task_ids = []
        for paper in papers:
            task_id = self.submit_analysis(
                paper_id=paper["paper_id"], paper_title=paper.get("title", "Unknown"),
                paper_content=paper["content"], analysis_type=analysis_type)
            task_ids.append(task_id)
        return task_ids

    def get_task(self, task_id):
        return self._tasks.get(task_id)

    def get_all_tasks(self):
        return [t.to_dict() for t in self._tasks.values()]

    async def cancel_task(self, task_id):
        future = self._running_futures.get(task_id)
        if future and not future.done():
            future.cancel()
            task = self._tasks.get(task_id)
            if task:
                task.status = AnalysisStatus.CANCELLED
            return True
        return False

    async def analyze_comparative(self, papers_data):
        summaries = []
        for p in papers_data:
            summaries.append(
                f"### Paper {p.get('paper_id','?')}: {p.get('title','Unknown')}\n"
                f"{p.get('abstract', p.get('content','')[:2000])}")
        prompt = COMPARATIVE_ANALYSIS_PROMPT.format(papers_summary="\n\n".join(summaries))
        return await self._call_claude(prompt, max_tokens=4096)

    async def _run_analysis(self, task, paper_content, analysis_type):
        async with self.semaphore:
            task.status = AnalysisStatus.RUNNING
            task.started_at = time.time()
            task.progress = 10
            try:
                if analysis_type == "quick":
                    prompt = QUICK_SUMMARY_PROMPT.format(paper_content=paper_content[:30000])
                else:
                    prompt = DEEP_ANALYSIS_PROMPT.format(paper_content=paper_content[:100000])
                task.progress = 30
                result = await asyncio.wait_for(
                    self._call_claude(prompt), timeout=settings.ANALYSIS_TIMEOUT_SECONDS)
                task.progress = 100
                task.result = result
                task.status = AnalysisStatus.COMPLETED
                task.completed_at = time.time()
                logger.info(f"[{task.task_id}] Completed in {task.completed_at - task.started_at:.1f}s")
            except asyncio.TimeoutError:
                task.status = AnalysisStatus.FAILED
                task.error = f"Timed out after {settings.ANALYSIS_TIMEOUT_SECONDS}s"
            except asyncio.CancelledError:
                task.status = AnalysisStatus.CANCELLED
            except Exception as e:
                task.status = AnalysisStatus.FAILED
                task.error = str(e)
                logger.error(f"[{task.task_id}] Failed: {e}", exc_info=True)
            finally:
                self._running_futures.pop(task.task_id, None)

    async def _call_claude(self, user_prompt, max_tokens=None):
        max_tokens = max_tokens or settings.MAX_TOKENS
        message = await self.client.messages.create(
            model=settings.CLAUDE_MODEL, max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}])
        raw_text = message.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            return {"raw_response": raw_text, "parse_error": str(e)}

agent = PaperAnalysisAgent()
