from datetime import datetime
from typing import Optional, List
import uuid
from pydantic import BaseModel

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ProjectRead(ProjectBase):
    id: uuid.UUID
    status: str
    created_at: datetime
    synthesis_report: Optional[str] = None
    ai_source: str = "gemini"

    class Config:
        from_attributes = True
