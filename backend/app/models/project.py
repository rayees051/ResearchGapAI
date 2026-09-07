from datetime import datetime
from typing import List, Optional
import uuid
from sqlmodel import SQLModel, Field, Relationship

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="idle")  # idle, running, completed, failed
    user_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    synthesis_report: Optional[str] = Field(default=None)
    ai_source: str = Field(default="gemini")  # gemini, fallback
    
    # Relationships with cascade delete
    user: "User" = Relationship(back_populates="projects")
    papers: List["Paper"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    gaps: List["ResearchGap"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    logs: List["AgentLog"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
