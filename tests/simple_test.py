import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.tools.glm_cmd import glm_cmd, GlmCmdParams, glm_bypass, GlmBypassParams

async def run_simple_tests():
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ ZHIPU_API_KEY 환경변수가 설정되지 않았습니다.")
        return

    print("--- Testing glm_cmd ---")
    res1 = await glm_cmd(GlmCmdParams(task_description="안녕? 너는 누구니? 간단하게 한 줄로 대답해줘."))
    print(f"Success: {res1.success}")
    if res1.success:
        print(f"Response: {res1.data.get('content')}")
    else:
        print(f"Error: {res1.message}")

    print("\n--- Testing glm_bypass ---")
    res2 = await glm_bypass(GlmBypassParams(prompt="1+1은 뭐니? 숫자만 대답해줘."))
    print(f"Success: {res2.success}")
    if res2.success:
        print(f"Response: {res2.data.get('response')}")
    else:
        print(f"Error: {res2.message}")

if __name__ == "__main__":
    asyncio.run(run_simple_tests())
