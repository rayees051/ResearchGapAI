from datetime import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel

class PaperBase(BaseModel):
    title: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None

class PaperCreate(PaperBase):
    project_id: uuid.UUID

class PaperRead(PaperBase):
    id: uuid.UUID
    project_id: uuid.UUID
    storage_path: Optional[str] = None
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaperSectionRead(BaseModel):
    id: uuid.UUID
    paper_id: uuid.UUID
    section_title: Optional[str] = None
    content: str

    class Config:
        from_attributes = True
