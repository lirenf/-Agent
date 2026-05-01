"""高并发科研论文深度分析 Agent - 主应用入口"""
import logging, os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import analysis, papers, export
from utils.config import settings

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Paper Analysis Agent starting...")
    yield
    logger.info("Paper Analysis Agent shutting down...")

app = FastAPI(title="高并发科研论文深度分析 Agent",
    description="Academic Paper Deep Analysis powered by Claude AI",
    version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Static files & templates
_this = os.path.dirname(__file__)
frontend_dir = os.path.join(_this, "..", "frontend")
static_dir   = os.path.join(frontend_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=os.path.join(frontend_dir, "templates"))

app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(papers.router,   prefix="/api/papers",   tags=["Papers"])
app.include_router(export.router,   prefix="/api/export",   tags=["Export"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=settings.DEBUG, workers=1, log_level="info")
