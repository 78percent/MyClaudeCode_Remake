"""WebSearchTool — web search via SerpAPI.

Corresponds to TS: tools/WebSearchTool.

通过 SerpAPI 的 Google 搜索接口实现真实的网络搜索。
需要配置 SERP_API_KEY（或 SERPAPI_KEY），支持环境变量或项目 .env 文件。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from cc.tools.base import Tool, ToolResult, ToolSchema

logger = logging.getLogger(__name__)

WEB_SEARCH_TOOL_NAME = "WebSearch"

# SerpAPI 的 Google 搜索接口
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
MAX_RESULTS_DEFAULT = 5

# 兼容两种常见的 key 命名：用户 .env 里填的是 SERP_API_KEY，官方文档常写 SERPAPI_KEY
_SERPAPI_KEY_NAMES = ("SERP_API_KEY", "SERPAPI_KEY")


def _get_api_key() -> str:
    """Return the SerpAPI key, reading environment then the project .env file.

    与 cc/main.py 的 _load_env 保持一致的优先级：环境变量 > .env 文件。
    工具在子进程/后台 agent 中运行时拿不到 main 的 env dict，所以这里
    自己解析一次 .env，确保 key 填在 .env 里也能被读到。
    """
    for name in _SERPAPI_KEY_NAMES:
        val = os.environ.get(name)
        if val:
            return val

    # cc/tools/web_search/web_search_tool.py → 项目根目录 = parents[3]
    env_file = Path(__file__).resolve().parents[3] / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() in _SERPAPI_KEY_NAMES and v.strip():
                    return v.strip()
    return ""


def _format_results(data: dict[str, Any], query: str) -> str:
    """把 SerpAPI 的 JSON 响应整理成模型易读的纯文本。"""
    lines: list[str] = [f"Search results for: {query}\n"]

    # 优先展示 answer_box（天气、汇率、百科定义等直接答案）
    answer_box = data.get("answer_box") or {}
    if answer_box:
        lines.append("Direct answer:")
        for key in ("title", "answer", "snippet", "result"):
            val = answer_box.get(key)
            if val:
                lines.append(f"  {val}")
        lines.append("")

    organic = data.get("organic_results") or []
    if organic:
        lines.append(f"Top {len(organic)} results:")
        for i, item in enumerate(organic, 1):
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            lines.append(f"{i}. {title}")
            if link:
                lines.append(f"   {link}")
            if snippet:
                lines.append(f"   {snippet}")
    else:
        lines.append("No results found.")

    return "\n".join(lines)


class WebSearchTool(Tool):
    """Search the web via SerpAPI and return formatted results.

    Corresponds to TS: tools/WebSearchTool.
    返回带标题、链接和摘要的结构化结果，供模型直接阅读引用。
    """

    def get_name(self) -> str:
        return WEB_SEARCH_TOOL_NAME

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=WEB_SEARCH_TOOL_NAME,
            description="Search the web for information using a search query.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": MAX_RESULTS_DEFAULT,
                    },
                },
                "required": ["query"],
            },
        )

    def is_concurrency_safe(self, tool_input: dict[str, Any]) -> bool:
        # 搜索请求为只读外部 API 调用，不修改本地状态，可安全并发
        return True

    async def execute(self, tool_input: dict[str, Any]) -> ToolResult:
        query = tool_input.get("query", "")
        if not query:
            return ToolResult(content="Error: query is required", is_error=True)

        api_key = _get_api_key()
        if not api_key:
            return ToolResult(
                content=(
                    "WebSearch requires a SerpAPI key. "
                    "Set SERP_API_KEY (or SERPAPI_KEY) in the project .env file or as an environment variable. "
                    "Get a free key at https://serpapi.com."
                ),
                is_error=True,
            )

        max_results = tool_input.get("max_results", MAX_RESULTS_DEFAULT)
        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = MAX_RESULTS_DEFAULT
        # 夹在 1~10 之间，避免单次返回过多结果撑爆上下文
        max_results = max(1, min(max_results, 10))

        # 延迟导入 httpx，避免在不使用该工具时增加启动时间
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    SERPAPI_ENDPOINT,
                    params={
                        "engine": "google",
                        "q": query,
                        "api_key": api_key,
                        "num": str(max_results),
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            return ToolResult(content=f"SerpAPI HTTP error {e.response.status_code}: {e}", is_error=True)
        except httpx.ConnectError:
            return ToolResult(content="Error: Could not connect to SerpAPI", is_error=True)
        except Exception as e:
            return ToolResult(content=f"Error searching: {e}", is_error=True)

        # 组织结果为可读文本
        return ToolResult(content=_format_results(data, query))
