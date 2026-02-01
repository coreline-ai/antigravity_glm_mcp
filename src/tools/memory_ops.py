"""메모리/컨텍스트 공유 도구

Gemini와 GLM 간 컨텍스트를 공유합니다.
로컬 파일 기반으로 동작합니다.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from src.models import ToolResponse, ErrorCode
from src.core.config import config
import re

# 메모리 저장 경로 (Config 사용)
MEMORY_DIR = config.MEMORY_DIR


class MemorySaveParams(BaseModel):
    """glm_memory_save 파라미터"""
    key: str = Field(..., min_length=1, description="메모리 키")
    value: str = Field(..., description="저장할 값")
    category: str = Field(default="general", description="카테고리")
    ttl_hours: Optional[int] = Field(default=None, description="만료 시간 (시간)")


class MemoryGetParams(BaseModel):
    """glm_memory_get 파라미터"""
    key: str = Field(..., min_length=1, description="메모리 키")
    category: Optional[str] = Field(default=None, description="카테고리 필터")


class MemoryListParams(BaseModel):
    """glm_memory_list 파라미터"""
    category: Optional[str] = Field(default=None, description="카테고리 필터")
    limit: int = Field(default=20, ge=1, le=100, description="최대 개수")


class MemoryDeleteParams(BaseModel):
    """glm_memory_delete 파라미터"""
    key: str = Field(..., min_length=1, description="삭제할 키")


def _ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _validate_category(category: str):
    """카테고리명 보안 검증 (경로 조작 방지)"""
    if not re.match(r"^[a-zA-Z0-9_-]+$", category):
        raise ValueError(f"잘못된 카테고리명입니다 (특수문자 불가): {category}")


def _get_memory_file(category: str) -> Path:
    _validate_category(category)
    _ensure_memory_dir()
    return MEMORY_DIR / f"{category}.json"


def _load_memory(category: str) -> dict:
    file_path = _get_memory_file(category)
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_memory(category: str, data: dict):
    file_path = _get_memory_file(category)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def glm_memory_save(params: MemorySaveParams) -> ToolResponse:
    try:
        memory = _load_memory(params.category)
        entry = {
            "value": params.value,
            "created_at": datetime.now().isoformat(),
            "category": params.category,
        }
        if params.ttl_hours:
            entry["expires_at"] = datetime.now().timestamp() + params.ttl_hours * 3600

        memory[params.key] = entry
        _save_memory(params.category, memory)

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"메모리 저장 완료: {params.key}",
            data={"key": params.key, "category": params.category}
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"메모리 저장 실패: {str(e)}"
        )


async def glm_memory_get(params: MemoryGetParams) -> ToolResponse:
    try:
        categories = [params.category] if params.category else ["general", "code", "decision", "context"]
        for cat in categories:
            memory = _load_memory(cat)
            if params.key in memory:
                entry = memory[params.key]
                if "expires_at" in entry and datetime.now().timestamp() > entry["expires_at"]:
                    del memory[params.key]
                    _save_memory(cat, memory)
                    continue
                return ToolResponse(
                    success=True,
                    code=ErrorCode.SUCCESS,
                    message=f"메모리 조회 완료: {params.key}",
                    data=entry
                )
        return ToolResponse(
            success=False, code=ErrorCode.FILE_NOT_FOUND, message=f"메모리를 찾을 수 없음: {params.key}"
        )
    except Exception as e:
        return ToolResponse(
            success=False, code=ErrorCode.INTERNAL_ERROR, message=f"메모리 조회 실패: {str(e)}"
        )


async def glm_memory_list(params: MemoryListParams) -> ToolResponse:
    try:
        categories = [params.category] if params.category else ["general", "code", "decision", "context"]
        all_entries = []
        for cat in categories:
            memory = _load_memory(cat)
            for key, entry in memory.items():
                if "expires_at" in entry and datetime.now().timestamp() > entry["expires_at"]:
                    continue
                all_entries.append({
                    "key": key,
                    "category": entry["category"],
                    "created_at": entry["created_at"],
                    "preview": entry["value"][:100]
                })
        all_entries.sort(key=lambda x: x["created_at"], reverse=True)
        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"메모리 목록 조회 완료",
            data={"entries": all_entries[:params.limit], "total": len(all_entries)}
        )
    except Exception as e:
        return ToolResponse(
            success=False, code=ErrorCode.INTERNAL_ERROR, message=f"메모리 목록 조회 실패: {str(e)}"
        )


async def glm_memory_delete(params: MemoryDeleteParams) -> ToolResponse:
    try:
        categories = ["general", "code", "decision", "context"]
        for cat in categories:
            memory = _load_memory(cat)
            if params.key in memory:
                del memory[params.key]
                _save_memory(cat, memory)
                return ToolResponse(success=True, code=ErrorCode.SUCCESS, message=f"메모리 삭제 완료: {params.key}")
        return ToolResponse(success=False, code=ErrorCode.FILE_NOT_FOUND, message=f"메모리를 찾을 수 없음: {params.key}")
    except Exception as e:
        return ToolResponse(success=False, code=ErrorCode.INTERNAL_ERROR, message=f"메모리 삭제 실패: {str(e)}")
