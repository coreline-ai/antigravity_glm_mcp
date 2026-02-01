"""GLM 실행기

GLMClient를 래핑하여 도구에서 쉽게 사용할 수 있는 인터페이스를 제공합니다.
Docker 컨테이너 없이 GLM API를 직접 호출합니다.
"""

import os
from typing import Any, Optional

from src.core.glm_client import GLMClient, GLMClientConfig, get_glm_client


class GLMExecutor:
    """GLM 실행기

    GLMClient를 래핑하여 작업 실행에 필요한 추가 기능을 제공합니다.
    """

    def __init__(self, client: Optional[GLMClient] = None):
        """초기화

        Args:
            client: GLMClient 인스턴스 (없으면 싱글톤 사용)
        """
        self._client = client

    @property
    def client(self) -> GLMClient:
        """GLM 클라이언트 반환 (지연 초기화)"""
        if self._client is None:
            self._client = get_glm_client()
        return self._client

    async def execute(
        self,
        prompt: str,
        working_dir: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """작업 실행

        GLM에게 작업을 요청하고 결과를 반환합니다.

        Args:
            prompt: 작업 설명/프롬프트
            working_dir: 작업 디렉토리 (컨텍스트에 포함됨)
            context: 추가 컨텍스트

        Returns:
            GLM의 응답
        """
        # 컨텍스트 구성
        full_context = ""
        if working_dir:
            full_context += f"작업 디렉토리: {working_dir}\n"
        if context:
            full_context += context

        return await self.client.ask(
            task=prompt,
            context=full_context if full_context else None
        )

    async def execute_file_operation(
        self,
        operation: str,
        file_path: str,
        content: Optional[str] = None,
        old_string: Optional[str] = None,
        new_string: Optional[str] = None
    ) -> dict[str, Any]:
        """파일 작업 실행

        Args:
            operation: 작업 유형 (read, create, edit, delete)
            file_path: 파일 경로
            content: 파일 내용 (create 시)
            old_string: 교체할 문자열 (edit 시)
            new_string: 새 문자열 (edit 시)

        Returns:
            작업 결과
        """
        prompts = {
            "read": f"파일을 읽어서 내용을 분석해줘: {file_path}",
            "create": f"다음 내용으로 파일을 생성해줘.\n파일 경로: {file_path}\n내용:\n```\n{content}\n```",
            "edit": f"파일을 수정해줘.\n파일 경로: {file_path}\n교체할 문자열: {old_string}\n새 문자열: {new_string}",
            "delete": f"파일을 삭제해줘: {file_path}"
        }

        prompt = prompts.get(operation)
        if not prompt:
            raise ValueError(f"지원하지 않는 작업: {operation}")

        result = await self.execute(prompt)

        return {
            "operation": operation,
            "file_path": file_path,
            "result": result,
            "success": True
        }

    async def check_api(self) -> bool:
        """API 상태 확인

        Returns:
            API가 사용 가능하면 True
        """
        return await self.client.check_api()

    def get_stats(self) -> dict[str, Any]:
        """실행 통계 반환

        Returns:
            통계 정보
        """
        return self.client.get_stats()

    async def close(self) -> None:
        """리소스 정리"""
        if self._client:
            await self._client.close()


# 싱글톤 인스턴스
_executor: Optional[GLMExecutor] = None


def get_glm_executor() -> GLMExecutor:
    """GLM 실행기 싱글톤 반환

    Returns:
        GLMExecutor 인스턴스
    """
    global _executor
    if _executor is None:
        _executor = GLMExecutor()
    return _executor
