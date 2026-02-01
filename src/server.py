#!/usr/bin/env python3
"""gemini-glm-agent-mcp: Gemini (Antigravity)용 GLM-4-plus 협업 MCP 서버"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 도구 import
from src.tools.ask_glm import ask_glm, AskGLMParams
from src.tools.file_ops import (
    glm_file_read, FileReadParams,
    glm_file_create, FileCreateParams,
    glm_file_edit, FileEditParams,
    glm_file_delete, FileDeleteParams,
    glm_file_rollback, FileRollbackParams,
)
from src.tools.reporting import glm_action_log, ActionLogParams
from src.tools.memory_ops import (
    glm_memory_save, MemorySaveParams,
    glm_memory_get, MemoryGetParams,
    glm_memory_list, MemoryListParams,
    glm_memory_delete, MemoryDeleteParams,
)

server = Server("gemini-glm-agent-mcp")

# 도구 정의
TOOLS = [
    Tool(
        name="ask_glm",
        description="GLM-4-plus에 질문을 위임합니다.",
        inputSchema=AskGLMParams.model_json_schema(),
    ),
    Tool(
        name="glm_file_read",
        description="파일 내용을 읽습니다.",
        inputSchema=FileReadParams.model_json_schema(),
    ),
    Tool(
        name="glm_file_create",
        description="새 파일을 생성합니다.",
        inputSchema=FileCreateParams.model_json_schema(),
    ),
    Tool(
        name="glm_file_edit",
        description="파일을 수정합니다 (문자열 교체).",
        inputSchema=FileEditParams.model_json_schema(),
    ),
    Tool(
        name="glm_file_delete",
        description="파일을 삭제합니다.",
        inputSchema=FileDeleteParams.model_json_schema(),
    ),
    Tool(
        name="glm_file_rollback",
        description="파일을 이전 버전으로 복원합니다.",
        inputSchema=FileRollbackParams.model_json_schema(),
    ),
    Tool(
        name="glm_action_log",
        description="작업 로그를 조회합니다.",
        inputSchema=ActionLogParams.model_json_schema(),
    ),
    Tool(
        name="glm_memory_save",
        description="메모리를 저장합니다.",
        inputSchema=MemorySaveParams.model_json_schema(),
    ),
    Tool(
        name="glm_memory_get",
        description="저장된 메모리를 조회합니다.",
        inputSchema=MemoryGetParams.model_json_schema(),
    ),
    Tool(
        name="glm_memory_list",
        description="저장된 메모리 목록을 조회합니다.",
        inputSchema=MemoryListParams.model_json_schema(),
    ),
    Tool(
        name="glm_memory_delete",
        description="저장된 메모리를 삭제합니다.",
        inputSchema=MemoryDeleteParams.model_json_schema(),
    ),
]


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    handlers = {
        "ask_glm": (ask_glm, AskGLMParams),
        "glm_file_read": (glm_file_read, FileReadParams),
        "glm_file_create": (glm_file_create, FileCreateParams),
        "glm_file_edit": (glm_file_edit, FileEditParams),
        "glm_file_delete": (glm_file_delete, FileDeleteParams),
        "glm_file_rollback": (glm_file_rollback, FileRollbackParams),
        "glm_action_log": (glm_action_log, ActionLogParams),
        "glm_memory_save": (glm_memory_save, MemorySaveParams),
        "glm_memory_get": (glm_memory_get, MemoryGetParams),
        "glm_memory_list": (glm_memory_list, MemoryListParams),
        "glm_memory_delete": (glm_memory_delete, MemoryDeleteParams),
    }

    if name not in handlers:
        return [TextContent(type="text", text=f"도구 '{name}'을 찾을 수 없습니다.")]

    try:
        handler, param_class = handlers[name]
        params = param_class(**arguments)
        response = await handler(params)
        return [TextContent(type="text", text=response.model_dump_json(indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"오류: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
