import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to system path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.agents.nodes.optimizer import rule_based_keyword_extraction, query_optimization_node

class TestQueryOptimizer(unittest.TestCase):
    def setUp(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def test_rule_based_keyword_extraction(self):
        # Test case 1: Credit Card Fraud Detection
        title = "Credit Card Fraud Detection"
        desc = "This project determines whether a transaction is fraud or safe."
        keywords = rule_based_keyword_extraction(title, desc)
        
        # Verify cleaning and stop word filtering
        self.assertIn("credit", keywords)
        self.assertIn("card", keywords)
        self.assertIn("fraud", keywords)
        self.assertIn("detection", keywords)
        self.assertIn("transaction", keywords)
        self.assertIn("safe", keywords)
        
        # Stop words like "this", "project", "determines", "whether", "is", "or" should be filtered
        word_list = keywords.split()
        self.assertNotIn("this", word_list)
        self.assertNotIn("project", word_list)
        self.assertNotIn("determines", word_list)
        self.assertNotIn("whether", word_list)
        
        # Check uniqueness
        self.assertEqual(len(word_list), len(set(word_list)))

    @patch("app.agents.nodes.optimizer.call_llm")
    @patch("app.agents.nodes.optimizer.log_agent_step")
    def test_query_optimization_node_gemini_success(self, mock_log, mock_call_llm):
        # Mock Gemini returning optimized query
        mock_call_llm.return_value = (
            "credit card fraud detection machine learning transaction classification financial anomaly detection",
            "gemini"
        )
        
        state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "project_title": "Credit Card Fraud Detection",
            "project_description": "This project determines whether a transaction is fraud or safe.",
            "query": "",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [],
            "critiques": [],
            "gaps": [],
            "synthesis_report": "",
            "logs": []
        }
        
        result = self.loop.run_until_complete(query_optimization_node(state))
        
        # Assertions
        self.assertIn("query", result)
        self.assertEqual(
            result["query"],
            "credit card fraud detection machine learning transaction classification financial anomaly detection"
        )
        self.assertTrue(mock_call_llm.called)
        
        # Verify log_agent_step was called and contains correct log level/agent name
        mock_log.assert_any_call(
            project_id="00000000-0000-0000-0000-000000000000",
            agent_name="QueryOptimizerAgent",
            step_name="query_optimization",
            log_level="INFO",
            message=unittest.mock.ANY
        )

    @patch("app.agents.nodes.optimizer.call_llm")
    @patch("app.agents.nodes.optimizer.log_agent_step")
    def test_query_optimization_node_fallback(self, mock_log, mock_call_llm):
        # Mock call_llm triggering fallback (returns mock_fallback and "fallback")
        def side_effect(system_prompt, user_prompt, mock_fallback):
            return mock_fallback, "fallback"
        mock_call_llm.side_effect = side_effect
        
        state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "project_title": "AI for Agriculture",
            "project_description": "Detect crop diseases using images.",
            "query": "",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [],
            "critiques": [],
            "gaps": [],
            "synthesis_report": "",
            "logs": []
        }
        
        result = self.loop.run_until_complete(query_optimization_node(state))
        
        # The output query should be the rule-based keyword extraction results
        expected_keywords = rule_based_keyword_extraction("AI for Agriculture", "Detect crop diseases using images.")
        self.assertEqual(result["query"], expected_keywords)
        
        # Verify fallback logging (log_level="WARNING")
        mock_log.assert_any_call(
            project_id="00000000-0000-0000-0000-000000000000",
            agent_name="QueryOptimizerAgent",
            step_name="query_optimization",
            log_level="WARNING",
            message=unittest.mock.ANY
        )

    @patch("app.agents.nodes.optimizer.call_llm")
    @patch("app.agents.nodes.optimizer.log_agent_step")
    def test_query_optimization_length_capping(self, mock_log, mock_call_llm):
        # Mock Gemini returning more than 20 keywords
        long_query = " ".join([f"keyword{i}" for i in range(30)])
        mock_call_llm.return_value = (long_query, "gemini")
        
        state = {
            "project_id": "00000000-0000-0000-0000-000000000000",
            "project_title": "Title",
            "project_description": "Desc",
            "query": "",
            "iteration": 1,
            "max_iterations": 3,
            "papers_metadata": [],
            "critiques": [],
            "gaps": [],
            "synthesis_report": "",
            "logs": []
        }
        
        result = self.loop.run_until_complete(query_optimization_node(state))
        
        # The query should be capped at 20 keywords
        words = result["query"].split()
        self.assertEqual(len(words), 20)
        self.assertEqual(words[0], "keyword0")
        self.assertEqual(words[-1], "keyword19")

if __name__ == "__main__":
    unittest.main()
