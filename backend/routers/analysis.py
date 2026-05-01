"""Analysis API endpoints"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.analyzer import agent
from agent.registry import registry

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeRequest(BaseModel):
    paper_id: str
    analysis_type: str = "deep"

class BatchAnalyzeRequest(BaseModel):
    paper_ids: List[str]
    analysis_type: str = "deep"

class ComparativeRequest(BaseModel):
    paper_ids: List[str]

@router.post("/submit")
async def submit_analysis(req: AnalyzeRequest):
    paper = registry.get(req.paper_id)
    if not paper:
        raise HTTPException(404, f"Paper {req.paper_id} not found")
    task_id = agent.submit_analysis(paper_id=req.paper_id, paper_title=paper.title,
                                    paper_content=paper.content, analysis_type=req.analysis_type)
    return {"task_id": task_id, "status": "pending", "paper_id": req.paper_id}

@router.post("/batch")
async def submit_batch(req: BatchAnalyzeRequest):
    papers_data, missing = [], []
    for pid in req.paper_ids:
        paper = registry.get(pid)
        if paper:
            papers_data.append({"paper_id": pid, "title": paper.title, "content": paper.content})
        else:
            missing.append(pid)
    if not papers_data:
        raise HTTPException(400, "No valid papers found")
    task_ids = await agent.submit_batch(papers_data, analysis_type=req.analysis_type)
    return {"task_ids": task_ids, "submitted": len(task_ids), "missing_papers": missing,
            "message": f"Submitted {len(task_ids)} papers for concurrent analysis"}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = agent.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return task.to_dict()

@router.get("/tasks")
async def list_tasks():
    return {"tasks": agent.get_all_tasks(), "total": len(agent._tasks)}

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    cancelled = await agent.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(400, "Task not found or already completed")
    return {"task_id": task_id, "status": "cancelled"}

@router.post("/comparative")
async def comparative_analysis(req: ComparativeRequest):
    if len(req.paper_ids) < 2:
        raise HTTPException(400, "Comparative analysis requires at least 2 papers")
    if len(req.paper_ids) > 10:
        raise HTTPException(400, "Maximum 10 papers for comparative analysis")
    papers_data = []
    for pid in req.paper_ids:
        paper = registry.get(pid)
        if paper:
            papers_data.append({"paper_id": pid, "title": paper.title,
                                "abstract": paper.abstract or paper.content[:1500],
                                "content": paper.content[:3000]})
    if len(papers_data) < 2:
        raise HTTPException(400, "Could not find enough papers")
    result = await agent.analyze_comparative(papers_data)
    return {"comparative_analysis": result, "paper_count": len(papers_data)}
