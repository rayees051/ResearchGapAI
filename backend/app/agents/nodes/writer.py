from app.agents.state import ResearchState
from app.agents.tools.logger import log_agent_step
from app.agents.tools.llm import call_llm
from app.models.project import Project
from app.core.database import async_session_maker
import uuid
import json

async def writer_node(state: ResearchState) -> dict:
    """
    Synthesis Writer Agent. Compiles paper summaries and identified gaps 
    into a comprehensive, structured literature review markdown report.
    """
    project_id = state["project_id"]
    papers = state["papers_metadata"][:3]
    gaps = state["gaps"]
    
    await log_agent_step(
        project_id, 
        "SynthesisWriterAgent", 
        "synthesis_start", 
        "INFO", 
        "Synthesis Writer active. Structuring final literature synthesis report..."
    )
    
    # Formulate contextual information
    papers_summary = "\n".join([f"- **{p['title']}** ({p.get('year') or 'N/A'}) - {p.get('authors') or 'Unknown'}" for p in papers])
    gaps_summary = "\n".join([
        f"### Gap: {g['title']} (Rank: {g.get('rank', 'N/A')}, Score: {g.get('final_score', 'N/A')}/10)\n"
        f"- **Novelty**: {g.get('novelty', 'N/A')}/10, **Relevance**: {g.get('relevance', 'N/A')}/10, "
        f"**Feasibility**: {g.get('feasibility', 'N/A')}/10, **Research Impact**: {g.get('impact', 'N/A')}/10\n"
        f"- **Severity**: {g.get('severity', 'medium')}\n"
        f"- **Description**: {g.get('description', '')}"
        for g in gaps
    ])
    
    system_prompt = (
        "You are an academic copywriter and researcher. Compile the provided lists of papers and prioritized research gaps "
        "into a structured academic literature review report. "
        "Include the following sections:\n"
        "1. # Executive Summary\n"
        "2. # Survey of Existing Literature (synthesizing the papers listed)\n"
        "3. # Identified Research Gaps (explaining the severity, scores, and context of the gaps in order of their calculated priority rank)\n"
        "4. # Proposed Research Directions (actionable next steps based on the highest ranked gaps)\n"
        "Output ONLY valid markdown text."
    )
    
    user_prompt = (
        f"Generate report using this data:\n\n"
        f"## Input Papers:\n{papers_summary}\n\n"
        f"## Input Gaps (ranked by priority):\n{gaps_summary}"
    )
    
    # Sort gaps by rank if available, otherwise preserve order
    sorted_gaps = sorted(gaps, key=lambda x: x.get("rank") if x.get("rank") is not None else 99)
    fallback_directions = []
    for idx, gap in enumerate(sorted_gaps[:3]):
        gap_title = gap.get("title", "Unnamed Gap")
        gap_desc = gap.get("description", "")
        # Get first sentence of description
        desc_sentence = gap_desc.split(".")[0] if gap_desc else "Investigate issues related to this research void"
        desc_sentence = desc_sentence.strip()
        if desc_sentence and not desc_sentence.endswith("."):
            desc_sentence += "."
        fallback_directions.append(
            f"{idx + 1}. **{gap_title} Mitigation**: {desc_sentence}"
        )
        
    directions_text = "\n".join(fallback_directions) if fallback_directions else (
        "1. **Literature Expansion**: Gather more papers to identify potential research gaps.\n"
        "2. **Baseline Evaluation**: Establish reference performance metrics for the seed topic."
    )

    mock_markdown = (
        f"# Research Synthesis Report\n\n"
        f"## 1. Executive Summary\n"
        f"This report presents a synthesized literature analysis exploring the research topic. "
        f"By reviewing {len(papers)} seed documents, the framework identified several key operational deficiencies. "
        f"Specifically, {len(gaps)} core research gaps were outlined, prioritized, and scored by our Adaptive Ranking Engine, ranging from methodological voids to parameter sensitivity omission.\n\n"
        f"## 2. Survey of Existing Literature\n"
        f"We investigated current academic works, including:\n"
        f"{papers_summary}\n\n"
        f"Existing literature focuses heavily on standard evaluation configurations but largely assumes unlimited token allocations, "
        f"failing to evaluate cooperative system dynamics under strict hardware constraints.\n\n"
        f"## 3. Identified Research Gaps\n"
        f"{gaps_summary}\n\n"
        f"## 4. Proposed Research Directions\n"
        f"To address these challenges, we suggest the following development steps based on the identified gaps:\n"
        f"{directions_text}"
    )
    
    llm_res, ai_source = await call_llm(system_prompt, user_prompt, mock_fallback=mock_markdown)
    
    # Check if either this node or any previous gaps were generated in fallback mode
    any_fallback = (ai_source == "fallback") or any(g.get("ai_source") == "fallback" for g in gaps)
    
    if any_fallback:
        # Prepend a warning banner to the synthesis report
        banner = (
            "> [!WARNING]\n"
            "> **FALLBACK GENERATION ACTIVE**\n"
            "> This literature review was generated in Fallback Mode due to Google Gemini API key or quota failure. "
            "The content below contains template-based academic structures rather than live AI synthesis.\n\n"
        )
        llm_res = banner + llm_res
        
        await log_agent_step(
            project_id, 
            "SynthesisWriterAgent", 
            "fallback_activation", 
            "WARNING", 
            "Activating fallback markdown synthesis report due to Gemini API unavailable."
        )
        
    # Save the markdown report directly into the Project model in PostgreSQL
    async with async_session_maker() as db:
        project_uuid = uuid.UUID(project_id)
        project = await db.get(Project, project_uuid)
        if project:
            project.synthesis_report = llm_res
            project.ai_source = "fallback" if any_fallback else "gemini"
            project.status = "completed"  # Pipeline run finishes here
            db.add(project)
            await db.commit()
            
    await log_agent_step(
        project_id, 
        "SynthesisWriterAgent", 
        "synthesis_complete", 
        "INFO", 
        "Successfully finalized literature review and marked research pipeline as COMPLETED."
    )
    
    return {
        "synthesis_report": llm_res,
        "logs": [{"agent": "SynthesisWriterAgent", "message": "Compiled literature review."}]
    }
