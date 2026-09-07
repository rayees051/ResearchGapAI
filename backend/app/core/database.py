from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, text
from app.core.config import settings
from app.models import User, Project, Paper, PaperSection, Citation, ResearchGap, AgentLog, QueryCache

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """
    Initializes database schemas.
    """
    async with engine.begin() as conn:

        # Skip pgvector initialization for now
        pass

        await conn.run_sync(SQLModel.metadata.create_all)
        
        # Add columns for Adaptive Ranking Engine if they do not exist
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS novelty FLOAT;"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS relevance FLOAT;"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS feasibility FLOAT;"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS impact FLOAT;"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS final_score FLOAT;"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS " + '"rank" INTEGER;'))
        
        # Add columns for AI Source tracking
        await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS ai_source VARCHAR(50) DEFAULT 'gemini';"))
        await conn.execute(text("ALTER TABLE research_gaps ADD COLUMN IF NOT EXISTS ai_source VARCHAR(50) DEFAULT 'gemini';"))

async def get_session() -> AsyncSession:
    """
    FastAPI Dependency to get database session.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
