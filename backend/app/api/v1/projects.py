from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import asyncio
from datetime import datetime
from app.models.log import AgentLog
from app.core.database import async_session_maker

from app.core.database import get_session
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()

@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Project).where(Project.user_id == current_user.id)
    )
    return result.scalars().all()

@router.post("/", response_model=ProjectRead)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_project = Project(
        title=project_in.title,
        description=project_in.description,
        user_id=current_user.id,
        status="idle"
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@router.get("/{id}", response_model=ProjectRead)
async def get_project(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Project).where(Project.id == id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    return project

@router.delete("/{id}", response_model=ProjectRead)
async def delete_project(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Project).where(Project.id == id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    await db.delete(project)
    await db.commit()
    return project

@router.post("/{id}/run", response_model=ProjectRead)
async def run_project_pipeline(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify project exists and user owns it
    result = await db.execute(
        select(Project).where(Project.id == id, Project.user_id == current_user.id)
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
        
    if project.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline is already running for this project"
        )
        
    # Update status to running
    project.status = "running"
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # TODO: Trigger Celery task
    # For now, we will add a mock run script or trigger celery task here.
    from app.tasks.research_tasks import run_research_pipeline_task
    # We trigger the task in the background (asynchronous Celery invocation)
    run_research_pipeline_task.delay(str(project.id))
    
    return project

@router.websocket("/{id}/logs/stream")
async def websocket_logs_stream(websocket: WebSocket, id: uuid.UUID):
    """
    WebSocket channel for streaming project pipeline logs in real time.
    """
    await websocket.accept()
    last_checked = datetime.utcnow()
    
    try:
        # 1. Fetch and send all history logs
        async with async_session_maker() as db:
            result = await db.execute(
                select(AgentLog)
                .where(AgentLog.project_id == id)
                .order_by(AgentLog.timestamp.asc())
            )
            logs = result.scalars().all()
            for log in logs:
                await websocket.send_json({
                    "timestamp": log.timestamp.isoformat(),
                    "agent_name": log.agent_name,
                    "step_name": log.step_name,
                    "log_level": log.log_level,
                    "message": log.message
                })
                
        # 2. Poll the database for new logs
        while True:
            await asyncio.sleep(0.5)
            async with async_session_maker() as db:
                result = await db.execute(
                    select(AgentLog)
                    .where(AgentLog.project_id == id, AgentLog.timestamp > last_checked)
                    .order_by(AgentLog.timestamp.asc())
                )
                new_logs = result.scalars().all()
                if new_logs:
                    for log in new_logs:
                        await websocket.send_json({
                            "timestamp": log.timestamp.isoformat(),
                            "agent_name": log.agent_name,
                            "step_name": log.step_name,
                            "log_level": log.log_level,
                            "message": log.message
                        })
                    last_checked = new_logs[-1].timestamp
                    
    except WebSocketDisconnect:
        pass

