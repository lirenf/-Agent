"""PDF extraction and text processing utilities"""
import io, logging, re
import httpx

logger = logging.getLogger(__name__)

async def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append(f"[Page {i+1}]\n{text}")
            return "\n\n".join(pages)
    except ImportError:
        return _extract_with_pypdf(pdf_bytes)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")

def _extract_with_pypdf(pdf_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        texts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                texts.append(f"[Page {i+1}]\n{text}")
        return "\n\n".join(texts)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")

async def fetch_arxiv_pdf(arxiv_id: str) -> bytes:
    arxiv_id = arxiv_id.strip()
    if arxiv_id.startswith("http"):
        match = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s/]+)", arxiv_id)
        if match:
            arxiv_id = match.group(1).replace(".pdf", "")
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(pdf_url)
        resp.raise_for_status()
        return resp.content

async def fetch_arxiv_abstract(arxiv_id: str) -> dict:
    arxiv_id = arxiv_id.strip().replace(".pdf", "")
    if arxiv_id.startswith("http"):
        match = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s/]+)", arxiv_id)
        if match:
            arxiv_id = match.group(1)
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()
        content = resp.text
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {}
    def get(tag):
        el = entry.find(f"atom:{tag}", ns)
        return el.text.strip() if el is not None and el.text else ""
    authors = [a.find("atom:name", ns).text.strip()
               for a in entry.findall("atom:author", ns)
               if a.find("atom:name", ns) is not None]
    return {
        "arxiv_id": arxiv_id,
        "title": get("title"),
        "abstract": get("summary"),
        "authors": authors,
        "published": get("published")[:10] if get("published") else "",
        "categories": [c.attrib.get("term", "") for c in entry.findall("atom:category", ns)],
    }

def clean_text(text: str, max_chars: int = 120000) -> str:
    import re
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    if len(text) > max_chars:
        half = max_chars // 2
        text = text[:half] + "\n\n[... TRUNCATED ...]\n\n" + text[-half:]
    return text
