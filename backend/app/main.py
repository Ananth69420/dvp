from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(
    title="Log File Parser & AI-Assisted Log Visualization API",
    description="Deterministic log parsing, high-performance Pandas analytics, and AI-assisted visualization recommendations.",
    version="1.0.0",
)

# Allow CORS for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount frontend production build if available
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "Log File Parser & AI-Assisted Visualization System API",
            "docs_url": "/docs",
            "health_check": "/api/health",
        }

