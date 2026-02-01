import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models import ErrorCode
# 대상 도구들 임포트
from src.tools.file_ops import (
    glm_file_read, FileReadParams,
    glm_file_create, FileCreateParams,
    glm_file_edit, FileEditParams,
    glm_file_delete, FileDeleteParams,
    glm_file_rollback, FileRollbackParams,
)
from src.tools.dir_ops import glm_dir_list, DirListParams
from src.tools.memory_ops import (
    glm_memory_save, MemorySaveParams,
    glm_memory_get, MemoryGetParams,
    glm_memory_list, MemoryListParams,
    glm_memory_delete, MemoryDeleteParams,
)
from src.tools.reporting import glm_action_log, ActionLogParams
from src.tools.code_ops import glm_code_run, CodeRunParams
from src.tools.web_ops import glm_web_search, WebSearchParams
from src.tools.git_ops import (
    glm_git_status, GitStatusParams,
    glm_git_log, GitLogParams,
    glm_git_diff, GitDiffParams
)
from src.tools.http_ops import glm_http_request, HttpRequestParams
from src.tools.db_ops import glm_db_query, DbQueryParams
from src.tools.schedule_ops import glm_schedule_task, ScheduleTaskParams
from src.tools.grep_ops import glm_grep, GrepParams
from src.tools.shell_ops import glm_shell_exec, ShellExecParams

async def test_tool(name, coro):
    print(f"Testing {name:20}... ", end="", flush=True)
    try:
        res = await coro
        if res.success:
            print("✅ PASS")
        else:
            print(f"❌ FAIL: {res.message}")
        return res.success
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return False

async def main():
    print("=" * 60)
    print("🚀 GLM Agent MCP - Local & Utility Tools Test (Excluding Intelligence/Vision)")
    print("=" * 60)
    
    # 1. 파일 관리
    test_file = "data/local_test.txt"
    await test_tool("glm_file_create", glm_file_create(FileCreateParams(path=test_file, content="Local Tool Test", overwrite=True)))
    await test_tool("glm_file_read", glm_file_read(FileReadParams(path=test_file)))
    await test_tool("glm_file_edit", glm_file_edit(FileEditParams(path=test_file, old_string="Local", new_string="Success")))
    await test_tool("glm_file_rollback", glm_file_rollback(FileRollbackParams(path=test_file, version=-1)))
    await test_tool("glm_file_delete", glm_file_delete(FileDeleteParams(path=test_file)))
    await test_tool("glm_dir_list", glm_dir_list(DirListParams(path="src")))
    await test_tool("glm_grep", glm_grep(GrepParams(pattern="Tool", path="src/tools")))
    
    # 2. 코드/쉘
    await test_tool("glm_code_run", glm_code_run(CodeRunParams(code="print('Hello from test')")))
    await test_tool("glm_shell_exec", glm_shell_exec(ShellExecParams(command="ls -l", cwd=".")))
    
    # 3. Git
    await test_tool("glm_git_status", glm_git_status(GitStatusParams()))
    await test_tool("glm_git_log", glm_git_log(GitLogParams(n=1)))
    await test_tool("glm_git_diff", glm_git_diff(GitDiffParams(stat_only=True)))
    
    # 4. 네트워크
    await test_tool("glm_http_request", glm_http_request(HttpRequestParams(url="https://www.google.com")))
    await test_tool("glm_web_search", glm_web_search(WebSearchParams(query="Zhipu AI")))
    
    # 5. 메모리
    await test_tool("glm_memory_save", glm_memory_save(MemorySaveParams(key="local_key", value="local_val")))
    await test_tool("glm_memory_get", glm_memory_get(MemoryGetParams(key="local_key")))
    await test_tool("glm_memory_list", glm_memory_list(MemoryListParams()))
    await test_tool("glm_memory_delete", glm_memory_delete(MemoryDeleteParams(key="local_key")))
    
    # 6. 고급/기타
    await test_tool("glm_db_query", glm_db_query(DbQueryParams(query="SELECT 1", db_path="data/test.db")))
    await test_tool("glm_schedule_task", glm_schedule_task(ScheduleTaskParams(action="list")))
    await test_tool("glm_action_log", glm_action_log(ActionLogParams(limit=5)))
    
    print("=" * 60)
    print("🏁 Safe Tools Testing Completed.")

if __name__ == "__main__":
    asyncio.run(main())
