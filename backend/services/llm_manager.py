import sys
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import settings
from services.services_utils import is_model_on_cooldown, set_model_cooldown

logger = logging.getLogger("services.llm_manager")

QUOTA_ERRORS = ["429", "rate", "limit", "quota", "resourceexhausted"]

class LLMManager:
    def __init__(self):
        self.gemini_key = settings.GOOGLE_API_KEY
        self.models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        self.clients = {m: self._init_client(m) for m in self.models}

    def _init_client(self, model_name):
        if not self.gemini_key: return None
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=self.gemini_key, temperature=0.3)

    async def run_llm(self, prompt: str, variables: Optional[Dict] = None) -> str:
        if variables:
            for k, v in variables.items():
                prompt = prompt.replace("{" + k + "}", str(v) if v is not None else "")

        for model_name in self.models:
            client = self.clients.get(model_name)
            if not client or is_model_on_cooldown(model_name): continue

            try:
                result = await client.ainvoke([HumanMessage(content=prompt[:30000])])
                return str(result.content or "").strip()
            except Exception as e:
                if any(p in str(e).lower() for p in QUOTA_ERRORS):
                    set_model_cooldown(model_name, 600)
                continue
        return ""

llm_manager = LLMManager()

async def run_llm(prompt: str, variables: Optional[Dict] = None) -> str:
    return await llm_manager.run_llm(prompt, variables)