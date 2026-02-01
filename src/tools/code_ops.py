"""
code_ops.py - 코드 실행 도구

Python 코드를 샌드박스 환경 내에서 실행합니다.
보안을 위해 일부 위험한 모듈 사용이 제한될 수 있습니다.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator

class CodeRunParams(BaseModel):
    """코드 실행 파라미터"""
    code: str = Field(..., description="실행할 Python 코드")
    timeout: int = Field(10, description="실행 제한 시간 (초, 기본 10초)")

async def glm_code_run(params: CodeRunParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        project_root = validator.project_root

        # 임시 파일에 코드 작성
        # 주의: 실제 상용 환경에서는 더 강력한 격리(Docker, gVisor 등)가 필요합니다.
        # 현재 구현은 subprocess 레벨의 기본 격리만 제공합니다.
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(params.code)
            tmp_path = Path(tmp_file.name)

        try:
            # subprocess로 코드 실행
            # cwd를 프로젝트 루트로 설정하여 로컬 파일 접근 허용 (샌드박스 내에서)
            # PYTHONPATH를 설정하여 현재 프로젝트 모듈 접근 허용
            
            # [보안 조치] 호스트의 환경 변수가 자식 프로세스에 노출되지 않도록 엄격히 필터링
            # API Key, 민감한 설정값 등이 실행 중인 코드에서 접근 불가능하도록 차단함
            allowed_env_keys = {'PATH', 'LANG', 'LC_ALL', 'PYTHONIOENCODING'}
            # os.environ 전체를 넘기지 않고, 위에서 지정한 필수 키만 필터링하여 전달
            safe_env = {k: v for k, v in os.environ.items() if k in allowed_env_keys}
            safe_env['PYTHONPATH'] = str(project_root)
            
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(tmp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root),
                env=safe_env  # 필터링된 안전한 환경 변수만 사용
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=params.timeout)
                
                stdout_decoded = stdout.decode().strip()
                stderr_decoded = stderr.decode().strip()
                exit_code = process.returncode

                success = (exit_code == 0)
                
                return ToolResponse(
                    success=success,
                    code=ErrorCode.SUCCESS if success else ErrorCode.INTERNAL_ERROR,
                    message="코드 실행 완료" if success else "코드 실행 중 오류 발생",
                    data={
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
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"코드 실행 시간 초과 ({params.timeout}초)",
                    data={
                        "timeout": True
                    }
                )

        finally:
            # 임시 파일 삭제
            if tmp_path.exists():
                tmp_path.unlink()

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"코드 실행 실패: {str(e)}"
        )
