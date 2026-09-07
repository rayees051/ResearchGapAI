import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to system path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.agents.nodes.ranking import ranking_node
from app.models.user import User
from app.models.project import Project
from app.models.paper import Paper

class TestRankingEngine(unittest.TestCase):
    def setUp(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    @patch("app.agents.nodes.ranking.call_llm")
    @patch("app.agents.nodes.ranking.async_session_maker")
    @patch("app.agents.nodes.ranking.log_agent_step")
    def test_ranking_node_logic(self, mock_log, mock_db_maker, mock_call_llm):
        import json
        mock_call_llm.return_value = (
            json.dumps([
                {
                    "title": "Omission of Real-time User Feedback Channels in Auto-Criticism Agents",
                    "novelty": 7.0,
                    "relevance": 8.0,
                    "feasibility": 8.5,
                    "impact": 7.5
                },
                {
                    "title": "Lack of Multi-Agent Collaboration Benchmarking in Low-Resource Regimes",
                    "novelty": 8.5,
                    "relevance": 9.0,
                    "feasibility": 7.0,
                    "impact": 8.0
                }
            ]),
            "gemini"
        )
        # 1. Setup mock database session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_db_maker.return_value.__aenter__.return_value = mock_session
        
        # Mock database select result for ResearchGap
        mock_db_gap = MagicMock()
        mock_db_gap.title = "Lack of Multi-Agent Collaboration Benchmarking in Low-Resource Regimes"
        
        # Configure select query executing on mock DB
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value.first.return_value = mock_db_gap
        mock_session.execute.return_value = mock_execute_result

        # 2. Define input research state
        state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "query": "Cooperative Agent Chains in Resource-Constrained Environments",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "title": "A Survey of Multi-Agent Systems",
                    "authors": "John Doe",
                    "year": 2024
                }
            ],
            "critiques": [],
            "gaps": [
                {
                    "title": "Omission of Real-time User Feedback Channels in Auto-Criticism Agents",
                    "description": "Analyses reveal that current self-correcting agent chains operate completely autonomously, leading to runaway hallucinations.",
                    "category": "empirical",
                    "severity": "medium"
                },
                {
                    "title": "Lack of Multi-Agent Collaboration Benchmarking in Low-Resource Regimes",
                    "description": "While existing works focus on large-scale agent grids, there is a distinct gap in evaluating how cooperative agent networks perform under strict rate limits.",
                    "category": "methodological",
                    "severity": "high"
                }
            ],
            "synthesis_report": "",
            "logs": []
        }

        # 3. Invoke node
        result = self.loop.run_until_complete(ranking_node(state))
        ranked_gaps = result["gaps"]

        # 4. Assertions
        self.assertEqual(len(ranked_gaps), 2)
        
        # Verify columns are added
        for rg in ranked_gaps:
            self.assertIn("novelty", rg)
            self.assertIn("relevance", rg)
            self.assertIn("feasibility", rg)
            self.assertIn("impact", rg)
            self.assertIn("final_score", rg)
            self.assertIn("rank", rg)
            
            # Verify formula: 0.4*novelty + 0.3*relevance + 0.2*feasibility + 0.1*impact
            expected_score = round(
                0.4 * rg["novelty"] + 
                0.3 * rg["relevance"] + 
                0.2 * rg["feasibility"] + 
                0.1 * rg["impact"], 
                2
            )
            self.assertAlmostEqual(rg["final_score"], expected_score, places=2)

        # Verify sorted descending by final score
        self.assertGreaterEqual(ranked_gaps[0]["final_score"], ranked_gaps[1]["final_score"])
        
        # Verify rank indices
        self.assertEqual(ranked_gaps[0]["rank"], 1)
        self.assertEqual(ranked_gaps[1]["rank"], 2)

        # Verify database commit was triggered
        self.assertTrue(mock_session.commit.called)
        print("[OK] Ranking node unit test assertions passed successfully!")

if __name__ == "__main__":
    unittest.main()
