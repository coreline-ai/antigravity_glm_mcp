"""reporting 도구 구현"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from src.models import ToolResponse, ErrorCode


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
        return cls._instance

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
        self._logs.append(log)

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
