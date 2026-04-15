
import os
import json
import time
import logging
from celery import Celery, states
from celery.exceptions import Ignore

from config import settings
from services.skill_extractions import process_resume
from services.roadmap_generate import generate_roadmap
from models import Resume

logger = logging.getLogger("backend.task")
logger.setLevel(logging.INFO)



celery_app = Celery(
    "career_pipeline",
    broker=getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
    backend=getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
)



@celery_app.task(
    bind=True,
    name="parse_resume_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def parse_resume_task(self, user_id: int, resume_id: int, file_path: str):
    """
    Full pipeline task:
      1️⃣ Extract and parse resume
      2️⃣ Refine structured JSON
      3️⃣ Generate roadmap (optional)
      4️⃣ Save results to DB
    """
    start_time = time.time()
    try:
        logger.info(f"[Task] 🚀 Starting parse for user {user_id}, resume {resume_id}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        
        parsed = process_resume(user_id=user_id, file_path=file_path, model_pref="auto")

        
        roadmap_data = {}
        if parsed.get("roadmap_ready"):
            roadmap_data = generate_roadmap(
                user_id=user_id,
                target_role=parsed.get("target_role", "Generalist"),
                timeline_months=6,
                parsed_resume=parsed,
                model_pref="auto",
            )

        
        Resume.create_json(
            user_id=user_id,
            file_path=file_path,
            parsed_json=parsed,
            roadmap_json=roadmap_data,
        )

        duration = time.time() - start_time
        logger.info(f"[Task] ✅ Resume {resume_id} parsed & saved successfully in {duration:.2f}s")

        return {
            "resume_id": resume_id,
            "status": "completed",
            "parsed_data": parsed,
            "roadmap_data": roadmap_data,
            "duration_sec": round(duration, 2),
        }

    except FileNotFoundError as e:
        logger.error(f"[Task] ❌ File missing: {e}")
        self.update_state(state=states.FAILURE, meta={"error": str(e)})
        raise Ignore()

    except Exception as e:
        logger.error(f"[Task] ❌ Error during pipeline: {e}")
        
        raise e