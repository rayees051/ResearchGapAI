import uuid
from datetime import datetime
from app.core.database import async_session_maker
from app.models.log import AgentLog

async def log_agent_step(project_id: str, agent_name: str, step_name: str, log_level: str, message: str):
    """
    Saves an agent execution step to the database for real-time dashboard progress tracking.
    """
    try:
        db_log = AgentLog(
            project_id=uuid.UUID(project_id),
            agent_name=agent_name,
            step_name=step_name,
            log_level=log_level,
            message=message,
            timestamp=datetime.utcnow()
        )
        async with async_session_maker() as db:
            db.add(db_log)
            await db.commit()
    except Exception as e:
        print(f"Error saving agent step log: {e}")
        
    try:
        print(f"[{agent_name}][{step_name}] {log_level}: {message}")
    except UnicodeEncodeError:
        try:
            import sys
            encoding = sys.stdout.encoding or 'utf-8'
            print(f"[{agent_name}][{step_name}] {log_level}: {message.encode(encoding, errors='replace').decode(encoding)}")
        except Exception:
            pass
