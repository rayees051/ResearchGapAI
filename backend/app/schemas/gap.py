from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel

class ResearchGapBase(BaseModel):
    title: str
    description: str
    category: str = "methodological"
    severity: str = "medium"
    suggested_directions: List[Dict[str, Any]] = []
    novelty: Optional[float] = None
    relevance: Optional[float] = None
    feasibility: Optional[float] = None
    impact: Optional[float] = None
    final_score: Optional[float] = None
    rank: Optional[int] = None
    ai_source: str = "gemini"

class ResearchGapCreate(ResearchGapBase):
    project_id: uuid.UUID

class ResearchGapRead(ResearchGapBase):
    id: uuid.UUID
    project_id: uuid.UUID
    identified_at: datetime

    class Config:
        from_attributes = True
