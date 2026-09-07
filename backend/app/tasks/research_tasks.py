from app.tasks.celery_app import celery_app
from app.agents.graph import research_graph
from app.core.database import async_session_maker
from app.models.project import Project
from app.agents.tools.logger import log_agent_step
import asyncio
from sqlmodel import select
import uuid

def run_async(coro):
    """
    Runs an asynchronous coroutine inside a synchronous Celery task worker.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task(name="app.tasks.run_research_pipeline_task")
def run_research_pipeline_task(project_id_str: str):
    """
    Celery task that executes the multi-agent LangGraph workflow.
    """
    return run_async(async_run_pipeline(project_id_str))

async def async_run_pipeline(project_id_str: str):
    project_uuid = uuid.UUID(project_id_str)
    
    # Load project details to get seed query
    async with async_session_maker() as db:
        project = await db.get(Project, project_uuid)
        if not project:
            print(f"Project {project_id_str} not found in database. Aborting pipeline.")
            return
        # Use description as search seed if present, otherwise fall back to title
        query = project.description if project.description else project.title
        
    await log_agent_step(
        project_id_str,
        "Supervisor",
        "pipeline_start",
        "INFO",
        f"Starting asynchronous research discovery pipeline for project '{project.title}'"
    )
    
    # Initial state
    initial_state = {
        "project_id": project_id_str,
        "project_title": project.title,
        "project_description": project.description or "",
        "query": "",
        "iteration": 1,
        "max_iterations": 3,
        "papers_metadata": [],
        "critiques": [],
        "gaps": [],
        "synthesis_report": "",
        "logs": []
    }
    
    try:
        # Invoke LangGraph pipeline
        result = await research_graph.ainvoke(initial_state)
        
        await log_agent_step(
            project_id_str,
            "Supervisor",
            "pipeline_success",
            "INFO",
            f"Successfully executed research discovery pipeline for project '{project.title}'."
        )
        
    except Exception as e:
        await log_agent_step(
            project_id_str,
            "Supervisor",
            "pipeline_failure",
            "ERROR",
            f"Fatal error during pipeline execution: {str(e)}"
        )
        # Update project status to failed
        async with async_session_maker() as db:
            proj = await db.get(Project, project_uuid)
            if proj:
                proj.status = "failed"
                db.add(proj)
                await db.commit()
                print(f"Set project {project_id_str} status to failed.")
