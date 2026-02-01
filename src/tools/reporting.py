"""reporting 도구 구현"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from src.models import ToolResponse, ErrorCode
from src.core.config import config
import json
import asyncio
from datetime import datetime
from pathlib import Path


class ActionLogParams(BaseModel):
    """작업 로그 조회 파라미터"""
    limit: int = Field(default=20, ge=1, description="조회할 로그 개수")
    offset: int = Field(default=0, ge=0, description="시작 오프셋")
    action_filter: Optional[str] = Field(default=None, description="액션 타입 필터")


class ActionLogger:
    """작업 로거 (싱글톤)"""
    _instance: Optional["ActionLogger"] = None
    _logs: List[Dict[str, Any]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._logs = []
        self._initialized = True
        # 기존 로그 로드
        asyncio.create_task(self._load_existing_logs())

    async def get_logs(
        self,
        limit: int = 20,
        offset: int = 0,
        action_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filtered_logs = self._logs
        if action_filter:
            filtered_logs = [log for log in self._logs if log.get("action") == action_filter]
        sorted_logs = sorted(filtered_logs, key=lambda x: x.get("timestamp", ""), reverse=True)
        return sorted_logs[offset:offset + limit]

    async def add_log(self, log: Dict[str, Any]) -> None:
        # 타임스탬프 자동 추가
        if "timestamp" not in log:
            log["timestamp"] = datetime.now().isoformat()
            
        self._logs.append(log)
        await self._save_log_entry(log)

    async def _save_log_entry(self, log: Dict[str, Any]) -> None:
        """로그를 파일에 추가 (JSONL)"""
        try:
            log_line = json.dumps(log, ensure_ascii=False) + "\n"
            log_file = config.LOG_FILE
            
            # 부모 디렉토리 생성
            if not log_file.parent.exists():
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
            await asyncio.to_thread(self._append_to_file, log_file, log_line)
        except Exception as e:
            # 로깅 실패가 전체 흐름을 막지 않도록 함
            print(f"로그 저장 실패: {e}")

    def _append_to_file(self, path: Path, content: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    async def _load_existing_logs(self) -> None:
        """기존 로그 파일에서 최근 로그 로드"""
        try:
            log_file = config.LOG_FILE
            if not log_file.exists():
                return

            # 파일이 클 수 있으므로 마지막 N줄만 읽는 것이 좋지만,
            # 여기서는 JSONL이므로 간단히 전체 로드 (메모리 제약 고려 필요시 수정)
            def read_logs():
                loaded = []
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                loaded.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                return loaded

            logs = await asyncio.to_thread(read_logs)
            # 중복 방지를 위해 기존 로그를 교체하거나 병합
            # 여기서는 초기화 시점에만 호출되므로 append
            self._logs.extend(logs)
            # 시간순 정렬
            self._logs.sort(key=lambda x: x.get("timestamp", ""))
        except Exception as e:
            print(f"기존 로그 로드 실패: {e}")

    async def clear_logs(self) -> None:
        self._logs.clear()


_logger_instance: Optional[ActionLogger] = None


def get_action_logger() -> ActionLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ActionLogger()
    return _logger_instance


async def glm_action_log(params: ActionLogParams) -> ToolResponse:
    try:
        logger = get_action_logger()
        logs = await logger.get_logs(limit=params.limit, offset=params.offset, action_filter=params.action_filter)
        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"로그 {len(logs)}개 조회 완료",
            data={"logs": logs, "total": len(logs)}
        )
    except Exception as e:
        return ToolResponse(success=False, code=ErrorCode.INTERNAL_ERROR, message=f"로그 조회 실패: {str(e)}")
