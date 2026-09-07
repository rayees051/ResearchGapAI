from fastapi import APIRouter
from app.api.v1 import auth, projects, papers, gaps

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(gaps.router, prefix="/gaps", tags=["gaps"])
