from app.agents.state import ResearchState
from app.agents.tools.logger import log_agent_step
from app.services.scholar_api import search_external_papers
from app.models.paper import Paper
from app.core.database import async_session_maker
from sqlmodel import select
import uuid

async def retrieval_node(state: ResearchState) -> dict:
    """
    Search and Retrieval Agent node. Loads local papers or fetches from arXiv/Semantic Scholar.
    """
    project_id = state["project_id"]
    query = state["query"]
    
    await log_agent_step(
        project_id, 
        "RetrievalAgent", 
        "search_and_fetch", 
        "INFO", 
        f"Retrieval Agent triggered. Initiating research search for seed query: '{query}'"
    )
    
    # Check if we already have papers in the database
    async with async_session_maker() as db:
        result = await db.execute(select(Paper).where(Paper.project_id == uuid.UUID(project_id)))
        db_papers = result.scalars().all()
        
    papers_found = []
    
    if db_papers:
        await log_agent_step(
            project_id, 
            "RetrievalAgent", 
            "database_load", 
            "INFO", 
            f"Loaded {len(db_papers)} user-managed papers from database."
        )
        for p in db_papers:
            papers_found.append({
                "id": str(p.id),
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "doi": p.doi,
                "pdf_url": p.pdf_url
            })
    else:
        # Fetch from arXiv/Semantic Scholar
        await log_agent_step(
            project_id, 
            "RetrievalAgent", 
            "api_fetch", 
            "INFO", 
            f"No local papers found. Querying external academic APIs..."
        )
        api_results = await search_external_papers(query, limit=5, project_id=project_id)
        
        # Save them in the database for future runs
        async with async_session_maker() as db:
            for item in api_results:
                paper = Paper(
                    project_id=uuid.UUID(project_id),
                    title=item["title"],
                    authors=", ".join(item["authors"]) if isinstance(item["authors"], list) else item["authors"],
                    journal=item["journal"],
                    year=item["year"],
                    doi=item["doi"],
                    pdf_url=item["pdf_url"]
                )
                db.add(paper)
                
            await db.commit()
            
            # Re-fetch with IDs
            result = await db.execute(select(Paper).where(Paper.project_id == uuid.UUID(project_id)))
            db_papers = result.scalars().all()
            for p in db_papers:
                papers_found.append({
                    "id": str(p.id),
                    "title": p.title,
                    "authors": p.authors,
                    "journal": p.journal,
                    "year": p.year,
                    "doi": p.doi,
                    "pdf_url": p.pdf_url
                })
            
        await log_agent_step(
            project_id, 
            "RetrievalAgent", 
            "import_complete", 
            "INFO", 
            f"Successfully imported {len(papers_found)} seed papers."
        )
        
    s2_papers_count = len([p for p in papers_found if p.get("journal") != "arXiv"]) if 'api_results' in locals() else 0
    inserted_count = len(api_results) if 'api_results' in locals() else 0
    passed_count = len(papers_found)
    
    await log_agent_step(
        project_id,
        "RetrievalAgent",
        "retrieval_run_summary",
        "INFO",
        f"Retrieval Run Summary:\n"
        f" - Semantic Scholar papers returned: {s2_papers_count}\n"
        f" - Papers inserted into PostgreSQL: {inserted_count}\n"
        f" - Papers passed to Critique Agent: {passed_count}"
    )
        
    return {
        "papers_metadata": papers_found,
        "logs": [{"agent": "RetrievalAgent", "message": f"Ingested {len(papers_found)} papers."}]
    }
