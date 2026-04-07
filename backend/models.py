# backend/models.py
from datetime import datetime
from typing import Optional, Dict, List
from database import get_db
import logging, json

mysql_db = get_db()
logger = logging.getLogger(__name__)

class User:
    @staticmethod
    def create(email: str, password_hash: str, name: Optional[str] = None, current_role: Optional[str] = None, target_role: Optional[str] = None, location: Optional[str] = None, is_email_verified: int = 0) -> int:
        with mysql_db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (
                    email, password_hash, name, current_role, target_role, location,
                    is_email_verified, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (email, password_hash, name, current_role, target_role, location, is_email_verified))
            return cursor.lastrowid

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        return mysql_db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        return mysql_db.fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))

    @staticmethod
    def update(user_id: int, **fields):
        allowed = {"name", "current_role", "target_role", "location", "is_email_verified", "mfa_temp_token", "mfa_otp_hash", "mfa_otp_expires"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates: return None
        columns = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        with mysql_db.get_cursor() as cursor:
            cursor.execute(f"UPDATE users SET {columns}, updated_at = NOW() WHERE user_id = %s", values)
        return user_id

class Resume:
    @staticmethod
    def create_binary(user_id: int, filename: str, file_bytes: bytes, mime_type: str, parsed_json: dict):
        try:
            query = """
                INSERT INTO resumes (user_id, file_path, raw_file, mime_type, parsed_json, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            mysql_db.execute_query(query, (user_id, filename, file_bytes, mime_type, json.dumps(parsed_json, ensure_ascii=False), datetime.now()))
        except Exception as e:
            logger.exception(f"[create_binary] ❌ Failed: {e}")
            raise

    @staticmethod
    def get_by_user(user_id: int, limit: int = 7):
        return mysql_db.fetch_all("SELECT resume_id, file_path, uploaded_at FROM resumes WHERE user_id=%s ORDER BY uploaded_at DESC LIMIT %s", (user_id, limit))

    @staticmethod
    def get_by_id(resume_id: int):
        return mysql_db.fetch_one("SELECT * FROM resumes WHERE resume_id=%s", (resume_id,))

    @staticmethod
    def delete(resume_id: int, user_id: int):
        mysql_db.execute_query("DELETE FROM resumes WHERE resume_id=%s AND user_id=%s", (resume_id, user_id))

class Skill:
    @staticmethod
    def get_or_create(skill_name: str, category: str = None) -> int:
        row = mysql_db.fetch_one("SELECT skill_id FROM skills WHERE skill_name = %s", (skill_name,))
        if row: return row["skill_id"]
        with mysql_db.get_cursor() as cursor:
            cursor.execute("INSERT INTO skills (skill_name, category) VALUES (%s, %s)", (skill_name, category))
            return cursor.lastrowid

class UserSkill:
    @staticmethod
    def create_or_update(user_id: int, skill_id: int, level: str):
        row = mysql_db.fetch_one("SELECT user_skill_id FROM user_skills WHERE user_id = %s AND skill_id = %s", (user_id, skill_id))
        with mysql_db.get_cursor() as cursor:
            if row:
                cursor.execute("UPDATE user_skills SET level = %s, last_updated = NOW() WHERE user_skill_id = %s", (level, row["user_skill_id"]))
            else:
                cursor.execute("INSERT INTO user_skills (user_id, skill_id, level, last_updated) VALUES (%s, %s, %s, NOW())", (user_id, skill_id, level))