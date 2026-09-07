from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.database import get_session
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.gap import ResearchGap
from app.schemas.gap import ResearchGapRead

router = APIRouter()

@router.get("/", response_model=List[ResearchGapRead])
async def list_gaps(
    project_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    proj_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    if not proj_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    result = await db.execute(
        select(ResearchGap)
        .where(ResearchGap.project_id == project_id)
        .order_by(ResearchGap.rank.asc())
    )
    return result.scalars().all()

@router.get("/synthesis")
async def get_synthesis_report(
    project_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    return {
        "project_id": project.id,
        "synthesis_report": project.synthesis_report or "No report generated yet."
    }

@router.put("/synthesis")
async def update_synthesis_report(
    project_id: uuid.UUID = Query(...),
    content: str = Query(..., description="Markdown content of synthesis report"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
        
    project.synthesis_report = content
    db.add(project)
    await db.commit()
    return {"status": "success", "message": "Synthesis report updated"}
