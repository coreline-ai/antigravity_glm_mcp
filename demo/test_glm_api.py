"""GLM API 테스트 스크립트

MCP 서버를 거치지 않고 GLM API를 직접 호출하여
API 키와 모델 설정이 올바른지 확인합니다.
Python 3.9 환경에서도 동작합니다.
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트를 python path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.glm_client import GLMClient, GLMClientConfig
import mcp # 설치 확인용

# 사용자 설정
API_KEY = "bd9b45e80d5d489fb912dde188df0aa2.09LUOUkQWjVkctqo"
MODEL = "GLM-4.5"
BASE_URL = "https://api.z.ai/api/coding/paas/v4"

async def test_api():
    print(f"🔵 환경 점검 및 API 테스트 시작")
    print(f" - Python: {sys.version.split()[0]} ({sys.executable})")
    print(f" - MCP Version: {mcp.__version__ if hasattr(mcp, '__version__') else 'Installed'}")
    print(f" - Model: {MODEL}")
    print(f" - URL: {BASE_URL}")
    
    config = GLMClientConfig(
        api_key=API_KEY,
        model=MODEL,
        base_url=BASE_URL,
        timeout=30
    )
    
    client = GLMClient(config)
    
    try:
        print("\n📡 API 호출 중...")
        response = await client.ask("Hello! Who are you?", context="Answer briefly in English.")
        print(f"\n✅ 응답 수신 성공:\n{response}")
        
        stats = client.get_stats()
        print(f"\n📊 통계: {stats}")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_api())
