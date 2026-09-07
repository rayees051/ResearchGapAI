import fitz  # PyMuPDF
import uuid
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.paper import PaperSection, Paper
from app.core.config import settings
from google import genai
from google.genai import types
from typing import List

def get_gemini_client():
    """
    Returns the initialized Gemini client if the GEMINI_API_KEY is configured.
    """
    if settings.GEMINI_API_KEY:
        return genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=15000,  # 15 seconds timeout
                retry_options=types.HttpRetryOptions(
                    attempts=2,  # 1 initial + 1 retry
                    initial_delay=2.0,
                    max_delay=10.0,
                    http_status_codes=[504]  # Retry specifically on 504 Gateway Timeout
                )
            )
        )
    return None

async def generate_embeddings(texts: List[str], project_id: str = None) -> List[List[float]]:
    """
    Generates text embeddings using Google Gemini API (text-embedding-004).
    Gracefully falls back to a 768-dimensional mock vector if API key is not configured.
    """
    client = get_gemini_client()
    if not client:
        if project_id:
            from app.agents.tools.logger import log_agent_step
            await log_agent_step(
                project_id,
                "PDFParser",
                "fallback_activation",
                "WARNING",
                "Activating fallback zero-vector embeddings (768-dim) due to missing GEMINI_API_KEY."
            )
        # Return 768-dim dummy vectors
        return [[0.0] * 768 for _ in texts]
        
    try:
        res = await client.aio.models.embed_content(
            model="text-embedding-004",
            contents=texts
        )
        return [embedding.values for embedding in res.embeddings]
    except Exception as e:
        import traceback
        print(f"Exception during embedding generation: {str(e)}")
        traceback.print_exc()
        if project_id:
            from app.agents.tools.logger import log_agent_step
            await log_agent_step(
                project_id,
                "PDFParser",
                "fallback_activation",
                "WARNING",
                f"Activating fallback zero-vector embeddings (768-dim) due to Gemini embedding API error: {str(e)}."
            )
            
    return [[0.0] * 768 for _ in texts]

async def process_pdf_document(paper_id: uuid.UUID, file_path: str, db: AsyncSession):
    """
    Segments PDF documents into sections using structural parsing heuristics,
    creates vector embeddings for each block, and saves them to PostgreSQL.
    """
    # Try to fetch project_id to log fallback activation if necessary
    project_id = None
    try:
        paper = await db.get(Paper, paper_id)
        if paper:
            project_id = str(paper.project_id)
    except Exception as e:
        print(f"Could not load paper project metadata: {e}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"Failed to open PDF file {file_path}: {e}")
        return

    sections = []
    current_section = "Abstract / Introduction"
    current_content = []
    
    # Parse text page by page
    for page in doc:
        text_content = page.get_text("text")
        lines = text_content.split("\n")
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            # Heuristic for section header identification:
            # Short lines that are either fully uppercase or start with Roman numerals / digit indices
            is_header = len(line_str) < 80 and (
                line_str.isupper() or 
                line_str.startswith((
                    "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ",
                    "1 ", "2 ", "3 ", "4 ", "5 ", "6 ", "7 ", "8 ",
                    "I. ", "II. ", "III. ", "IV. ", "V. ", "VI. ",
                    "Abstract", "Introduction", "Methodology", "Experiments", 
                    "Results", "Conclusion", "References"
                ))
            )
            
            if is_header:
                # Save previous section if it has gathered paragraphs
                if current_content:
                    sections.append({
                        "title": current_section,
                        "content": "\n".join(current_content)
                    })
                    current_content = []
                current_section = line_str
            else:
                current_content.append(line_str)
                
    # Add final remaining section
    if current_content:
        sections.append({
            "title": current_section,
            "content": "\n".join(current_content)
        })
        
    # Commit sections and their embeddings to DB
    if sections:
        # Sub-chunk sections if they are excessively large
        processed_contents = [sec["content"][:3000] for sec in sections]
        embeddings = await generate_embeddings(processed_contents, project_id=project_id)
        
        for i, sec in enumerate(sections):
            db_sec = PaperSection(
                paper_id=paper_id,
                section_title=sec["title"],
                content=sec["content"],
                embedding=embeddings[i]
            )
            db.add(db_sec)
            
        await db.commit()
        print(f"Successfully processed PDF: {len(sections)} sections inserted.")
