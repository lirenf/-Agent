"""In-memory paper registry"""
import time, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Paper:
    paper_id: str
    title: str
    content: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    source: str = "upload"
    arxiv_id: str = ""
    file_size: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self, include_content=False):
        d = {
            "paper_id": self.paper_id, "title": self.title,
            "abstract": self.abstract, "authors": self.authors,
            "year": self.year, "source": self.source,
            "arxiv_id": self.arxiv_id, "file_size": self.file_size,
            "created_at": self.created_at, "content_length": len(self.content),
        }
        if include_content:
            d["content"] = self.content[:2000] + "..." if len(self.content) > 2000 else self.content
        return d

class PaperRegistry:
    def __init__(self):
        self._papers: Dict[str, Paper] = {}

    def create(self, title, content, abstract="", authors=None, year="",
               source="upload", arxiv_id="", file_size=0):
        paper = Paper(paper_id=str(uuid.uuid4()), title=title, content=content,
                      abstract=abstract, authors=authors or [], year=year,
                      source=source, arxiv_id=arxiv_id, file_size=file_size)
        self._papers[paper.paper_id] = paper
        return paper

    def get(self, paper_id):
        return self._papers.get(paper_id)

    def list_all(self):
        return [p.to_dict() for p in self._papers.values()]

    def delete(self, paper_id):
        if paper_id in self._papers:
            del self._papers[paper_id]
            return True
        return False

    def count(self):
        return len(self._papers)

registry = PaperRegistry()
