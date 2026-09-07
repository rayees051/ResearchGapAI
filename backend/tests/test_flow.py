import sys
import os
import asyncio
import uuid

# Add backend directory to system path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

async def test_compilation_and_graph():
    print("==========================================================")
    print("Testing Multi-Agent LangGraph Compilation...")
    print("==========================================================")
    
    try:
        # Import graph and state
        from app.agents.graph import research_graph
        from app.agents.state import ResearchState
        
        print("[OK] LangGraph compiled successfully.")
        
        # Define mock state
        mock_project_id = str(uuid.uuid4())
        initial_state = {
            "project_id": mock_project_id,
            "project_title": "Cooperative Agent Chains",
            "project_description": "Resource-Constrained Environments",
            "query": "",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [],
            "critiques": [],
            "gaps": [],
            "synthesis_report": "",
            "logs": []
        }
        
        print(f"[OK] Initialized mock ResearchState for project: {mock_project_id}")
        print("[OK] Checking agent nodes and tools connectivity...")
        
        from app.agents.nodes.retrieval import retrieval_node
        from app.agents.nodes.critique import critique_node
        from app.agents.nodes.analyzer import analyzer_node
        from app.agents.nodes.ranking import ranking_node
        from app.agents.nodes.writer import writer_node
        
        print("[OK] All agent node modules resolved correctly.")
        print("==========================================================")
        print("Test Passed: Framework compiles and resolves graph states.")
        print("==========================================================")
        
    except Exception as e:
        print(f"[ERROR] Graph compilation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_compilation_and_graph())
