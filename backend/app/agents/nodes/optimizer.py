import re
from app.agents.state import ResearchState
from app.agents.tools.logger import log_agent_step
from app.agents.tools.llm import call_llm

def rule_based_keyword_extraction(title: str, description: str) -> str:
    """
    Fallback method: Clean input text, drop common stop words, and extract unique keywords.
    """
    combined = f"{title} {description}"
    # Clean text: replace punctuation and special characters with spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', ' ', combined.lower())
    words = cleaned.split()
    
    # Common academic/English stop words to filter out
    stop_words = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
        'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
        'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for', 'from',
        'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here',
        'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in',
        'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor',
        'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
        'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than', 'that', 'thats',
        'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these', 'they', 'theyd', 'theyll',
        'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasnt', 'we',
        'wed', 'well', 'were', 'werent', 'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while', 'who',
        'whos', 'whom', 'why', 'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve',
        'your', 'yours', 'yourself', 'yourselves',
        # academic noise words
        'project', 'determines', 'whether', 'using', 'used', 'use', 'detect', 'detects', 'images', 'image', 'secure',
        'paper', 'study', 'research', 'analysis', 'method', 'approach', 'system', 'framework', 'model', 'results',
        'based', 'proposed', 'novel'
    }
    
    unique_keywords = []
    seen = set()
    for w in words:
        w_clean = w.strip('-')
        if len(w_clean) > 1 and w_clean not in stop_words and w_clean not in seen:
            seen.add(w_clean)
            unique_keywords.append(w_clean)
            
    # Limit fallback query length to at most 18 keywords
    return " ".join(unique_keywords[:18])

async def query_optimization_node(state: ResearchState) -> dict:
    """
    Query Optimization Agent node.
    Converts raw Title and Description into an optimized academic search query (15-20 keywords).
    Uses Gemini when available, and falls back to rule-based keyword extraction if unavailable.
    """
    project_id = state["project_id"]
    title = state.get("project_title", "")
    description = state.get("project_description", "")
    
    await log_agent_step(
        project_id,
        "QueryOptimizerAgent",
        "optimization_start",
        "INFO",
        f"Query Optimizer Agent active. Optimizing search query for title: '{title}'"
    )
    
    # 1. Define LLM prompt for academic keyword extraction/expansion
    system_prompt = (
        "You are an expert academic research librarian and search optimizer. "
        "Your task is to convert a project title and description into an optimized academic search query. "
        "The search query must consist of 15 to 20 high-quality, concise academic keywords "
        "representing domain terms, methodologies, datasets, and application areas. "
        "Do NOT include any introduction, formatting, bullet points, numbering, or punctuation. "
        "Provide ONLY the space-separated list of keywords on a single line."
    )
    
    user_prompt = (
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        "Optimized space-separated academic keywords:"
    )
    
    # 2. Get rule-based fallback keywords
    fallback_query = rule_based_keyword_extraction(title, description)
    
    # 3. Call LLM with fallback
    llm_res, ai_source = await call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        mock_fallback=fallback_query
    )
    
    # 4. Clean and post-process output query (from LLM or fallback)
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', ' ', llm_res.lower())
    words = [w.strip('-') for w in cleaned.split() if len(w.strip('-')) > 1]
            
    # Limit query length to 15-20 keywords (cap at 20 keywords)
    optimized_query = " ".join(words[:20])
    
    # If the LLM returned empty or too few keywords, use rule-based fallback
    if len(optimized_query.split()) < 3:
        optimized_query = fallback_query
        ai_source = "fallback"
    
    # 5. Log details
    if ai_source == "fallback":
        log_message = (
            f"Activating rule-based fallback query optimization due to Gemini API unavailable.\n"
            f"original_title: {title}\n"
            f"original_description: {description}\n"
            f"optimized_query: {optimized_query}"
        )
        log_level = "WARNING"
    else:
        log_message = (
            f"Query Optimization completed.\n"
            f"original_title: {title}\n"
            f"original_description: {description}\n"
            f"optimized_query: {optimized_query}"
        )
        log_level = "INFO"
        
    await log_agent_step(
        project_id=project_id,
        agent_name="QueryOptimizerAgent",
        step_name="query_optimization",
        log_level=log_level,
        message=log_message
    )
    
    return {
        "query": optimized_query,
        "logs": [{"agent": "QueryOptimizerAgent", "message": f"Optimized query to: {optimized_query}"}]
    }
