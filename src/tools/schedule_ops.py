"""
schedule_ops.py - 작업 예약 도구

단순한 JSON 파일 기반의 작업 스케줄러입니다.
실제 백그라운드 실행은 별도의 루프가 필요합니다 (현재는 저장/조회 기능만 제공).
"""

import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from src.models import ErrorCode, ToolResponse

from src.core.config import config

SCHEDULE_FILE = config.SCHEDULE_FILE

class ScheduleTaskParams(BaseModel):
    """작업 예약 파라미터"""
    action: str = Field(..., description="동작: add, list, remove")
    name: Optional[str] = Field(None, description="작업 이름")
    cron: Optional[str] = Field(None, description="cron 표현식 (예: '0 9 * * *')")
    command: Optional[str] = Field(None, description="실행할 명령어 또는 도구 호출 JSON")
    task_id: Optional[str] = Field(None, description="삭제할 작업 ID")

def load_schedule():
    if not SCHEDULE_FILE.exists():
        return []
    try:
        content = SCHEDULE_FILE.read_text(encoding="utf-8")
        if not content.strip():
            return []
        return json.loads(content)
    except json.JSONDecodeError:
        # 파일이 손상되었을 경우, 백업 후 초기화하여 시스템 중단 방지
        backup_path = SCHEDULE_FILE.with_suffix(f".bak.{int(datetime.now().timestamp())}")
        try:
            SCHEDULE_FILE.rename(backup_path)
        except Exception:
            pass # rename 실패 시 무시
        return []
    except Exception as e:
        # 기타 파일 읽기 오류 등
        print(f"스케줄 로드 중 오류: {e}")
        return []

def save_schedule(tasks):
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

async def glm_schedule_task(params: ScheduleTaskParams) -> ToolResponse:
    try:
        tasks = load_schedule()
        
        if params.action == "add":
            if not params.name or not params.cron or not params.command:
                return ToolResponse(success=False, code=ErrorCode.INVALID_PARAMS, message="작업 추가 시 name, cron, command는 필수입니다.")
            
            new_task = {
                "id": str(uuid.uuid4()),
                "name": params.name,
                "cron": params.cron,
                "command": params.command,
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            tasks.append(new_task)
            save_schedule(tasks)
            return ToolResponse(success=True, code=ErrorCode.SUCCESS, message="작업 예약 성공", data=new_task)

        elif params.action == "list":
            return ToolResponse(success=True, code=ErrorCode.SUCCESS, message=f"작업 목록: {len(tasks)}개", data={"tasks": tasks})

        elif params.action == "remove":
            if not params.task_id:
                return ToolResponse(success=False, code=ErrorCode.INVALID_PARAMS, message="작업 삭제 시 task_id가 필요합니다.")
            
            initial_count = len(tasks)
            tasks = [t for t in tasks if t["id"] != params.task_id]
            
            if len(tasks) == initial_count:
                return ToolResponse(success=False, code=ErrorCode.FILE_NOT_FOUND, message=f"작업 ID를 찾을 수 없음: {params.task_id}")
            
            save_schedule(tasks)
            return ToolResponse(success=True, code=ErrorCode.SUCCESS, message="작업 삭제 성공")

        else:
            return ToolResponse(success=False, code=ErrorCode.INVALID_PARAMS, message=f"알 수 없는 동작: {params.action}")

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"스케줄 작업 실패: {str(e)}"
        )
