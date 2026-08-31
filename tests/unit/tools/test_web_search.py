"""Tests for WebSearchTool.

Verifies schema and SerpAPI behavior (no-key error, result formatting).
"""

import pytest

from cc.tools.web_search import web_search_tool
from cc.tools.web_search.web_search_tool import WebSearchTool, _format_results


class TestWebSearchTool:
    @pytest.mark.asyncio
    async def test_search_without_key_returns_error(self, monkeypatch) -> None:
        # 强制走「无 key」分支，避免测试读到项目 .env 里的真实 key 而发起真实请求
        monkeypatch.setattr(web_search_tool, "_get_api_key", lambda: "")
        tool = WebSearchTool()
        result = await tool.execute({"query": "python testing"})
        assert result.is_error
        assert "SERP_API_KEY" in result.content

    @pytest.mark.asyncio
    async def test_empty_query_error(self) -> None:
        tool = WebSearchTool()
        result = await tool.execute({"query": ""})
        assert result.is_error
        assert "required" in result.content

    @pytest.mark.asyncio
    async def test_schema(self) -> None:
        tool = WebSearchTool()
        assert tool.get_name() == "WebSearch"
        schema = tool.get_schema()
        assert schema.name == "WebSearch"
        assert "query" in schema.input_schema["properties"]
        assert "max_results" in schema.input_schema["properties"]
        assert "query" in schema.input_schema["required"]

    @pytest.mark.asyncio
    async def test_concurrency_safe(self) -> None:
        tool = WebSearchTool()
        assert tool.is_concurrency_safe({}) is True

    def test_format_results(self) -> None:
        data = {
            "answer_box": {"title": "Weather", "answer": "Sunny 25C"},
            "organic_results": [
                {"title": "Result 1", "link": "https://example.com", "snippet": "snippet one"},
            ],
        }
        text = _format_results(data, "weather")
        assert "Weather" in text
        assert "Sunny 25C" in text
        assert "Result 1" in text
        assert "https://example.com" in text
