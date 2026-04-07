import logging
import json
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from pydantic import BaseModel

from routes.auth import get_current_user
from models import Resume, User
from services.skill_extractions import process_resume

logger = logging.getLogger("routes.user")
router = APIRouter(tags=["User"])

class ProfileUpdate(BaseModel):
    name: str | None = None
    current_role: str | None = None
    target_role: str | None = None
    career_level: str | None = None
    location: str | None = None  

@router.put("/profile")
def update_profile(payload: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["user_id"]
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None} 
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        User.update(user_id, **update_data) 
        updated = User.get_by_id(user_id) 
        return {"message": "Profile updated successfully", "user": updated}
    except Exception as e:
        logger.exception(f"Profile update failed: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = User.get_by_id(current_user["user_id"]) 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name"),
        "current_role": user.get("current_role"),
        "target_role": user.get("target_role"),
        "location": user.get("location"),  
        "created_at": user.get("created_at"),
    }

@router.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...), model_pref: Optional[str] = Query("auto"), current_user: Dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file upload")

        parsed = await process_resume(
            user_id=user_id,
            file_bytes=content,
            filename=file.filename,
            model_pref=model_pref,
        )

        Resume.create_binary(
            user_id=user_id,
            filename=file.filename,
            file_bytes=content,
            mime_type=file.content_type or "application/pdf",
            parsed_json=parsed,
        )
        return {"message": "Resume parsed successfully", "parsed_json": parsed}
    except Exception as e:
        logger.exception(f"Resume parsing failed: {e}")
        raise HTTPException(status_code=500, detail="Resume parsing failed")

@router.get("/resume/history")
async def resume_history(current_user: Dict = Depends(get_current_user)):
    records = Resume.get_by_user(current_user["user_id"], limit=7)
    return {"resumes": records}

@router.get("/resume/load/{resume_id}")
async def load_resume(resume_id: int, current_user: Dict = Depends(get_current_user)):
    rec = Resume.get_by_id(resume_id)
    if not rec or rec["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Not found or unauthorized")

    parsed_data = rec.get("parsed_json", {})
    try:
        if isinstance(parsed_data, str):
            parsed_data = json.loads(parsed_data)
    except Exception:
        parsed_data = {}

    return {
        "resume_id": rec["resume_id"],
        "file_path": rec.get("file_path"),
        "uploaded_at": rec.get("uploaded_at"),
        "parsed_json": parsed_data,
    }

@router.delete("/resume/delete/{resume_id}")
async def delete_resume(resume_id: int, current_user: Dict = Depends(get_current_user)):
    try:
        Resume.delete(resume_id, current_user["user_id"])
        return {"message": "Resume deleted successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete resume")