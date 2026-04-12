import json
import re
import time
import logging
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("services.services_utils")
logger.setLevel(logging.INFO)

# ==========================================
# 1. LLM COOLDOWN MANAGEMENT
# ==========================================
_MODEL_COOLDOWN: Dict[str, float] = {}

def set_model_cooldown(model_name: str, seconds: int = 600):
    _MODEL_COOLDOWN[model_name] = time.time() + seconds

def is_model_on_cooldown(model_name: str) -> bool:
    expiry = _MODEL_COOLDOWN.get(model_name)
    if not expiry: 
        return False
    if expiry > time.time(): 
        return True
    _MODEL_COOLDOWN.pop(model_name, None)
    return False

# ==========================================
# 2. JSON PARSERS & REPAIR
# ==========================================
def safe_json_load(json_str: str, mode: str = "default") -> Dict[str, Any]:
    """Cleans and parses LLM output into a dictionary."""
    try:
        # Remove markdown code blocks if present
        clean_str = re.sub(r"```json\s*|\s*```", "", json_str).strip()
        return json.loads(clean_str)
    except Exception as e:
        logger.warning(f"JSON Parse failed, attempting repair: {e}")
        try:
            # Basic repair for common LLM truncation issues
            if not json_str.endswith("}"): json_str += "}"
            return json.loads(json_str)
        except:
            return {}

# ==========================================
# 3. SCHEMA DEFINITIONS (Updated with Improvements)
# ==========================================
class ExperienceItem(BaseModel):
    role: str = ""
    company: str = ""
    description: str = ""
    analysis_pros: List[str] = []
    analysis_cons: List[str] = []

class RecommendedExperience(BaseModel):
    role: str = ""
    company: str = "Self-Driven / Open Source"
    description: str = ""
    why_add_this: str = ""

class ProjectItem(BaseModel):
    title: str = ""
    technologies: List[str] = []
    pros: List[str] = []
    cons: List[str] = []
    recommended_bullet_to_add: str = ""

class IssueItem(BaseModel):
    quote: str = ""
    feedback: str = ""
    type: str = "general"
    improvements: List[str] = []  # Added for 2-3 points of improvement versions

class FixCategory(BaseModel):
    category_name: str = ""
    score: int = 0
    max_score: int = 10
    issues: List[IssueItem] = []

class ResumeParsed(BaseModel):
    overall_score: int = 50
    summary_feedback: str = ""
    skills: List[str] = []
    missing_skills: List[str] = []
    recommended_skills_to_add: List[str] = []
    experience: List[ExperienceItem] = []
    recommended_experiences: List[RecommendedExperience] = []
    projects: List[ProjectItem] = []
    top_fixes: List[FixCategory] = []

def validate_resume_json(data: Dict) -> Dict:
    """Ensures data matches expected schema and fixes common LLM list/dict errors."""
    list_fields = ["experience", "projects", "top_fixes", "recommended_experiences"]
    
    for field in list_fields:
        if field in data and isinstance(data[field], dict):
            data[field] = [data[field]]

    try:
        return ResumeParsed(**data).model_dump()
    except ValidationError as e:
        logger.warning(f"[validate_resume_json] Validation error: {e}")
        return data