#!/usr/bin/env python3
"""
Gemini GLM Agent MCP 설치 및 설정 스크립트.

이 스크립트는 다음 작업을 수행합니다:
1. Python 의존성 설치 (pip install -e .)
2. 사용자로부터 API 키와 프로젝트 경로 입력 받기
3. Claude Desktop App의 설정 파일(mcp_config.json 등)을 찾아 자동 업데이트
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

def print_step(msg: str):
    print(f"\n🔵 {msg}")

def print_success(msg: str):
    print(f"✅ {msg}")

def print_error(msg: str):
    print(f"❌ {msg}")
    sys.exit(1)

def install_dependencies():
    """패키지 의존성을 설치합니다."""
    print_step("Python 의존성 설치 중...")
    
    # pyproject.toml 파싱이 어려우므로 필수 패키지 직접 설치
    packages = [
        "mcp>=1.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "chardet>=5.0.0",
        "requests>=2.31.0"
    ]
    
    try:
        # pip 업그레이드 먼저 시도
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        )
        
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages
        )
        print_success("의존성 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 의존성 설치 중 오류 발생 (무시하고 설정 진행): {e}")

def find_claude_config() -> Optional[Path]:
    """Claude Desktop 설정 파일 위치를 찾습니다."""
    home = Path.home()
    
    # macOS
    if sys.platform == "darwin":
        path = home / "Library/Application Support/Claude/claude_desktop_config.json"
        if path.exists():
            return path
            
    # Windows
    elif sys.platform == "win32":
        path = home / "AppData/Roaming/Claude/claude_desktop_config.json"
        if path.exists():
            return path
            
    return None

def update_config(api_key: str, target_project_root: str, model: str = None, base_url: str = None):
    """MCP 설정 파일을 업데이트합니다."""
    print_step("MCP 설정 구성 중...")
    
    config_path = find_claude_config()
    current_script = Path(__file__).parent.parent / "src" / "server.py"
    project_root = Path(__file__).parent.parent
    abs_script_path = str(current_script.resolve())
    abs_project_root = str(project_root.resolve())
    
    # 가상환경 Python 경로 감지
    venv_python = project_root / ".venv" / "bin" / "python"
    python_cmd = str(venv_python.absolute()) if venv_python.exists() else sys.executable
    print_step(f"Python 실행 경로: {python_cmd}")
    
    env_vars = {
        "PROJECT_ROOT": str(Path(target_project_root).resolve()),
        "ZHIPU_API_KEY": api_key,
        "PYTHONPATH": abs_project_root  # 모듈 import를 위해 추가
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

    if config_path:
        print(f"📄 설정 파일 발견: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
            
        if "mcpServers" not in data:
            data["mcpServers"] = {}
            
        data["mcpServers"]["gemini-glm-agent"] = server_config
        
        # 백업 생성
        backup_path = config_path.with_suffix('.json.bak')
        shutil.copy2(config_path, backup_path)
        print(f"📦 설정 파일 백업됨: {backup_path.name}")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print_success("Claude Desktop 설정이 업데이트되었습니다!")
        
    else:
        print("\n⚠️ Claude Desktop 설정 파일을 자동으로 찾을 수 없습니다.")
        print("아래 내용을 복사하여 설정 파일(mcp_config.json 등)에 추가해주세요:\n")
        
        manual_config = {
            "mcpServers": {
                "gemini-glm-agent": server_config
            }
        }
        print(json.dumps(manual_config, indent=2, ensure_ascii=False))

def main():
    print("="*60)
    print("   Gemini GLM Agent MCP 설정 도우미")
    print("="*60)
    
    # 1. 의존성 설치
    install_dependencies()
    
    # CLI 인자 처리
    import argparse
    parser = argparse.ArgumentParser(description="Gemini GLM Agent MCP 설치 스크립트")
    parser.add_argument("--api-key", help="Zhipu AI API Key")
    parser.add_argument("--path", help="Project Root Path")
    parser.add_argument("--model", help="GLM Model Name (e.g., glm-4-plus)")
    parser.add_argument("--base-url", help="GLM Base URL")
    args, _ = parser.parse_known_args()

    # 2. 정보 입력
    print_step("설정 정보 입력")
    
    api_key = args.api_key
    if not api_key:
        api_key = input("🔑 Zhipu AI API Key 입력: ").strip()
    
    if not api_key:
        print_error("API Key는 필수입니다.")
        
    target_path = args.path
    if not target_path:
        default_path = os.getcwd()
        target_path = input(f"📂 GLM이 작업할 프로젝트 경로 (기본값: {default_path}): ").strip() or default_path
        
    if not os.path.exists(target_path):
        if args.path: # CLI로 전달된 경우 자동 생성 시도
            os.makedirs(target_path)
            print(f"폴더 생성됨: {target_path}")
        else:
            create = input("경로가 존재하지 않습니다. 생성하시겠습니까? (y/n): ").lower()
            if create == 'y':
                os.makedirs(target_path)
            else:
                print_error("유효한 프로젝트 경로가 필요합니다.")

    # 3. 설정 업데이트
    update_config(api_key, target_path, args.model, args.base_url)
    
    print("\n" + "="*60)
    print("🎉 설정이 완료되었습니다!")
    print("이제 Claude/Gemini Desktop을 재시작하면 도구를 사용할 수 있습니다.")
    print("="*60)

if __name__ == "__main__":
    main()
