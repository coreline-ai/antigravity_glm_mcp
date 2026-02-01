"""
dir_ops.py - 디렉토리 작업 도구

디렉토리 내의 파일 목록을 조회하고 메타데이터를 반환합니다.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator

class DirListParams(BaseModel):
    """디렉토리 목록 조회 파라미터"""
    path: str = Field(..., description="조회할 디렉토리 경로 (상대 경로 또는 절대 경로)")
    recursive: bool = Field(False, description="하위 디렉토리까지 재귀적으로 조회 여부 (현재는 1단계만 지원)")
    only_directories: bool = Field(False, description="디렉토리만 조회 여부")

async def glm_dir_list(params: DirListParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        
        # 경로 검증 및 절대 경로 변환
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}"
            )
            
        target_path = validator.resolve_path(params.path)
        
        if not target_path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"디렉토리를 찾을 수 없습니다: {params.path}"
            )
            
        if not target_path.is_dir():
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"디렉토리가 아닙니다: {params.path}"
            )

        items = []
        try:
            # os.scandir을 사용하여 효율적으로 조회
            with os.scandir(target_path) as it:
                for entry in it:
                    if params.only_directories and not entry.is_dir():
                        continue
                        
                    try:
                        stat = entry.stat()
                        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        
                        item_type = "directory" if entry.is_dir() else "file"
                        size = stat.st_size if entry.is_file() else 0
                        
                        items.append({
                            "name": entry.name,
                            "type": item_type,
                            "size": size,
                            "modified": modified_time,
                            "path": str(Path(entry.path).relative_to(validator.project_root)) 
                            if str(entry.path).startswith(str(validator.project_root)) else entry.path
                        })
                    except OSError:
                        # 권한 문제 등으로 접근 불가능한 항목은 건너뜀
                        continue
                        
        except OSError as e:
            return ToolResponse(
                success=False,
                code=ErrorCode.INTERNAL_ERROR,
                message=f"디렉토리 조회 실패: {str(e)}"
            )

        # 이름순 정렬
        items.sort(key=lambda x: (x["type"] != "directory", x["name"]))

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"디렉토리 조회 성공: {len(items)}개 항목",
            data={
                "path": str(target_path),
                "total_items": len(items),
                "items": items
            }
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"알 수 없는 오류: {str(e)}"
        )
