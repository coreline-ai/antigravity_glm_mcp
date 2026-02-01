"""GLM API 클라이언트

Zhipu AI GLM-4-plus API와 직접 통신하는 비동기 클라이언트.
Docker 컨테이너 없이 HTTPS로 직접 호출합니다.
"""

import asyncio
import os
from typing import Any, Optional

from src.core.config import config

import httpx
from pydantic import BaseModel, Field


class GLMClientConfig(BaseModel):
    """GLM 클라이언트 설정"""

    api_key: str = Field(..., description="Zhipu API 키")
    model: str = Field(default="glm-4-plus", description="사용할 모델")
    timeout: int = Field(default=120, description="요청 타임아웃 (초)")
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", description="API 베이스 URL"
    )


class GLMClient:
    """GLM API 클라이언트

    Zhipu AI의 GLM-4 모델과 직접 통신하는 비동기 클라이언트.
    Docker 컨테이너 없이 HTTPS로 직접 호출합니다.
    """

    def __init__(self, config: GLMClientConfig) -> None:
        """클라이언트 초기화

        Args:
            config: 클라이언트 설정
        """
        self.config = config
        self._total_tokens = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._call_count = 0
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    async def _make_request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """API 요청 실행

        Args:
            messages: 메시지 목록

        Returns:
            API 응답

        Raises:
            httpx.HTTPError: HTTP 에러
            httpx.TimeoutException: 타임아웃
        """
        payload = {
            "model": self.config.model,
            "messages": messages,
        }

        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt == self.config.max_retries - 1:
                    raise
                # 지수 백오프: 1초, 2초, 4초...
                wait_time = 2**attempt
                await asyncio.sleep(wait_time)

        # 타입 체커를 위한 폴백 (실제로는 도달하지 않음)
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("요청 실패")

    async def ask(self, task: str, context: Optional[str] = None) -> str:
        """GLM에 질문

        Args:
            task: 질문 내용
            context: 추가 컨텍스트 (선택)

        Returns:
            GLM의 응답

        Raises:
            httpx.HTTPError: API 요청 실패
            httpx.TimeoutException: 타임아웃
        """
        messages: list[dict[str, str]] = []

        # 컨텍스트가 있으면 시스템 메시지로 추가
        if context:
            messages.append({"role": "system", "content": context})

        # 사용자 질문
        messages.append({"role": "user", "content": task})

        # API 요청
        response = await self._make_request(messages)

        # 호출 횟수 증가
        self._call_count += 1

        # 토큰 사용량 업데이트
        if "usage" in response:
            usage = response["usage"]
            self._total_tokens += usage.get("total_tokens", 0)
            self._prompt_tokens += usage.get("prompt_tokens", 0)
            self._completion_tokens += usage.get("completion_tokens", 0)

        # 응답 추출
        if "choices" in response and len(response["choices"]) > 0:
            content: str = response["choices"][0]["message"]["content"]
            return content

        raise ValueError("응답에서 메시지를 찾을 수 없습니다")

    async def check_api(self) -> bool:
        """API 연결 상태 확인

        간단한 요청을 보내 API 키가 유효한지 확인합니다.

        Returns:
            True if API is reachable and key is valid
        """
        try:
            # 간단한 테스트 요청
            await self.ask("ping", context="한 단어로만 응답해주세요.")
            return True
        except Exception:
            return False

    def get_token_usage(self) -> dict[str, int]:
        """토큰 사용량 조회

        Returns:
            토큰 사용량 정보
        """
        return {
            "total": self._total_tokens,
            "prompt": self._prompt_tokens,
            "completion": self._completion_tokens,
        }

    def get_stats(self) -> dict[str, Any]:
        """통계 조회

        Returns:
            호출 통계
        """
        return {
            "call_count": self._call_count,
            "model": self.config.model,
            "base_url": self.config.base_url,
            **self.get_token_usage(),
        }

    async def close(self) -> None:
        """클라이언트 종료"""
        await self._client.aclose()


# 싱글톤 인스턴스
_client: Optional[GLMClient] = None


def get_glm_client() -> GLMClient:
    """GLM 클라이언트 싱글톤 반환

    환경변수에서 ZHIPU_API_KEY를 읽어 클라이언트를 생성합니다.

    Returns:
        GLMClient 인스턴스

    Raises:
        ValueError: ZHIPU_API_KEY가 설정되지 않은 경우
    """
    global _client
    if _client is None:
        api_key = config.ZHIPU_API_KEY
        if not api_key:
            raise ValueError("ZHIPU_API_KEY 환경변수가 설정되지 않았습니다")

        client_config = GLMClientConfig(
            api_key=api_key,
            model=config.GLM_MODEL,
            timeout=config.GLM_TIMEOUT,
            base_url=config.GLM_BASE_URL,
        )
        _client = GLMClient(client_config)
    return _client
