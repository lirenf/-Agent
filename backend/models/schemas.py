"""
请求/响应数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    text: Optional[str] = None
    url:  Optional[str] = None
    mode: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    dimensions: Optional[List[str]] = None   # e.g. ["methodology", "experiments"]
    session_id: Optional[str] = None


class PaperItem(BaseModel):
    title: str = ""
    text:  str = ""
    url:   Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    papers: List[PaperItem]
    mode: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    session_id: Optional[str] = None


class CompareRequest(BaseModel):
    papers: List[PaperItem]
    session_id: Optional[str] = None


class AnalysisResult(BaseModel):
    title: str = ""
    status: str = "done"
    content: str = ""
    elapsed_s: float = 0.0
    error: Optional[str] = None


class BatchAnalysisResult(BaseModel):
    task_id: str
    results: List[AnalysisResult]
