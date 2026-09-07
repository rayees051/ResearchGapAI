from app.agents.state import ResearchState
from app.agents.tools.logger import log_agent_step
from app.agents.tools.llm import call_llm
from app.models.paper import Paper, PaperSection
from app.core.database import async_session_maker
from sqlmodel import select
import uuid
import json

async def critique_node(state: ResearchState) -> dict:
    """
    Methodology Critique Agent. Analyzes experimental configurations,
    limitations, and data validation scopes of each parsed paper.
    """
    project_id = state["project_id"]
    papers = state["papers_metadata"][:3]
    
    await log_agent_step(
        project_id, 
        "CritiqueAgent", 
        "critique_start", 
        "INFO", 
        f"Critique Agent active. Reviewing methodologies of {len(papers)} papers."
    )
    
    critiques = []
    
    async with async_session_maker() as db:
        for paper in papers:
            # Fetch parsed sections to critique actual content if available
            paper_uuid = uuid.UUID(paper["id"])
            sec_res = await db.execute(
                select(PaperSection).where(PaperSection.paper_id == paper_uuid)
            )
            sections = sec_res.scalars().all()
            
            # Formulate text context
            if sections:
                context = "\n\n".join([f"## Section: {s.section_title}\n{s.content[:1000]}" for s in sections[:2]])
            else:
                context = f"Title: {paper['title']}\nAuthors: {paper['authors'] or 'Unknown'}\nJournal: {paper['journal'] or 'N/A'}"
                
            await log_agent_step(
                project_id, 
                "CritiqueAgent", 
                "paper_analysis", 
                "INFO", 
                f"Analyzing study parameters of: '{paper['title'][:40]}...'"
            )
            
            system_prompt = (
                "You are an academic peer reviewer and methodology expert. Critique the research design of the provided paper context. "
                "Highlight the core assumptions, sample limitations, dataset details, verification metrics, and implicit biases. "
                "Return a strict JSON output matching this structure:\n"
                '{"assumptions": ["string"], "limitations": ["string"], "evaluation_flaws": ["string"], "methodology_type": "string"}'
            )
            
            user_prompt = f"Critique the following paper information:\n{context}"
            
            # Structured mock critique to fallback on
            mock_json = {
                "assumptions": [
                    "Assumes stationary distribution of scientific variables over time.",
                    "Relies on the availability of highly clean API inputs."
                ],
                "limitations": [
                    f"Small empirical evaluation footprint limited to synthetic benchmarks in '{paper['title'][:30]}'.",
                    "Evaluation does not measure real-world user interface friction."
                ],
                "evaluation_flaws": [
                    "Lacks comparison with modern hyperparameter optimization baselines.",
                    "Fails to specify statistical significance thresholds."
                ],
                "methodology_type": "Empirical / Quantitative Evaluation"
            }
            mock_text = json.dumps(mock_json)
            
            llm_res, ai_source = await call_llm(system_prompt, user_prompt, mock_fallback=mock_text)
            
            try:
                # Strip out possible markdown wrappers if LLM returned them
                cleaned_res = llm_res.strip()
                if cleaned_res.startswith("```json"):
                    cleaned_res = cleaned_res[7:]
                if cleaned_res.endswith("```"):
                    cleaned_res = cleaned_res[:-3]
                parsed_critique = json.loads(cleaned_res.strip())
                if ai_source == "fallback":
                    await log_agent_step(
                        project_id,
                        "CritiqueAgent",
                        "fallback_activation",
                        "WARNING",
                        f"Activating fallback critique template for paper '{paper['title']}' due to Gemini API unavailable."
                    )
            except Exception as e:
                parsed_critique = mock_json
                ai_source = "fallback"
                await log_agent_step(
                    project_id,
                    "CritiqueAgent",
                    "fallback_activation",
                    "WARNING",
                    f"Activating fallback critique template for paper '{paper['title']}' due to JSON parsing error: {str(e)}."
                )
                
            critiques.append({
                "paper_id": paper["id"],
                "title": paper["title"],
                "critique": parsed_critique,
                "ai_source": ai_source
            })
            
    await log_agent_step(
        project_id, 
        "CritiqueAgent", 
        "critique_finish", 
        "INFO", 
        f"Completed critiques for all {len(papers)} scientific documents."
    )
    
    return {
        "critiques": critiques,
        "logs": [{"agent": "CritiqueAgent", "message": f"Critiqued {len(papers)} papers."}]
    }
