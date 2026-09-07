from typing import List, Dict, Any, TypedDict, Annotated
import operator

class ResearchState(TypedDict):
    """
    State representing the context passed between nodes in the Multi-Agent LangGraph.
    """
    project_id: str
    project_title: str
    project_description: str
    query: str
    iteration: int
    max_iterations: int
    
    # Reducers can accumulate list state rather than overwriting
    papers_metadata: Annotated[List[Dict[str, Any]], operator.add]
    critiques: Annotated[List[Dict[str, Any]], operator.add]
    gaps: List[Dict[str, Any]]
    
    synthesis_report: str
    logs: Annotated[List[Dict[str, Any]], operator.add]
