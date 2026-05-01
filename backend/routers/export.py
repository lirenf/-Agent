"""Export analysis results"""
import json, logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from agent.analyzer import agent

logger = logging.getLogger(__name__)
router = APIRouter()

class ExportRequest(BaseModel):
    task_ids: List[str]
    format: str = "json"

@router.post("/results")
async def export_results(req: ExportRequest):
    tasks = [t for tid in req.task_ids
             for t in [agent.get_task(tid)] if t and t.result]
    if not tasks:
        raise HTTPException(404, "No completed analyses found")

    if req.format == "json":
        data = {
            "export_time": datetime.now().isoformat(), "count": len(tasks),
            "analyses": [{"task_id": t.task_id, "paper_title": t.paper_title,
                          "duration_s": round(t.completed_at - t.started_at, 2)
                          if t.started_at and t.completed_at else None,
                          "result": t.result} for t in tasks]
        }
        return JSONResponse(content=data)
    elif req.format == "markdown":
        lines = [f"# Paper Analysis Export", f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        for t in tasks:
            r = t.result or {}
            meta = r.get("meta", {})
            s = r.get("executive_summary", {})
            c = r.get("critical_analysis", {})
            e = r.get("engineering_perspective", {})
            lines += [
                f"---", f"## {t.paper_title}",
                f"**Authors**: {', '.join(meta.get('authors',[]))} | **Year**: {meta.get('year','N/A')}",
                "", f"### One-liner", s.get("one_liner",""), "",
                f"### Problem", s.get("problem_statement",""), "",
                f"### Novelty Score: {s.get('novelty_score','?')}/10", s.get("novelty_justification",""), "",
                f"### Strengths",
            ]
            for st in c.get("strengths",[]):
                lines.append(f"- **{st.get('point','')}**: {st.get('elaboration','')}")
            lines += ["", f"### Weaknesses"]
            for w in c.get("weaknesses",[]):
                lines.append(f"- [{w.get('severity','?').upper()}] **{w.get('point','')}**: {w.get('elaboration','')}")
            lines += ["", f"### Engineering", e.get("implementation_notes",""), ""]
        content = "\n".join(lines)
        return PlainTextResponse(content=content, media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=analysis_export.md"})
    else:
        raise HTTPException(400, f"Unsupported format: {req.format}")

@router.get("/task/{task_id}/markdown")
async def export_single_markdown(task_id: str):
    return await export_results(ExportRequest(task_ids=[task_id], format="markdown"))
