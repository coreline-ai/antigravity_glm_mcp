#!/usr/bin/env python3
"""
Gemini GLM Agent MCP 설치 및 설정 스크립트.

이 스크립트는 다음 작업을 수행합니다:
1. Python 의존성 설치
2. 사용자로부터 API 키와 프로젝트 경로 입력
3. Gemini (Antigravity) MCP 설정 파일 자동 업데이트
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ============================================================
# 출력 유틸리티
# ============================================================

def print_banner():
    """설치 배너 출력"""
    print("\n" + "=" * 60)
    print("   🤖 Gemini GLM Agent MCP 설치 도우미")
    print("   25개 도구 | 파일/Git/코드/네트워크/메모리")
    print("=" * 60)


def print_step(msg: str):
    print(f"\n🔵 {msg}")


def print_success(msg: str):
    print(f"✅ {msg}")


def print_warning(msg: str):
    print(f"⚠️  {msg}")


def print_error(msg: str):
    print(f"❌ {msg}")
    sys.exit(1)


# ============================================================
# 의존성 설치
# ============================================================

def install_dependencies():
    """패키지 의존성을 설치합니다."""
    print_step("Python 의존성 설치 중...")
    
    packages = [
        "mcp>=1.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "chardet>=5.0.0",
        "requests>=2.31.0",
        "duckduckgo-search>=4.0.0",
        "zhipuai>=1.0.7",
    ]
    
    try:
        # pip 업그레이드
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            stdout=subprocess.DEVNULL
        )
        
        # 패키지 설치
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages,
            stdout=subprocess.DEVNULL
        )
        print_success("의존성 설치 완료")
        
    except subprocess.CalledProcessError as e:
        print_warning(f"일부 의존성 설치 중 오류 발생 (계속 진행): {e}")


# ============================================================
# 설정 파일 탐색
# ============================================================

def find_gemini_mcp_config() -> Optional[Path]:
    """Gemini MCP 설정 파일 위치를 찾습니다."""
    home = Path.home()
    
    # macOS - Gemini (Antigravity)
    if sys.platform == "darwin":
        # Check both root and antigravity subfolder
        paths = [
            home / ".gemini" / "antigravity" / "mcp_config.json",
            home / ".gemini" / "mcp_config.json"
        ]
        for path in paths:
            if path.exists():
                return path
            
    # Windows
    elif sys.platform == "win32":
        path = home / "AppData/Roaming/Gemini/mcp_config.json"
        if path.exists():
            return path
    
    # Linux
    else:
        path = home / ".config/gemini/mcp_config.json"
        if path.exists():
            return path
            
    return None



# ============================================================
# 설정 업데이트
# ============================================================

def update_config(api_key: str, target_project_root: str, model: str = None, base_url: str = None):
    """MCP 설정 파일을 업데이트합니다."""
    print_step("MCP 설정 구성 중...")
    
    project_root = Path(__file__).parent.parent
    server_script = project_root / "src" / "server.py"
    abs_script_path = str(server_script.resolve())
    abs_project_root = str(project_root.resolve())
    
    # 가상환경 Python 경로 감지
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"  # Windows
    
    python_cmd = str(venv_python.absolute()) if venv_python.exists() else sys.executable
    print(f"   Python 경로: {python_cmd}")
    
    # 환경변수 구성
    env_vars = {
        "PROJECT_ROOT": str(Path(target_project_root).resolve()),
        "ZHIPU_API_KEY": api_key,
        "PYTHONPATH": abs_project_root
    }
    
    if model:
        env_vars["GLM_MODEL"] = model
    if base_url:
        env_vars["GLM_BASE_URL"] = base_url
    
    server_config = {
        "command": python_cmd,
        "args": [abs_script_path],
        "env": env_vars
    }

    # Gemini MCP 설정 업데이트
    config_path = find_gemini_mcp_config()
    
    if config_path:
        print(f"   📄 Gemini 설정 발견: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
            
        if "mcpServers" not in data:
            data["mcpServers"] = {}
            
        data["mcpServers"]["antigravity_glm_mcp"] = server_config
        
        # 백업 생성
        backup_path = config_path.with_suffix('.json.bak')
        shutil.copy2(config_path, backup_path)
        print(f"   📦 백업 생성됨: {backup_path.name}")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print_success("Gemini MCP 설정이 업데이트되었습니다!")
        
    else:
        print_warning("Gemini MCP 설정 파일을 자동으로 찾을 수 없습니다.")
        print("\n아래 내용을 설정 파일에 추가해주세요:\n")
        
        manual_config = {
            "mcpServers": {
                "antigravity_glm_mcp": server_config
            }
        }
        print(json.dumps(manual_config, indent=2, ensure_ascii=False))
        print()


# ============================================================
# 도구 목록 출력
# ============================================================

def print_tool_summary():
    """사용 가능한 도구 목록을 출력합니다."""
    print_step("사용 가능한 도구 (25개)")
    
    tools = {
        "지능 위임": ["glm_cmd", "glm_bypass"],
        "파일 관리": ["glm_file_read", "glm_file_create", "glm_file_edit",
                     "glm_file_delete", "glm_file_rollback", "glm_dir_list"],
        "탐색/검색": ["glm_grep"],
        "코드 실행": ["glm_code_run", "glm_shell_exec"],
        "웹 검색": ["glm_web_search"],
        "Git 협업": ["glm_git_status", "glm_git_commit", "glm_git_log", "glm_git_diff"],
        "네트워크": ["glm_http_request"],
        "메모리": ["glm_memory_save", "glm_memory_get", "glm_memory_list", "glm_memory_delete"],
        "고급": ["glm_db_query", "glm_image_analyze", "glm_schedule_task", "glm_action_log"],
    }
    
    for category, tool_list in tools.items():
        print(f"   {category}: {', '.join(tool_list)}")


# ============================================================
# 메인 함수
# ============================================================

def main():
    print_banner()
    
    # CLI 인자 처리
    import argparse
    parser = argparse.ArgumentParser(description="Gemini GLM Agent MCP 설치 스크립트")
    parser.add_argument("--api-key", help="Zhipu AI API Key")
    parser.add_argument("--path", help="Project Root Path")
    parser.add_argument("--model", help="GLM Model Name (e.g., glm-4-plus)")
    parser.add_argument("--base-url", help="GLM Base URL")
    parser.add_argument("--skip-deps", action="store_true", help="의존성 설치 건너뛰기")
    args, _ = parser.parse_known_args()

    # 1. 의존성 설치
    if not args.skip_deps:
        install_dependencies()
    
    # 2. 정보 입력
    print_step("설정 정보 입력")
    
    api_key = args.api_key
    if not api_key:
        api_key = input("   🔑 Zhipu AI API Key: ").strip()
    
    if not api_key:
        print_error("API Key는 필수입니다.")
        
    target_path = args.path
    if not target_path:
        default_path = os.getcwd()
        user_input = input(f"   📂 GLM 작업 대상 경로 (기본: {default_path}): ").strip()
        target_path = user_input or default_path
        
    if not os.path.exists(target_path):
        if args.path:
            os.makedirs(target_path)
            print(f"   📁 폴더 생성됨: {target_path}")
        else:
            create = input("   경로가 존재하지 않습니다. 생성할까요? (y/n): ").lower()
            if create == 'y':
                os.makedirs(target_path)
            else:
                print_error("유효한 프로젝트 경로가 필요합니다.")

    # 3. 설정 업데이트
    update_config(api_key, target_path, args.model, args.base_url)
    
    # 4. 도구 목록 출력
    print_tool_summary()
    
    # 5. 완료 메시지
    print("\n" + "=" * 60)
    print("🎉 설정이 완료되었습니다!")
    print("")
    print("다음 단계:")
    print("  1. Gemini (Antigravity)를 재시작하세요")
    print("  2. 채팅창에서 도구를 사용해보세요:")
    print('     → "이 코드를 GLM에게 분석해달라고 해줘"')
    print('     → "프로젝트에서 TODO를 검색해줘"')
    print("=" * 60)


if __name__ == "__main__":
    main()
