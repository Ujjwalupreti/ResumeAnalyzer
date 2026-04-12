import io
import logging
import hashlib
import json
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader
import docx

from models import User, Resume
from database import get_db
from services.prompts import PROMPT_PARSE
from services.llm_manager import run_llm
from services.services_utils import safe_json_load, validate_resume_json

logger = logging.getLogger("services.skill_extractions")
logger.setLevel(logging.INFO)
mysql_db = get_db()

def get_content_hash(file_bytes: bytes) -> str:
    """Generates a unique SHA-256 hash for the file content."""
    return hashlib.sha256(file_bytes).hexdigest()

def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """Extracts text from PDF or DOCX while preserving structure."""
    try:
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        elif filename.lower().endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            return "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"[extract_text_from_bytes] Error: {e}")
        return ""

async def process_resume(
    user_id: int,
    file_bytes: bytes,
    filename: Optional[str] = None,
    model_pref: str = "auto",
) -> Dict[str, Any]:
    
    # 1. Hashing Retrieval System (Consistency Cache)
    file_hash = get_content_hash(file_bytes)
    existing = mysql_db.fetch_one(
        "SELECT parsed_json FROM resumes WHERE content_hash = %s LIMIT 1", 
        (file_hash,)
    )
    if existing:
        logger.info(f"Retrieved cached analysis for hash {file_hash[:8]}")
        return json.loads(existing['parsed_json'])

    # 2. Extract raw text
    text = extract_text_from_bytes(file_bytes, filename or "resume.pdf")
    if not text.strip():
        return {"error": "Empty or unreadable file"}

    # 3. Fetch User Context
    user = User.get_by_id(user_id) or {}
    current_role = user.get("current_role", "Professional")
    target_role = user.get("target_role", "Software Developer")

    # 4. Single-Pass Audit via Gemini (Hugging Face removed)
    try:
        output = await run_llm(
            PROMPT_PARSE,
            variables={
                "text": text[:14000],
                "current_role": current_role, 
                "target_role": target_role
            }
        )
        parsed = safe_json_load(output)
    except Exception as e:
        logger.exception(f"[process_resume] LLM analysis failed: {e}")
        parsed = {}

    # 5. Schema Validation & Improvement Injection
    final_data = validate_resume_json(parsed)
    final_data["content_hash"] = file_hash  # Include hash for storage

    return final_data