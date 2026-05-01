"""
PDF 文本提取工具
优先使用 pdfplumber，回退到 PyPDF2
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract(self, raw: bytes) -> Optional[str]:
        """从 PDF bytes 提取纯文本"""
        text = self._extract_pdfplumber(raw)
        if not text:
            text = self._extract_pypdf2(raw)
        return text.strip() if text else None

    def _extract_pdfplumber(self, raw: bytes) -> str:
        try:
            import pdfplumber
            buf = io.BytesIO(raw)
            pages_text = []
            with pdfplumber.open(buf) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
            return "\n\n".join(pages_text)
        except ImportError:
            logger.debug("pdfplumber not installed, trying PyPDF2")
            return ""
        except Exception as e:
            logger.warning(f"pdfplumber error: {e}")
            return ""

    def _extract_pypdf2(self, raw: bytes) -> str:
        try:
            import PyPDF2
            buf = io.BytesIO(raw)
            reader = PyPDF2.PdfReader(buf)
            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            return "\n\n".join(pages_text)
        except ImportError:
            logger.debug("PyPDF2 not installed")
            return ""
        except Exception as e:
            logger.warning(f"PyPDF2 error: {e}")
            return ""
