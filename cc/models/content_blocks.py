from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Literal

@dataclass
class ContentBlock:
    """
    A content block
    """

    text: str
    type: Literal["text"] = 'text'

    def to_api_dict(self) -> dict[str, Any]:
        return {"text": self.text, "type": self.type}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ContentBlock:
        return cls(text=data["text"])


@dataclass
class ToolUseBox:
    """
    A tool use content block (model requesting tool execution)
    """

    id: str
    name: str
    input: dict[str, Any]
    type: Literal["tool_use"] = "tool_use"

    def to_api_dict(self):
        return {"id": self.id, "name": self.name, "input": self.input, "type": self.type}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ToolUseBox:
        return cls(id=data["id"], name=data["name"], input=data["input"], type=data["type"])


@dataclass
class ToolResultContent:
    """
    Content within a tool result - can be text or image.
    """

    type: Literal["text","image"]
    # 如果它是文本块，就用 text 存内容；如果它是图片块，text 可以没有。
    text: str | None = None
    # 如果它是图片块，就用source存图片来源信息
    source: dict[str, Any] = None

    def to_api_dict(self) -> dict[str, Any]:
        if self.type == 'text':
            return {"type": 'text', "text": self.text or ""}
        return {"type": 'image', 'source': self.source or {}}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ToolResultContent:
        block_type = data.get("type", "text")
        if block_type == "text":
            return cls(type='text', text=data.get("text", ""))
        if block_type == "image":
            return cls(type='image', source=data.get("source", {}))

        return cls(type='text', text=data.get("text", str(data)))


@dataclass
class ToolResultBlock:
    """
    A tool result content block (returning results to the model).
    """

    tool_use_id: str
    content: str | list[ToolResultContent]
    is_error: bool = False
    type: Literal['tool_result'] = 'tool_result'

    def to_api_dict(self) -> dict[str, Any]:
        api_content : str | list[dict[str, Any]]
        if isinstance(self.content, str):
            api_content = self.content
        else:
            api_content = [c.to_api_dict() for c in self.content]

        result: dict[str, Any] = {
            'type': self.type,
            "tool_use_id": self.tool_use_id,
            "content": api_content,
        }

        if self.is_error:
            result["is_error"] = True

        return result

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ToolResultBlock:
        raw_content = data["content"]
        if isinstance(raw_content, str):
            content: str | list[ToolResultContent] = raw_content
        else:
            content = [ToolResultContent.from_api_dict(c) for c in raw_content]
        return cls(
            tool_use_id=data["tool_use_id"],
            content=content,
            is_error=data.get("is_error", False),
        )








# block = ContentBlock("你好")
#
#
# test = block.to_api_dict()
# print(test)
#
# contentblock = ContentBlock.from_api_dict(test)
# print(contentblock)




# test2 = ToolUseBox(
#     id="test2",
#     name="test2",
#     input={"path": "test.py"}
# )
#
# print(test2)
#
# test2_dict = test2.to_api_dict()
# print(test2_dict)
#
# tubox = ToolUseBox.from_api_dict(test2_dict)
# print(tubox)

