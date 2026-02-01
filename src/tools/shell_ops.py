"""
shell_ops.py - 제한적 쉘 명령 실행 도구

보안을 위해 화이트리스트에 등록된 명령어만 실행할 수 있습니다.
위험한 명령어(rm -rf, sudo 등)는 원천적으로 차단됩니다.
"""

import asyncio
import shlex
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator
from src.core.config import config


# === 화이트리스트 정의 ===
# 안전하다고 판단되는 명령어만 허용
ALLOWED_COMMANDS = {
    # 패키지 관리자 (읽기/설치 작업)
    "pip", "pip3", "npm", "npx", "yarn", "pnpm", "poetry", "uv",
    # 파일 조회 (읽기 전용)
    "ls", "cat", "head", "tail", "wc", "find", "grep", "rg", "fd",
    "tree", "file", "stat", "du", "df",
    # 텍스트 처리
    "echo", "printf", "sed", "awk", "sort", "uniq", "cut", "tr",
    "jq", "yq",
    # 개발 도구
    "python", "python3", "node", "ruby", "go", "cargo", "rustc",
    "flutter", "dart", "java", "javac", "gradle", "mvn",
    # 빌드/테스트
    "make", "cmake", "ninja",
    # 버전 확인
    "which", "whereis", "type",
    # 네트워크 (읽기 전용)
    "curl", "wget", "ping",
    # 기타 유틸리티
    "date", "env", "printenv", "pwd", "id", "whoami",
    "diff", "cmp", "md5sum", "sha256sum",
}

# 명시적 차단 패턴 (화이트리스트에 있더라도 차단)
BLOCKED_PATTERNS = [
    "rm -rf",
    "rm -r /",
    "rm -fr",
    "> /dev/",
    "sudo",
    "su -",
    "chmod 777",
    "curl | sh",
    "curl | bash",
    "wget | sh",
    "; rm",
    "&& rm",
    "|| rm",
    "`rm",
    "$(rm",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",  # Fork bomb
]


class ShellExecParams(BaseModel):
    """쉘 명령 실행 파라미터"""
    command: str = Field(..., description="실행할 명령어 (화이트리스트 기반)")
    cwd: Optional[str] = Field(None, description="작업 디렉토리 (기본값: 프로젝트 루트)")
    timeout: int = Field(60, description="실행 제한 시간 (초, 기본 60초, 최대 300초)")
    capture_stderr: bool = Field(True, description="stderr도 함께 캡처")


def validate_command(command: str) -> tuple[bool, str]:
    """명령어 보안 검증
    
    Returns:
        (is_valid, error_message)
    """
    # 1. 위험 패턴 차단
    command_lower = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in command_lower:
            return False, f"차단된 명령 패턴입니다: {pattern}"
    
    # 2. 첫 번째 명령어(실행 파일) 추출
    try:
        parts = shlex.split(command)
        if not parts:
            return False, "빈 명령어입니다"
        
        base_command = parts[0].split("/")[-1]  # 경로 제거하고 실행파일명만
        
        # 3. 화이트리스트 검증
        if base_command not in ALLOWED_COMMANDS:
            return False, f"허용되지 않은 명령어입니다: {base_command}. 허용 목록: {', '.join(sorted(ALLOWED_COMMANDS)[:10])}..."
        
        return True, ""
        
    except ValueError as e:
        return False, f"명령어 파싱 실패: {str(e)}"


async def glm_shell_exec(params: ShellExecParams) -> ToolResponse:
    """제한적 쉘 명령 실행 (화이트리스트 기반)"""
    try:
        # 1. 명령어 보안 검증
        is_valid, error_msg = validate_command(params.command)
        if not is_valid:
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"보안 정책 위반: {error_msg}"
            )
        
        # 2. 작업 디렉토리 검증
        validator = get_sandbox_validator()
        cwd = params.cwd or str(config.PROJECT_ROOT)
        
        if not validator.validate_path(cwd):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"작업 디렉토리 접근 차단됨 (샌드박스 위반): {cwd}"
            )
        
        resolved_cwd = validator.resolve_path(cwd)
        if not resolved_cwd.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"작업 디렉토리를 찾을 수 없습니다: {cwd}"
            )
        
        # 3. 타임아웃 제한
        timeout = min(params.timeout, 300)  # 최대 5분
        
        # 4. 명령 실행 (shell=True 사용하지 않음 - 보안 강화)
        # shlex.split으로 파싱된 명령어 사용
        args = shlex.split(params.command)
        
        # 5. 환경 변수 필터링 (민감 정보 제거)
        import os
        allowed_env_keys = {'PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'SHELL', 
                           'TERM', 'PYTHONPATH', 'NODE_PATH', 'GOPATH'}
        safe_env = {k: v for k, v in os.environ.items() if k in allowed_env_keys}
        
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE if params.capture_stderr else None,
            cwd=str(resolved_cwd),
            env=safe_env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            stdout_decoded = stdout.decode('utf-8', errors='replace').strip()
            stderr_decoded = stderr.decode('utf-8', errors='replace').strip() if stderr else ""
            exit_code = process.returncode
            
            success = (exit_code == 0)
            
            return ToolResponse(
                success=success,
                code=ErrorCode.SUCCESS if success else ErrorCode.INTERNAL_ERROR,
                message=f"명령 실행 {'완료' if success else '실패'} (exit: {exit_code})",
                data={
                    "command": params.command,
                    "stdout": stdout_decoded,
                    "stderr": stderr_decoded,
                    "exit_code": exit_code,
                    "timeout": False
                }
            )
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return ToolResponse(
                success=False,
                code=ErrorCode.TIMEOUT,
                message=f"명령 실행 시간 초과 ({timeout}초)",
                data={
                    "command": params.command,
                    "timeout": True
                }
            )
            
    except FileNotFoundError:
        return ToolResponse(
            success=False,
            code=ErrorCode.FILE_NOT_FOUND,
            message=f"명령어를 찾을 수 없습니다: {params.command.split()[0]}"
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"명령 실행 실패: {str(e)}"
        )
