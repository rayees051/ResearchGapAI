from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import os
import shutil

from app.core.database import get_session
from app.core.config import settings
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.paper import Paper
from app.schemas.paper import PaperRead, PaperCreate
from app.services.scholar_api import search_external_papers
from app.services.pdf_parser import process_pdf_document

router = APIRouter()

@router.get("/", response_model=List[PaperRead])
async def list_papers(
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
        select(Paper).where(Paper.project_id == project_id)
    )
    return result.scalars().all()

@router.post("/upload", response_model=PaperRead)
async def upload_paper(
    project_id: uuid.UUID = Query(...),
    file: UploadFile = File(...),
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
        
    # Save the file locally
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create the paper entry
    db_paper = Paper(
        title=file.filename.replace(".pdf", ""),
        project_id=project_id,
        storage_path=file_path,
        pdf_url=None
    )
    db.add(db_paper)
    await db.commit()
    await db.refresh(db_paper)
    
    # Process PDF asynchronously or synchronously
    # For simplicity and fast testing, let's run the parser in a background thread or synchronously
    try:
        await process_pdf_document(db_paper.id, file_path, db)
    except Exception as e:
        # Don't fail the upload, but log it
        print(f"Error parsing PDF: {e}")
        
    return db_paper

@router.post("/search", response_model=List[PaperRead])
async def search_and_import_papers(
    project_id: uuid.UUID = Query(...),
    query: str = Query(...),
    limit: int = Query(5),
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
        
    # Fetch papers from external APIs
    external_papers = await search_external_papers(query, limit, project_id=str(project_id))
    imported_papers = []
    
    for ep in external_papers:
        db_paper = Paper(
            title=ep.get("title", "Untitled"),
            project_id=project_id,
            authors=", ".join(ep.get("authors", [])),
            journal=ep.get("journal"),
            year=ep.get("year"),
            doi=ep.get("doi"),
            pdf_url=ep.get("pdf_url")
        )
        db.add(db_paper)
        imported_papers.append(db_paper)
        
    await db.commit()
    
    # Refresh all
    for paper in imported_papers:
        await db.refresh(paper)
        
    return imported_papers

@router.delete("/{id}", response_model=PaperRead)
async def delete_paper(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership of paper's project
    result = await db.execute(
        select(Paper).where(Paper.id == id)
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
        
    proj_res = await db.execute(
        select(Project).where(Project.id == paper.project_id, Project.user_id == current_user.id)
    )
    if not proj_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
        
    # Delete file if exists
    if paper.storage_path and os.path.exists(paper.storage_path):
        try:
            os.remove(paper.storage_path)
        except Exception:
            pass
            
    await db.delete(paper)
    await db.commit()
    return paper
