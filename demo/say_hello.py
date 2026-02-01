import asyncio
import os
import sys

# Add project root to path
sys.path.append("/Users/hwanchoi/opensource_projects/antigravity_glm_mcp")

from src.core.glm_client import get_glm_client

# Explicitly set env vars for this script if not already set in the shell
# 1. API 키 설정 (환경 변수 ZHIPU_API_KEY가 설정되어 있어야 합니다)
if not os.getenv("ZHIPU_API_KEY"):
    print("ZHIPU_API_KEY 환경 변수가 설정되지 않았습니다.")
    # 아래 줄의 주석을 풀고 본인의 키를 직접 입력할 수도 있습니다 (비추천)
    # os.environ[\"ZHIPU_API_KEY\"] = \"your-api-key-here\"
os.environ["GLM_MODEL"] = "GLM-4.5"
os.environ["GLM_BASE_URL"] = "https://api.z.ai/api/coding/paas/v4"
os.environ["PROJECT_ROOT"] = "/Users/hwanchoi/opensource_projects/antigravity_glm_mcp/demo"

async def main():
    try:
        client = get_glm_client()
        print("🤖 GLM에게 질문 중: '안녕? 자기소개 좀 해줘'...")
        response = await client.ask("안녕? 자기소개 좀 해줘")
        print("\n[GLM 응답]")
        print(response)
        await client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
