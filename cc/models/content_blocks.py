from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal



@dataclass
class TextBlock:
    """
    A content block
    """

    text: str
    type: Literal["text"] = 'text'

    def to_api_dict(self) -> dict[str, Any]:
        return {"text": self.text, "type": self.type}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> TextBlock:
        return cls(text=data["text"])


@dataclass
class ToolUseBlock:
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
    def from_api_dict(cls, data: dict[str, Any]) -> ToolUseBlock:
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


@dataclass
class ThinkingBlock:
    """
    An extended thinking content block.
    """

    thinking: str
    signature: str
    type: Literal['thinking'] = 'thinking'

    def to_api_dict(self) -> dict[str, Any]:
        return {"type": self.type, "thinking": self.thinking, "signature": self.signature}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ThinkingBlock:
        return cls(
            thinking=data["thinking"],
            signature=data.get("signature", ""),
        )

@dataclass
class RedactedThinkingBlock:
    """
    A redacted thinking block (content hidden by API).
    """

    data: str = ''
    type: Literal['redacted_thinking'] = 'redacted_thinking'

    def to_api_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": self.data}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> RedactedThinkingBlock:
        return cls(
            data.get("data", ""),
        )


@dataclass
class ImageBlock:
    """
    An image content block.
    """
    source: ImageSource
    type: Literal['image'] = 'image'

    def to_api_dict(self) -> dict[str, Any]:
        return {"type": self.type, "source": self.source.to_api_dict()}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ImageBlock:
        return cls(source=ImageSource.from_api_dict(data["source"]))




@dataclass
class ImageSource:
    """
    Image source data.
    """

    type: Literal['base64'] = 'base64'
    media_type: str = 'image/png'
    data: str = ''

    def to_api_dict(self) -> dict[str, Any]:
        return {"type": self.type, "media_type": self.media_type, "data": self.data}

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ImageSource:
        return cls(
            type=data.get("type", "base64"),
            media_type=data.get("media_type", "image/png"),
            data=data.get("data", ""),
        )




ContentBlock = (
    TextBlock
    | ToolUseBlock
    | ToolResultBlock
    | ThinkingBlock
    | RedactedThinkingBlock
    | ImageBlock
)

AssistantBlock = (
    TextBlock
    | ToolUseBlock
    | ThinkingBlock
    | RedactedThinkingBlock
)

UserContentBlock = (
    TextBlock
    | ToolResultBlock
    | ImageBlock
)

def content_block_from_api_dict(data: dict[str, Any],) -> TextBlock:
    block_type = data["type"]

    match block_type:
        case 'text':
            return TextBlock.from_api_dict(data)

        case "tool_use":
            return ToolUseBlock.from_api_dict(data)

        case "tool_result":
            return ToolResultBlock.from_api_dict(data)

        case "thinking":
            return ThinkingBlock.from_api_dict(data)

        case "redacted_thinking":
            return RedactedThinkingBlock.from_api_dict(data)

        case "image":
            return ImageBlock.from_api_dict(data)

        case _:
            raise ValueError(
                f"Unknown content block type: {block_type}"
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


if __name__ == "__main__":
    api_blocks = [
        {
            "type": "text",
            "text": "准备读取文件",
        },
        {
            "type": "tool_use",
            "id": "toolu_123",
            "name": "Read",
            "input": {
                "file_path": "hello.txt",
            },
        },
        {
            "type": "thinking",
            "thinking": "我需要先查看文件",
            "signature": "abc123",
        },
    ]

    blocks = [
        content_block_from_api_dict(data)
        for data in api_blocks
    ]

    print("转换前的字典列表：")
    print(api_blocks)

    print("转换后的对象列表：")
    for block in blocks:
        print(block)

