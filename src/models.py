"""antigravity_glm_mcp 데이터 모델"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    """에러 코드"""
    SUCCESS = "SUCCESS"
    INVALID_PARAMS = "INVALID_PARAMS"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_EXISTS = "FILE_EXISTS"
    API_ERROR = "API_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUTH_ERROR = "AUTH_ERROR"


class ToolResponse(BaseModel):
    """MCP 도구 응답 모델"""
    success: bool
    code: ErrorCode = ErrorCode.SUCCESS
    message: str
    data: Optional[Any] = None


class GLMRequest(BaseModel):
    """GLM API 요청 모델"""
    task_description: str = Field(..., description="작업 설명")
    context: Optional[str] = Field(None, description="추가 컨텍스트")
    max_tokens: int = Field(2000, ge=1, le=8000)
    temperature: float = Field(0.7, ge=0, le=1)


class GLMResponse(BaseModel):
    """GLM API 응답 모델"""
    content: str
    tokens_used: int
    model: str = "glm-4"


class FileOperation(BaseModel):
    """파일 작업 기록"""
    operation: str  # read, create, edit, delete
    file_path: str
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool
    details: Optional[str] = None


class BackupInfo(BaseModel):
    """백업 정보"""
    file_path: str
    backup_path: str
    version: int
    created_at: datetime
    size_bytes: int


class ActionLog(BaseModel):
    """작업 로그"""
    id: str
    action: str
    timestamp: datetime
    details: dict
    success: bool
