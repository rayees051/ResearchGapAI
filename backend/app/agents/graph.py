from langgraph.graph import StateGraph, END
from app.agents.state import ResearchState
from app.agents.nodes.optimizer import query_optimization_node
from app.agents.nodes.retrieval import retrieval_node
from app.agents.nodes.critique import critique_node
from app.agents.nodes.analyzer import analyzer_node
from app.agents.nodes.ranking import ranking_node
from app.agents.nodes.writer import writer_node

def build_research_graph():
    """
    Assembles the multi-agent execution pipeline inside a LangGraph StateGraph.
    Execution Flow: Query Optimizer -> Retrieval -> Critique -> Gap Analysis -> Adaptive Ranking -> Synthesis Writer.
    """
    # Initialize the graph with State definition
    workflow = StateGraph(ResearchState)
    
    # Add operational agent nodes
    workflow.add_node("query_optimizer", query_optimization_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("critique", critique_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("ranking", ranking_node)
    workflow.add_node("writer", writer_node)
    
    # Define directional routing pathways
    workflow.set_entry_point("query_optimizer")
    
    workflow.add_edge("query_optimizer", "retrieval")
    workflow.add_edge("retrieval", "critique")
    workflow.add_edge("critique", "analyzer")
    workflow.add_edge("analyzer", "ranking")
    workflow.add_edge("ranking", "writer")
    workflow.add_edge("writer", END)
    
    # Compile the graph
    return workflow.compile()

# Single compiled instance ready for runner execution
research_graph = build_research_graph()
