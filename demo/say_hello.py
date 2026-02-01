import asyncio
import os
import sys

# Add project root to path
sys.path.append("/Users/hwanchoi/opensource_projects/gemini-glm-agent-mcp")

from src.core.glm_client import get_glm_client

# Explicitly set env vars for this script if not already set in the shell
os.environ["ZHIPU_API_KEY"] = "bd9b45e80d5d489fb912dde188df0aa2.09LUOUkQWjVkctqo"
os.environ["GLM_MODEL"] = "GLM-4.5"
os.environ["GLM_BASE_URL"] = "https://api.z.ai/api/coding/paas/v4"
os.environ["PROJECT_ROOT"] = "/Users/hwanchoi/opensource_projects/gemini-glm-agent-mcp/demo"

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
