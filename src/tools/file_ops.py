"""file_ops 도구 구현

호스트 시스템에서 직접 파일 작업을 수행합니다.
- 샌드박스 검증: 로컬에서 수행 (보안)
- 백업: 로컬에서 수행 (수정/삭제 전)
- 파일 작업: Python으로 직접 수행
"""

import asyncio
import os
from pathlib import Path

from typing import Optional

import chardet
from pydantic import BaseModel, Field, field_validator

from src.core.backup import BackupManager
from src.core.sandbox import SandboxValidator
from src.models import ErrorCode, ToolResponse

# 상수
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


# 싱글톤 인스턴스
_sandbox_validator: Optional[SandboxValidator] = None
_backup_manager: Optional[BackupManager] = None


def get_sandbox_validator() -> SandboxValidator:
    """샌드박스 검증기 팩토리 (싱글톤)"""
    global _sandbox_validator

    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT 환경변수가 설정되지 않았습니다")

    if _sandbox_validator is None or str(_sandbox_validator.project_root) != project_root:
        _sandbox_validator = SandboxValidator(project_root)

    return _sandbox_validator


def get_backup_manager() -> BackupManager:
    """백업 관리자 팩토리 (싱글톤)"""
    global _backup_manager

    project_root = os.getenv("PROJECT_ROOT", "/tmp")
    backup_dir = Path(project_root) / ".glm_backups"

    if _backup_manager is None or str(_backup_manager.backup_dir) != str(backup_dir):
        _backup_manager = BackupManager(backup_dir=backup_dir, max_versions=10)

    return _backup_manager


# 파라미터 모델
class FileReadParams(BaseModel):
    """파일 읽기 파라미터"""
    path: str = Field(..., description="읽을 파일 경로")
    encoding: str = Field("utf-8", description="파일 인코딩 (기본: utf-8)")


class FileCreateParams(BaseModel):
    """파일 생성 파라미터"""
    path: str = Field(..., description="생성할 파일 경로")
    content: str = Field(..., description="파일 내용")
    overwrite: bool = Field(False, description="기존 파일 덮어쓰기 허용 여부")
    encoding: str = Field("utf-8", description="파일 인코딩")


class FileEditParams(BaseModel):
    """파일 수정 파라미터"""
    path: str = Field(..., description="수정할 파일 경로")
    old_string: str = Field(..., description="찾을 문자열")
    new_string: str = Field(..., description="바꿀 문자열")

    @field_validator("old_string")
    @classmethod
    def validate_old_string(cls, v: str) -> str:
        if not v:
            raise ValueError("old_string은 비어있을 수 없습니다")
        return v


class FileDeleteParams(BaseModel):
    """파일 삭제 파라미터"""
    path: str = Field(..., description="삭제할 파일 경로")


class FileRollbackParams(BaseModel):
    """파일 복원 파라미터"""
    path: str = Field(..., description="복원할 파일 경로")
    version: int = Field(-1, description="복원할 버전 (-1: 최신)")


# 도구 구현
async def glm_file_read(params: FileReadParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}",
            )

        resolved_path = validator.resolve_path(params.path)
        if not resolved_path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"파일을 찾을 수 없습니다: {params.path}",
            )

        file_size = resolved_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"파일 크기가 10MB를 초과합니다 ({file_size / 1024 / 1024:.2f}MB)",
            )

        file_bytes = await asyncio.to_thread(resolved_path.read_bytes)
        detected = chardet.detect(file_bytes)
        encoding = detected.get("encoding", "utf-8") or "utf-8"

        try:
            content = file_bytes.decode(encoding)
        except UnicodeDecodeError:
            content = file_bytes.decode("utf-8", errors="replace")
            encoding = "utf-8"

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"파일 읽기 성공: {params.path}",
            data={
                "content": content,
                "encoding": encoding,
                "size_bytes": file_size,
            },
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"파일 읽기 실패: {str(e)}",
        )


async def glm_file_create(params: FileCreateParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}",
            )

        resolved_path = validator.resolve_path(params.path)
        if resolved_path.exists() and not params.overwrite:
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_EXISTS,
                message=f"파일이 이미 존재합니다: {params.path}",
            )

        # 부모 디렉토리 생성 시 절대 경로 보장
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(resolved_path.write_text, params.content, encoding=params.encoding)

        file_size = resolved_path.stat().st_size

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"파일 생성 성공: {params.path}",
            data={
                "path": str(resolved_path),
                "size_bytes": file_size,
            },
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"파일 생성 실패: {str(e)}",
        )


async def glm_file_edit(params: FileEditParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}",
            )

        resolved_path = validator.resolve_path(params.path)
        if not resolved_path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"파일을 찾을 수 없습니다: {params.path}",
            )

        content = await asyncio.to_thread(resolved_path.read_text, encoding="utf-8")
        count = content.count(params.old_string)
        if count == 0:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"'{params.old_string}' 문자열을 찾을 수 없습니다",
            )
        elif count > 1:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"'{params.old_string}' 문자열이 여러 위치에서 발견되었습니다 ({count}개).",
            )

        backup_manager = get_backup_manager()
        backup_path = await backup_manager.create_backup(resolved_path)

        new_content = content.replace(params.old_string, params.new_string, 1)
        await asyncio.to_thread(resolved_path.write_text, new_content, encoding="utf-8")

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"파일 수정 성공: {params.path}",
            data={
                "changes": 1,
                "backup_path": backup_path,
            },
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"파일 수정 실패: {str(e)}",
        )


async def glm_file_delete(params: FileDeleteParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}",
            )

        resolved_path = validator.resolve_path(params.path)
        if not resolved_path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"파일을 찾을 수 없습니다: {params.path}",
            )

        if resolved_path.is_dir():
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"디렉토리는 삭제할 수 없습니다: {params.path}",
            )

        # 백업 생성 전 절대 경로 사용
        backup_manager = get_backup_manager()
        backup_path = await backup_manager.create_backup(resolved_path)
        await asyncio.to_thread(resolved_path.unlink)

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"파일 삭제 성공: {params.path}",
            data={
                "backup_path": backup_path,
            },
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"파일 삭제 실패: {str(e)}",
        )


async def glm_file_rollback(params: FileRollbackParams) -> ToolResponse:
    try:
        validator = get_sandbox_validator()
        if not validator.validate_path(params.path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"샌드박스 외부 접근 불가: {params.path}",
            )

        resolved_path = validator.resolve_path(params.path)
        backup_manager = get_backup_manager()
        backups = await backup_manager.list_backups(resolved_path)

        if not backups:
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"백업을 찾을 수 없습니다: {params.path}",
            )

        try:
            backup_info = backups[params.version]
        except IndexError:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"잘못된 버전 인덱스: {params.version}",
            )

        success = await backup_manager.restore_backup(resolved_path, params.version)

        if not success:
            return ToolResponse(
                success=False,
                code=ErrorCode.INTERNAL_ERROR,
                message=f"파일 복원 실패: {params.path}",
            )

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"파일 복원 성공: {params.path}",
            data={
                "restored_from": backup_info.backup_path,
                "version": backup_info.version,
            },
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"파일 복원 실패: {str(e)}",
        )
