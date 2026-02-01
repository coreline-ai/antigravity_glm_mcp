"""
grep_ops.py - 파일 내용 검색 도구

프로젝트 내 파일에서 패턴을 검색합니다.
정규식 및 대소문자 구분 옵션을 지원합니다.
"""

import asyncio
import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator


class GrepParams(BaseModel):
    """파일 내용 검색 파라미터"""
    pattern: str = Field(..., description="검색할 패턴 (문자열 또는 정규식)")
    path: str = Field(".", description="검색 시작 경로 (기본값: 프로젝트 루트)")
    recursive: bool = Field(True, description="하위 디렉토리까지 재귀 검색")
    file_pattern: Optional[str] = Field(None, description="파일 필터 (예: '*.py', '*.js')")
    case_sensitive: bool = Field(True, description="대소문자 구분")
    max_results: int = Field(100, description="최대 결과 수 (성능 보호)")
    context_lines: int = Field(0, description="매칭 라인 전후 컨텍스트 라인 수")


async def glm_grep(params: GrepParams) -> ToolResponse:
    """프로젝트 파일 내용 검색 (grep 기능)"""
    try:
        validator = get_sandbox_validator()
        
        # 경로 검증
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"검색 경로 접근 차단됨 (샌드박스 위반): {params.path}"
            )
        
        search_path = validator.resolve_path(params.path)
        
        if not search_path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"검색 경로를 찾을 수 없습니다: {params.path}"
            )
        
        # 정규식 컴파일
        flags = 0 if params.case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(params.pattern, flags)
        except re.error as e:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"잘못된 정규식 패턴입니다: {str(e)}"
            )
        
        # 파일 목록 수집
        files_to_search: List[Path] = []
        
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            glob_pattern = params.file_pattern or "*"
            if params.recursive:
                files_to_search = list(search_path.rglob(glob_pattern))
            else:
                files_to_search = list(search_path.glob(glob_pattern))
        
        # 파일만 필터링 (디렉토리 제외)
        files_to_search = [f for f in files_to_search if f.is_file()]
        
        # 바이너리 파일 및 .git 디렉토리 제외
        excluded_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.idea'}
        files_to_search = [
            f for f in files_to_search
            if not any(ex in f.parts for ex in excluded_dirs)
        ]
        
        results = []
        total_matches = 0
        
        for file_path in files_to_search:
            if total_matches >= params.max_results:
                break
                
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.splitlines()
                
                for line_num, line in enumerate(lines, start=1):
                    if total_matches >= params.max_results:
                        break
                        
                    if regex.search(line):
                        # 컨텍스트 라인 수집
                        context_before = []
                        context_after = []
                        
                        if params.context_lines > 0:
                            start = max(0, line_num - 1 - params.context_lines)
                            end = min(len(lines), line_num + params.context_lines)
                            context_before = lines[start:line_num - 1]
                            context_after = lines[line_num:end]
                        
                        relative_path = str(file_path.relative_to(validator.project_root))
                        
                        results.append({
                            "file": relative_path,
                            "line_number": line_num,
                            "content": line.strip(),
                            "context_before": context_before if params.context_lines > 0 else None,
                            "context_after": context_after if params.context_lines > 0 else None
                        })
                        total_matches += 1
                        
            except Exception:
                # 읽기 실패한 파일은 스킵 (인코딩 문제 등)
                continue
        
        truncated = total_matches >= params.max_results
        
        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"검색 완료: {len(results)}개 매칭 발견" + (" (결과 제한됨)" if truncated else ""),
            data={
                "pattern": params.pattern,
                "total_matches": len(results),
                "truncated": truncated,
                "results": results
            }
        )
        
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"검색 실패: {str(e)}"
        )
