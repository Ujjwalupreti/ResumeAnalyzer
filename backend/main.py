# backend/main.py
import os, sys, logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from database import init_db
from routes import auth, user

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="Resume Analyzer API", version="1.0.0")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("main")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",      
        "http://127.0.0.1:5500",      
        "http://localhost:5173",      
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",      
        "http://127.0.0.1:8000",
        "*"                           
    ],
    allow_credentials=True,
    allow_methods=["*"],            
    allow_headers=["*"],              
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        logger.info("MySQL initialized successfully")
    except Exception as e:
        logger.warning(f"MySQL init failed: {e}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

from fastapi.staticfiles import StaticFiles

app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/user")

frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")