"""ask_glm 도구

GLM-4-plus API를 직접 호출하여 질문을 위임합니다.
Docker 컨테이너 없이 HTTPS로 직접 통신합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.core.glm_executor import get_glm_executor
from src.models import ToolResponse, ErrorCode


class AskGLMParams(BaseModel):
    """ask_glm 파라미터"""

    task_description: str = Field(
        ...,
        min_length=1,
        description="GLM에게 위임할 작업 설명"
    )
    context: Optional[str] = Field(
        default=None,
        description="추가 컨텍스트 (코드, 파일 내용 등)"
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="작업 디렉토리 경로"
    )

    @field_validator('task_description')
    @classmethod
    def validate_task_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("작업 설명은 비어있을 수 없습니다")
        return v.strip()


async def ask_glm(params: AskGLMParams) -> ToolResponse:
    """GLM에 질문 위임

    GLM-4-plus API를 직접 호출합니다.
    Docker 컨테이너나 Claude CLI 없이 HTTPS로 직접 통신합니다.

    Args:
        params: 요청 파라미터

    Returns:
        GLM 응답
    """
    try:
        executor = get_glm_executor()

        # GLM API 호출
        response = await executor.execute(
            prompt=params.task_description,
            context=params.context,
            working_dir=params.working_dir
        )

        # 통계
        stats = executor.get_stats()

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message="GLM 응답 완료",
            data={
                "content": response,
                "call_count": stats["call_count"],
                "model": stats.get("model", "glm-4-plus"),
                "tokens": {
                    "total": stats.get("total", 0),
                    "prompt": stats.get("prompt", 0),
                    "completion": stats.get("completion", 0),
                }
            }
        )

    except ValueError as e:
        # API 키 미설정 등
        return ToolResponse(
            success=False,
            code=ErrorCode.INVALID_PARAMS,
            message=str(e),
        )
    except TimeoutError as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.TIMEOUT,
            message=str(e),
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.API_ERROR,
            message=f"GLM 호출 실패: {str(e)}",
        )
