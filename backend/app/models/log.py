from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field, Relationship

class AgentLog(SQLModel, table=True):
    __tablename__ = "agent_logs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id")
    agent_name: str
    step_name: str
    log_level: str = Field(default="INFO")  # INFO, WARNING, ERROR
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    project: "Project" = Relationship(back_populates="logs")
