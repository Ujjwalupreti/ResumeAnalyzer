import logging
import json
from typing import List, Dict, Any, Optional

from services.llm_manager import run_llm
from services.services_utils import safe_json_load
from services.prompts import EXPERIENCE_FILL_PROMPT, PROMPT_IMPROVEMENT_ANALYSIS

logger = logging.getLogger("services.recommendation")
logger.setLevel(logging.INFO)

async def generate_experience_suggestions(
    target_role: str, skills: List[str], projects: List[str], model_pref: str = "auto"
) -> List[Dict[str, Any]]:
    try:
        vars = {
            "target_role": target_role,
            "skills": ", ".join(skills[:5]),
            "projects": ", ".join(projects[:3]),
        }
        output = await run_llm(EXPERIENCE_FILL_PROMPT, variables=vars, preference=model_pref)
        parsed = safe_json_load(output)
        return parsed.get("experiences", []) if isinstance(parsed, dict) else []
    except Exception:
        return []

async def generate_resume_improvement(parsed_resume: Dict[str, Any], model_pref: str = "auto") -> Dict[str, Any]:
    try:
        output = await run_llm(
            PROMPT_IMPROVEMENT_ANALYSIS,
            variables={
                "text": json.dumps(parsed_resume, ensure_ascii=False)[:12000],
                "current_role": parsed_resume.get("user_current_role", ""),
                "target_role": parsed_resume.get("user_target_role", "")
            },
            preference=model_pref,
        )
        analysis = safe_json_load(output)
        if isinstance(analysis, dict):
            analysis.setdefault("summary", {"pros": [], "cons": [], "suggestions": []})
            analysis.setdefault("skills", {"pros": [], "cons": [], "suggestions": []})
            analysis.setdefault("experience", [])
            analysis.setdefault("projects", [])
            analysis.setdefault("overall_tips", [])
            return analysis
        return {}
    except Exception:
        return {}