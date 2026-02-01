"""GLM 실행기

GLMClient를 래핑하여 도구에서 쉽게 사용할 수 있는 인터페이스를 제공합니다.
Docker 컨테이너 없이 GLM API를 직접 호출합니다.
"""

import os
from typing import Any, Optional

from src.core.config import config
from src.core.glm_client import GLMClient, GLMClientConfig, get_glm_client


# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 Google DeepMind가 제작한 강력한 AI 코딩 에이전트, 'Antigravity'입니다.
당신의 목표는 로컬 시스템의 다양한 도구들을 활용하여 사용자의 복잡한 코딩 및 시스템 작업을 완벽하게 수행하는 것입니다.

[보유 기술 및 도구 세트]
1. 📂 파일/디렉토리: 절대 경로 중심의 CRUD 작업. 모든 작업은 Sandbox 내에서 안전하게 수행됩니다.
2. 💻 코드 실행: Python 구문을 샌드박스에서 실행하여 데이터 분석, 유틸리티 생성 등을 수행합니다.
3. 🌐 웹/네트워크: DuckDuckGo 검색 및 HTTP 요청(SSRF 방호 적용됨)을 통한 정보 수집.
4. 🛠 개발 협업: Git 워크플로우 지원 (상태 확인, 커밋). SQL 데이터베이스(SQLite) 쿼리.
5. 🖼 비전/미디어: 이미지 파일을 분석하여 텍스트로 설명(Vision 능력).
6. ⏰ 자동화: 미래의 특정 시점에 실행될 작업을 예약하고 관리.

[행동 원칙]
- 당신은 극도로 유능하며, 명확하고 실행 가능한 해결책을 제시합니다.
- 복잡한 작업은 단계를 나누어 설명하고, 각 단계에서 필요한 도구를 정확히 식별하십시오.
- 보안이 민감한 작업(삭제, 외부 요청 등) 전에는 항상 잠재적 영향을 고려하십시오.
- 오류 발생 시, 단순히 실패를 보고하는 대신 원인을 분석하고 대안(Alternative)을 제시하십시오.
- 전문적인 톤을 유지하되, 지나치게 장황하지 않게 핵심을 짚으십시오.
"""

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
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """작업 실행

        GLM에게 작업을 요청하고 결과를 반환합니다.

        Args:
            prompt: 작업 설명/프롬프트
            working_dir: 작업 디렉토리 (컨텍스트에 포함됨)
            context: 추가 컨텍스트
            system_prompt: 시스템 프롬프트 (None이면 기본값 사용)

        Returns:
            GLM의 응답
        """
        # 0. 시스템 프롬프트 구성
        if system_prompt is None:
            sys_msg = DEFAULT_SYSTEM_PROMPT
        else:
            sys_msg = system_prompt

        # 1. 컨텍스트 구성
        full_context = ""
        
        # 시스템 프롬프트를 컨텍스트 최상단에 배치
        if sys_msg:
            full_context += f"System:\n{sys_msg}\n\n"

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
