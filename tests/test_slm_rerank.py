import os
import unittest
from unittest.mock import patch

# Set environment variable
os.environ["SLM_ENABLED"] = "true"

from superlocalmemory.mcp.server import server


async def handle_list_tools():
    return await server.list_tools()


async def handle_call_tool(name, arguments):
    return await server.call_tool(name, arguments)


class TestSLMRerank(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for K3.1 SLM MCP Rerank implementation.
    """

    async def test_rerank_tool_exists(self):
        """Verify that 'rerank' tool is registered on the SLM MCP server."""
        tools = await handle_list_tools()  # type: ignore
        tool_names = [t.name for t in tools]
        self.assertIn("rerank", tool_names)

        # Find the rerank tool definition and check its schema
        rerank_tool = next(t for t in tools if t.name == "rerank")
        desc = rerank_tool.description or ""
        self.assertTrue(
            desc.startswith("Rerank a list of documents based on semantic similarity to a query.")
        )
        self.assertIn("query", rerank_tool.inputSchema["properties"])
        self.assertIn("documents", rerank_tool.inputSchema["properties"])

    @patch("superlocalmemory.core.embeddings.EmbeddingService.embed")
    @patch("superlocalmemory.core.embeddings.EmbeddingService.embed_batch")
    async def test_rerank_basic(self, mock_embed_batch, mock_embed):
        """Verify that basic reranking yields correct ordering, scores, and index/text/score format."""

        def embed_side_effect(text):
            if text == "query":
                return [1.0, 0.0]
            return [0.0, 0.0]

        def embed_batch_side_effect(texts):
            res = []
            for text in texts:
                if text == "doc0":
                    res.append([1.0, 0.0])
                elif text == "doc1":
                    res.append([0.0, 1.0])
                elif text == "doc2":
                    res.append([0.707, 0.707])
                else:
                    res.append([0.0, 0.0])
            return res

        mock_embed.side_effect = embed_side_effect
        mock_embed_batch.side_effect = embed_batch_side_effect

        arguments = {"query": "query", "documents": ["doc0", "doc1", "doc2"], "top_n": 3}

        response = await handle_call_tool("rerank", arguments)
        self.assertEqual(len(response), 1)

        import json

        result = json.loads(response[0].text)  # type: ignore
        self.assertIn("results", result)
        results = result["results"]

        self.assertEqual(len(results), 3)
        # Check ordering (descending score): doc0 (index 0) -> doc2 (index 2) -> doc1 (index 1)
        self.assertEqual(results[0]["index"], 0)
        self.assertEqual(results[0]["text"], "doc0")
        self.assertAlmostEqual(results[0]["score"], 1.0, places=3)

        self.assertEqual(results[1]["index"], 2)
        self.assertEqual(results[1]["text"], "doc2")
        self.assertAlmostEqual(results[1]["score"], 0.707, places=3)

        self.assertEqual(results[2]["index"], 1)
        self.assertEqual(results[2]["text"], "doc1")
        self.assertAlmostEqual(results[2]["score"], 0.0, places=3)

    async def test_rerank_empty_documents(self):
        """Verify that empty document lists gracefully return empty results."""
        arguments = {"query": "query", "documents": [], "top_n": 3}

        response = await handle_call_tool("rerank", arguments)
        self.assertEqual(len(response), 1)

        import json

        result = json.loads(response[0].text)  # type: ignore
        self.assertEqual(result, {"results": []})
