from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB

class ResearchGap(SQLModel, table=True):
    __tablename__ = "research_gaps"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id")
    title: str
    description: str
    category: str = Field(default="methodological")  # methodological, empirical, population, theoretical
    severity: str = Field(default="medium")         # high, medium, low
    
    # Store dynamic structure of future directions, citation keys, and sub-items
    suggested_directions: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )
    
    novelty: Optional[float] = Field(default=None)
    relevance: Optional[float] = Field(default=None)
    feasibility: Optional[float] = Field(default=None)
    impact: Optional[float] = Field(default=None)
    final_score: Optional[float] = Field(default=None)
    rank: Optional[int] = Field(default=None)
    
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    ai_source: str = Field(default="gemini")  # gemini, fallback
    
    # Relationships
    project: "Project" = Relationship(back_populates="gaps")
