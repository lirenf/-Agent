"""Paper ingestion endpoints"""
import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from agent.registry import registry
from utils.config import settings
from utils.pdf_utils import clean_text, extract_text_from_pdf_bytes, fetch_arxiv_abstract, fetch_arxiv_pdf

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), title: str = Form(default="")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_BYTES:
        raise HTTPException(413, f"File too large (max {settings.MAX_FILE_SIZE_MB} MB)")
    try:
        raw_text = await extract_text_from_pdf_bytes(pdf_bytes)
        content = clean_text(raw_text)
    except Exception as e:
        raise HTTPException(422, f"PDF extraction failed: {e}")
    if len(content.strip()) < 100:
        raise HTTPException(422, "Could not extract meaningful text from PDF")
    paper = registry.create(title=title or file.filename.replace(".pdf", ""),
                            content=content, source="upload", file_size=len(pdf_bytes))
    return {"paper_id": paper.paper_id, "title": paper.title,
            "content_length": len(content), "file_size_kb": round(len(pdf_bytes)/1024, 1),
            "message": "PDF uploaded and text extracted successfully"}

class ArxivRequest(BaseModel):
    arxiv_id: str
    include_pdf: bool = True

@router.post("/arxiv")
async def fetch_arxiv(req: ArxivRequest):
    try:
        meta = await fetch_arxiv_abstract(req.arxiv_id)
    except Exception as e:
        raise HTTPException(422, f"Failed to fetch arXiv metadata: {e}")
    content = ""
    if req.include_pdf:
        try:
            pdf_bytes = await fetch_arxiv_pdf(req.arxiv_id)
            raw_text = await extract_text_from_pdf_bytes(pdf_bytes)
            content = clean_text(raw_text)
        except Exception as e:
            logger.warning(f"PDF fetch failed, using abstract: {e}")
            content = meta.get("abstract", "")
    else:
        content = meta.get("abstract", "")
    paper = registry.create(title=meta.get("title") or req.arxiv_id, content=content,
                            abstract=meta.get("abstract",""), authors=meta.get("authors",[]),
                            year=meta.get("published","")[:4], source="arxiv",
                            arxiv_id=meta.get("arxiv_id", req.arxiv_id))
    return {"paper_id": paper.paper_id, "title": paper.title, "authors": paper.authors,
            "year": paper.year, "content_length": len(content), "arxiv_id": paper.arxiv_id,
            "message": "arXiv paper fetched successfully"}

class TextRequest(BaseModel):
    title: str
    content: str
    abstract: str = ""
    authors: list = []
    year: str = ""

@router.post("/text")
async def add_text_paper(req: TextRequest):
    if len(req.content.strip()) < 50:
        raise HTTPException(400, "Content too short")
    content = clean_text(req.content)
    paper = registry.create(title=req.title, content=content, abstract=req.abstract,
                            authors=req.authors, year=req.year, source="text")
    return {"paper_id": paper.paper_id, "title": paper.title,
            "content_length": len(content), "message": "Paper added successfully"}

@router.get("/")
async def list_papers():
    return {"papers": registry.list_all(), "total": registry.count()}

@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    paper = registry.get(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    return paper.to_dict(include_content=True)

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    if not registry.delete(paper_id):
        raise HTTPException(404, "Paper not found")
    return {"message": "Paper deleted", "paper_id": paper_id}
