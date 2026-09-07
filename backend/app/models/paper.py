from datetime import datetime
from typing import List, Optional
import uuid
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from sqlalchemy import text

class Paper(SQLModel, table=True):
    __tablename__ = "papers"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id")
    title: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    storage_path: Optional[str] = None
    processed_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project: "Project" = Relationship(back_populates="papers")
    sections: List["PaperSection"] = Relationship(
        back_populates="paper",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class PaperSection(SQLModel, table=True):
    __tablename__ = "paper_sections"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    paper_id: uuid.UUID = Field(foreign_key="papers.id")
    section_title: Optional[str] = None
    content: str
    
    # Vector embedding using pgvector (1536 dimensions for standard OpenAI embeddings)
    embedding: Optional[List[float]] = Field(
    default=None,
    sa_column=Column(JSON)
)
    
    # Relationships
    paper: Paper = Relationship(back_populates="sections")

class Citation(SQLModel, table=True):
    __tablename__ = "citations"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    source_paper_id: uuid.UUID = Field(foreign_key="papers.id")
    target_paper_id: uuid.UUID = Field(foreign_key="papers.id")

class QueryCache(SQLModel, table=True):
    __tablename__ = "query_caches"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    query: str = Field(index=True, unique=True)
    results: List[dict] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
