from app.agents.state import ResearchState
from app.agents.tools.logger import log_agent_step
from app.agents.tools.llm import call_llm, extract_json_block
from app.models.gap import ResearchGap
from app.core.database import async_session_maker
from sqlmodel import select
import uuid
import json

async def ranking_node(state: ResearchState) -> dict:
    """
    Adaptive Ranking Engine Agent. Evaluates identified research gaps across
    four dimensions (novelty, relevance, feasibility, impact), computes a
    weighted final score, ranks them, and updates the database.
    """
    project_id = state["project_id"]
    query = state["query"]
    papers = state["papers_metadata"][:3]
    gaps = state["gaps"]
    
    await log_agent_step(
        project_id,
        "RankingEngine",
        "ranking_start",
        "INFO",
        f"Adaptive Ranking Engine active. Evaluating {len(gaps)} research gaps..."
    )
    
    if not gaps:
        await log_agent_step(
            project_id,
            "RankingEngine",
            "ranking_empty",
            "WARNING",
            "No research gaps found to rank. Skipping ranking step."
        )
        return {"gaps": []}

    # Format the papers metadata to pass as context
    papers_summary = "\n".join([f"- **{p['title']}** ({p.get('year') or 'N/A'}): {p.get('authors') or 'Unknown'}" for p in papers])
    
    # Format the input gaps context for the LLM
    gaps_context = json.dumps([
        {
            "title": g["title"],
            "description": g["description"],
            "category": g.get("category", "methodological"),
            "suggested_directions": g.get("suggested_directions", [])
        } for g in gaps
    ], indent=2)

    system_prompt = (
        "You are an academic research ranker and evaluator. Evaluate the provided list of research gaps based on the project query and the retrieved paper metadata. "
        "For each research gap, you must assign four scores on a scale from 0.0 to 10.0 (decimal values are allowed):\n"
        "1. Novelty: How unique is this gap compared to existing paper findings and general literature?\n"
        "2. Relevance: How closely aligned is this gap to the project's seed research query and retrieved papers?\n"
        "3. Feasibility: How practical and implementable is it to address this gap (complexity of directions)?\n"
        "4. Research Impact: What is the expected contribution and value of solving this gap to the field?\n"
        "Return a strict JSON list of objects, one for each gap, matching the input list size and preserving the exact titles. "
        "The output structure MUST match this schema:\n"
        "[\n"
        "  {\n"
        "    \"title\": \"string\",\n"
        "    \"novelty\": float,\n"
        "    \"relevance\": float,\n"
        "    \"feasibility\": float,\n"
        "    \"impact\": float\n"
        "  }\n"
        "]"
    )

    user_prompt = (
        f"Project Seed Query: {query}\n\n"
        f"Retrieved Papers Context:\n{papers_summary}\n\n"
        f"Identified Research Gaps to Evaluate:\n{gaps_context}"
    )

    # Generate dynamic deterministic mock scores for fallback mapping
    default_scores = {
        "Lack of Multi-Agent Collaboration Benchmarking in Low-Resource Regimes": {
            "novelty": 8.5,
            "relevance": 9.0,
            "feasibility": 7.0,
            "impact": 8.0
        },
        "Omission of Real-time User Feedback Channels in Auto-Criticism Agents": {
            "novelty": 7.0,
            "relevance": 8.0,
            "feasibility": 8.5,
            "impact": 7.5
        },
        "Evaluation Biases in Synthesized Literature Reviews": {
            "novelty": 9.0,
            "relevance": 7.5,
            "feasibility": 6.0,
            "impact": 8.5
        }
    }

    mock_list = []
    for g in gaps:
        title = g["title"]
        if title in default_scores:
            scores = default_scores[title]
        else:
            # Deterministic pseudo-random generation based on title string hash to ensure stability
            char_sum = sum(ord(c) for c in title)
            scores = {
                "novelty": round(6.0 + (char_sum % 35) / 10.0, 1),
                "relevance": round(6.0 + ((char_sum * 3) % 35) / 10.0, 1),
                "feasibility": round(5.5 + ((char_sum * 7) % 40) / 10.0, 1),
                "impact": round(6.5 + ((char_sum * 11) % 30) / 10.0, 1)
            }
        mock_list.append({
            "title": title,
            **scores
        })

    mock_text = json.dumps(mock_list)
    import time
    start_time = time.time()
    llm_res, ai_source = await call_llm(system_prompt, user_prompt, mock_fallback=mock_text, timeout_ms=30000)
    elapsed_time = time.time() - start_time
    
    await log_agent_step(
        project_id,
        "RankingEngine",
        "gemini_timing",
        "INFO",
        f"Gemini LLM invocation completed in {elapsed_time:.2f} seconds."
    )

    # Parse and extract evaluated scores
    try:
        extracted_res = extract_json_block(llm_res)
        evaluated = json.loads(extracted_res.strip())
        
        await log_agent_step(
            project_id,
            "RankingEngine",
            "json_extraction_success",
            "INFO",
            "Successfully extracted and parsed JSON evaluation scores from Gemini response."
        )
        
        # Turn into a lookup map by title
        eval_map = {item["title"]: item for item in evaluated if "title" in item}
        if ai_source == "fallback":
            await log_agent_step(
                project_id,
                "RankingEngine",
                "fallback_activation",
                "WARNING",
                "Activating fallback scoring evaluation due to Gemini API unavailable."
            )
    except Exception as e:
        eval_map = {item["title"]: item for item in mock_list}
        ai_source = "fallback"
        await log_agent_step(
            project_id,
            "RankingEngine",
            "json_extraction_failure",
            "WARNING",
            f"Failed to extract/parse JSON evaluation scores from Gemini response: {str(e)}."
        )
        await log_agent_step(
            project_id,
            "RankingEngine",
            "fallback_activation",
            "WARNING",
            f"Activating fallback scoring evaluation due to JSON parsing error: {str(e)}."
        )

    # Merge scores, compute Final Score
    ranked_gaps = []
    for g in gaps:
        title = g["title"]
        eval_data = eval_map.get(title) or eval_map.get(title[:40])
        
        # If not found in evaluated map, fall back to mock data
        if not eval_data:
            char_sum = sum(ord(c) for c in title)
            eval_data = {
                "novelty": round(6.0 + (char_sum % 35) / 10.0, 1),
                "relevance": round(6.0 + ((char_sum * 3) % 35) / 10.0, 1),
                "feasibility": round(5.5 + ((char_sum * 7) % 40) / 10.0, 1),
                "impact": round(6.5 + ((char_sum * 11) % 30) / 10.0, 1)
            }
            
        novelty = float(eval_data.get("novelty", 7.0))
        relevance = float(eval_data.get("relevance", 7.0))
        feasibility = float(eval_data.get("feasibility", 7.0))
        impact = float(eval_data.get("impact", 7.0))
        
        # Formula: 0.4*Novelty + 0.3*Relevance + 0.2*Feasibility + 0.1*Impact
        final_score = 0.4 * novelty + 0.3 * relevance + 0.2 * feasibility + 0.1 * impact
        final_score = round(final_score, 2)
        
        # Create gap dictionary with scoring keys
        ranked_gap = {
            **g,
            "novelty": novelty,
            "relevance": relevance,
            "feasibility": feasibility,
            "impact": impact,
            "final_score": final_score,
            "ai_source": "fallback" if (g.get("ai_source") == "fallback" or ai_source == "fallback") else "gemini"
        }
        ranked_gaps.append(ranked_gap)

    # Sort gaps descending by final_score
    ranked_gaps.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Assign ranks
    for idx, rg in enumerate(ranked_gaps):
        rg["rank"] = idx + 1

    # Update gap entries in the database
    async with async_session_maker() as db:
        for rg in ranked_gaps:
            title = rg["title"]
            res = await db.execute(
                select(ResearchGap).where(
                    ResearchGap.project_id == uuid.UUID(project_id),
                    ResearchGap.title == title
                )
            )
            db_gap = res.scalars().first()
            if db_gap:
                db_gap.novelty = rg["novelty"]
                db_gap.relevance = rg["relevance"]
                db_gap.feasibility = rg["feasibility"]
                db_gap.impact = rg["impact"]
                db_gap.final_score = rg["final_score"]
                db_gap.rank = rg["rank"]
                db_gap.ai_source = rg["ai_source"]
                db.add(db_gap)
        await db.commit()

    await log_agent_step(
        project_id,
        "RankingEngine",
        "ranking_complete",
        "INFO",
        f"Successfully ranked {len(ranked_gaps)} research gaps. Highest final score: {ranked_gaps[0]['final_score'] if ranked_gaps else 'N/A'}"
    )

    return {
        "gaps": ranked_gaps,
        "logs": [{"agent": "RankingEngine", "message": f"Evaluated and ranked {len(ranked_gaps)} gaps."}]
    }
