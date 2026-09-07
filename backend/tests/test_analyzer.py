import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to system path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.agents.nodes.analyzer import analyzer_node, generate_dynamic_fallback_gaps
from app.models.user import User
from app.models.project import Project
from app.models.paper import Paper

class TestGapAnalyzer(unittest.TestCase):
    def setUp(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def test_dynamic_fallback_generation(self):
        # 1. Prepare inputs with custom titles/critiques
        papers = [
            {"title": "Decentralized Federated Agent Consensus Protocols"},
            {"title": "Robustness Limits of Autonomous LLM Chains"}
        ]
        critiques = [
            {
                "paper_id": "p1",
                "title": "Decentralized Federated Agent Consensus Protocols",
                "critique": {
                    "limitations": ["fails to converge when node count exceeds 50 agents"],
                    "evaluation_flaws": ["lacks statistical latency distribution bounds"],
                    "assumptions": ["requires synchronized network clocks"],
                    "methodology_type": "Theoretical"
                }
            }
        ]
        query = "Distributed Consensus Agents"

        # 2. Generate fallback gaps
        gaps = generate_dynamic_fallback_gaps(critiques, papers, query)

        # 3. Assertions on dynamic assembly
        self.assertEqual(len(gaps), 3)
        
        # Gap 1 (Methodological) should incorporate first paper title & flaws
        self.assertIn("Decentralized Federated Agent Consensus Protocols", gaps[0]["title"])
        self.assertIn("fails to converge", gaps[0]["description"])
        self.assertIn("lacks statistical latency", gaps[0]["description"])
        self.assertEqual(gaps[0]["category"], "methodological")
        
        # Gap 2 (Empirical) should incorporate query & assumptions
        self.assertIn("Distributed Consensus Agents", gaps[1]["title"])
        self.assertIn("requires synchronized network clocks", gaps[1]["description"])
        self.assertEqual(gaps[1]["category"], "empirical")
        
        # Gap 3 (Theoretical) should mention the contradiction between first two papers
        self.assertIn("Distributed Consensus Agents", gaps[2]["title"])
        self.assertIn("Decentralized Federated Agent Consensus Protocols", gaps[2]["description"])
        self.assertIn("Robustness Limits of Autonomous LLM Chains", gaps[2]["description"])
        self.assertEqual(gaps[2]["category"], "theoretical")

        print("[OK] Gap Analyzer dynamic fallback logic verified successfully!")

    @patch("app.agents.nodes.analyzer.call_llm")
    @patch("app.agents.nodes.analyzer.async_session_maker")
    @patch("app.agents.nodes.analyzer.log_agent_step")
    def test_analyzer_node_execution(self, mock_log, mock_db_maker, mock_call_llm):
        import json
        # Mock call_llm to avoid live API call during unit testing
        mock_call_llm.return_value = (
            json.dumps([
                {
                    "title": "Methodological Validation Gaps in Paper Alpha",
                    "description": "desc",
                    "category": "methodological",
                    "severity": "high",
                    "suggested_directions": []
                },
                {
                    "title": "Restricted Testing Populations",
                    "description": "desc",
                    "category": "empirical",
                    "severity": "medium",
                    "suggested_directions": []
                },
                {
                    "title": "Contradictory Scalability Claims",
                    "description": "desc",
                    "category": "theoretical",
                    "severity": "high",
                    "suggested_directions": []
                }
            ]),
            "gemini"
        )
        # Setup mock db session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_db_maker.return_value.__aenter__.return_value = mock_session

        state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "query": "Cooperative Reasoning Heuristics",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [
                {"id": "p1", "title": "Paper Alpha"}
            ],
            "critiques": [
                {
                    "paper_id": "p1",
                    "title": "Paper Alpha",
                    "critique": {
                        "limitations": ["assumes static token boundaries"],
                        "evaluation_flaws": ["does not test hardware degradation"],
                        "assumptions": ["perfect API network connectivity"],
                        "methodology_type": "Empirical"
                    }
                }
            ],
            "gaps": [],
            "synthesis_report": "",
            "logs": []
        }

        # Invoke node
        result = self.loop.run_until_complete(analyzer_node(state))
        parsed_gaps = result["gaps"]

        # Assertions
        self.assertEqual(len(parsed_gaps), 3)
        self.assertIn("Paper Alpha", parsed_gaps[0]["title"])
        self.assertTrue(mock_session.add.called)
        self.assertTrue(mock_session.commit.called)
        print("[OK] Gap Analyzer node wrapper execution verified successfully!")

if __name__ == "__main__":
    unittest.main()
