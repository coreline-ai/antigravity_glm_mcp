#!/usr/bin/env python3
"""antigravity_glm_mcp: Gemini (Antigravity)용 GLM-4-plus 협업 MCP 서버"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 1. 지능 도구
from src.tools.glm_cmd import glm_cmd, GlmCmdParams, glm_bypass, GlmBypassParams

# 2. 파일 관리 도구
from src.tools.file_ops import (
    glm_file_read, FileReadParams,
    glm_file_create, FileCreateParams,
    glm_file_edit, FileEditParams,
    glm_file_delete, FileDeleteParams,
    glm_file_rollback, FileRollbackParams,
)
from src.tools.dir_ops import glm_dir_list, DirListParams

# 3. 메모리 관리 도구
from src.tools.memory_ops import (
    glm_memory_save, MemorySaveParams,
    glm_memory_get, MemoryGetParams,
    glm_memory_list, MemoryListParams,
    glm_memory_delete, MemoryDeleteParams,
)

# 4. 리포팅 도구
from src.tools.reporting import glm_action_log, ActionLogParams, get_action_logger
import time

# [확장] 5. 코드 및 웹 도구 (1순위)
from src.tools.code_ops import glm_code_run, CodeRunParams
from src.tools.web_ops import glm_web_search, WebSearchParams

# [확장] 6. 협업 도구 (2순위)
from src.tools.git_ops import (
    glm_git_status, GitStatusParams,
    glm_git_commit, GitCommitParams,
    glm_git_log, GitLogParams,
    glm_git_diff, GitDiffParams
)
from src.tools.http_ops import glm_http_request, HttpRequestParams

# [확장] 7. 고급 기능 (3순위)
from src.tools.db_ops import glm_db_query, DbQueryParams
from src.tools.image_ops import glm_image_analyze, ImageAnalyzeParams
from src.tools.schedule_ops import glm_schedule_task, ScheduleTaskParams

# [신규] 8. 탐색 및 쉘 도구
from src.tools.grep_ops import glm_grep, GrepParams
from src.tools.shell_ops import glm_shell_exec, ShellExecParams


server = Server("antigravity_glm_mcp")

# 도구 정의
TOOLS = [
    # --- 기본 도구 (11개) ---
    Tool(name="glm_cmd", description="GLM-4-plus에 질문을 위임합니다. (지능)", inputSchema=GlmCmdParams.model_json_schema()),
    Tool(name="glm_bypass", description="GLM에 원시 프롬프트를 직접 보냅니다. (Raw Mode)", inputSchema=GlmBypassParams.model_json_schema()),
    Tool(name="glm_file_read", description="파일 내용을 읽습니다.", inputSchema=FileReadParams.model_json_schema()),
    Tool(name="glm_file_create", description="새 파일을 생성합니다.", inputSchema=FileCreateParams.model_json_schema()),
    Tool(name="glm_file_edit", description="파일을 수정합니다 (문자열 교체).", inputSchema=FileEditParams.model_json_schema()),
    Tool(name="glm_file_delete", description="파일을 삭제합니다 (백업 보관).", inputSchema=FileDeleteParams.model_json_schema()),
    Tool(name="glm_file_rollback", description="파일을 복원합니다.", inputSchema=FileRollbackParams.model_json_schema()),
    Tool(name="glm_memory_save", description="메모리 저장.", inputSchema=MemorySaveParams.model_json_schema()),
    Tool(name="glm_memory_get", description="메모리 조회.", inputSchema=MemoryGetParams.model_json_schema()),
    Tool(name="glm_memory_list", description="메모리 목록.", inputSchema=MemoryListParams.model_json_schema()),
    Tool(name="glm_memory_delete", description="메모리 삭제.", inputSchema=MemoryDeleteParams.model_json_schema()),
    Tool(name="glm_action_log", description="작업 로그 조회.", inputSchema=ActionLogParams.model_json_schema()),
    
    # --- 확장 도구 (9개) ---
    Tool(name="glm_dir_list", description="디렉토리 목록 조회.", inputSchema=DirListParams.model_json_schema()),
    Tool(name="glm_code_run", description="Python 코드 실행 (샌드박스).", inputSchema=CodeRunParams.model_json_schema()),
    Tool(name="glm_web_search", description="웹 검색 (DuckDuckGo).", inputSchema=WebSearchParams.model_json_schema()),
    Tool(name="glm_git_status", description="Git 상태 조회.", inputSchema=GitStatusParams.model_json_schema()),
    Tool(name="glm_git_commit", description="Git 커밋.", inputSchema=GitCommitParams.model_json_schema()),
    Tool(name="glm_http_request", description="HTTP 요청.", inputSchema=HttpRequestParams.model_json_schema()),
    Tool(name="glm_db_query", description="DB 쿼리 (SQLite).", inputSchema=DbQueryParams.model_json_schema()),
    Tool(name="glm_image_analyze", description="이미지 분석 (Vision).", inputSchema=ImageAnalyzeParams.model_json_schema()),
    Tool(name="glm_schedule_task", description="작업 예약 관리.", inputSchema=ScheduleTaskParams.model_json_schema()),
    
    # --- 신규 도구 (4개) ---
    Tool(name="glm_grep", description="파일 내용 검색 (grep).", inputSchema=GrepParams.model_json_schema()),
    Tool(name="glm_git_log", description="Git 커밋 이력 조회.", inputSchema=GitLogParams.model_json_schema()),
    Tool(name="glm_git_diff", description="Git 변경 사항 비교.", inputSchema=GitDiffParams.model_json_schema()),
    Tool(name="glm_shell_exec", description="제한적 쉘 명령 실행 (화이트리스트 기반).", inputSchema=ShellExecParams.model_json_schema()),
]


@server.list_tools()
async def list_tools():
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    handlers = {
        "glm_cmd": (glm_cmd, GlmCmdParams),
        "glm_bypass": (glm_bypass, GlmBypassParams),
        "glm_file_read": (glm_file_read, FileReadParams),
        "glm_file_create": (glm_file_create, FileCreateParams),
        "glm_file_edit": (glm_file_edit, FileEditParams),
        "glm_file_delete": (glm_file_delete, FileDeleteParams),
        "glm_file_rollback": (glm_file_rollback, FileRollbackParams),
        "glm_memory_save": (glm_memory_save, MemorySaveParams),
        "glm_memory_get": (glm_memory_get, MemoryGetParams),
        "glm_memory_list": (glm_memory_list, MemoryListParams),
        "glm_memory_delete": (glm_memory_delete, MemoryDeleteParams),
        "glm_action_log": (glm_action_log, ActionLogParams),
        
        # 확장 핸들러
        "glm_dir_list": (glm_dir_list, DirListParams),
        "glm_code_run": (glm_code_run, CodeRunParams),
        "glm_web_search": (glm_web_search, WebSearchParams),
        "glm_git_status": (glm_git_status, GitStatusParams),
        "glm_git_commit": (glm_git_commit, GitCommitParams),
        "glm_http_request": (glm_http_request, HttpRequestParams),
        "glm_db_query": (glm_db_query, DbQueryParams),
        "glm_image_analyze": (glm_image_analyze, ImageAnalyzeParams),
        "glm_schedule_task": (glm_schedule_task, ScheduleTaskParams),
        
        # 신규 핸들러
        "glm_grep": (glm_grep, GrepParams),
        "glm_git_log": (glm_git_log, GitLogParams),
        "glm_git_diff": (glm_git_diff, GitDiffParams),
        "glm_shell_exec": (glm_shell_exec, ShellExecParams),
    }

    logger = get_action_logger()
    start_time = time.time()
    success = False
    error_message = None

    if name not in handlers:
        error_message = f"도구 '{name}'을 찾을 수 없습니다."
        # 실패 로그 기록
        await logger.add_log({
            "action": name,
            "params": arguments,
            "success": False,
            "duration": 0,
            "error": error_message
        })
        return [TextContent(type="text", text=error_message)]

    try:
        handler, param_class = handlers[name]
        params = param_class(**arguments)
        response = await handler(params)
        
        success = response.success
        if not success:
            error_message = response.message
            
        return [TextContent(type="text", text=response.model_dump_json(indent=2))]
    except Exception as e:
        error_message = str(e)
        return [TextContent(type="text", text=f"오류: {str(e)}")]
    finally:
        duration = time.time() - start_time
        await logger.add_log({
            "action": name,
            "params": arguments,  # 민감 정보가 있다면 필터링 필요
            "success": success,
            "duration": duration,
            "error": error_message
        })


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
