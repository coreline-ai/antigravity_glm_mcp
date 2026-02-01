# 빠른 시작 가이드: Antigravity GLM MCP

> 5분 안에 Gemini와 GLM-4.5를 연결하세요!

---

## 📋 사전 요구사항

| 항목 | 요구사항 |
|------|----------|
| Python | 3.11 이상 |
| API 키 | [Zhipu AI](https://open.bigmodel.cn/) 발급 |
| 클라이언트 | Gemini (Antigravity) |

---

## 🚀 1. 설치

### 방법 1: 자동 설치 (추천)

```bash
# 1. 저장소 클론
git clone https://github.com/coreline-ai/antigravity_glm_mcp.git
cd antigravity_glm_mcp

# 2. 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 자동 설치 스크립트 실행
python scripts/install.py
```

- ✅ Gemini Desktop 설정 자동 업데이트

### 🔑 2. 환경 변수 설정 (보안)

로컬 테스트나 수동 설정을 위해 `.env.sample` 파일을 제공합니다.

1.  `.env.sample` 파일을 `.env`로 복사합니다:
    ```bash
    cp .env.sample .env
    ```
2.  `.env` 파일을 열어 `ZHIPU_API_KEY`와 `PROJECT_ROOT`를 입력합니다.
3.  이 파일은 `.gitignore`에 등록되어 있어 외부로 유출되지 않습니다.

### 방법 2: 수동 설정

MCP 설정 파일에 직접 추가:

```json
{
  "mcpServers": {
    "antigravity_glm_mcp": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/antigravity_glm_mcp/src/server.py"],
      "env": {
        "PROJECT_ROOT": "/path/to/your/project",
        "ZHIPU_API_KEY": "your-api-key",
        "PYTHONPATH": "/path/to/antigravity_glm_mcp"
      }
    }
  }
}
```

> [!TIP]
> 가상환경의 Python 경로 (`.venv/bin/python`)를 사용하면 의존성 문제를 피할 수 있습니다.

---

## 🎯 2. 바로 사용해보기

### 🤖 GLM 위임
Gemini 채팅창에서:
- "이 코드를 GLM에게 분석해달라고 해줘"
- "복잡한 알고리즘 리팩토링 계획을 GLM에게 물어봐"

### 📁 파일 작업
- "현재 파일의 `User` 클래스를 `Customer`로 수정해줘"
- "방금 수정한 내용을 이전 버전으로 돌려줘"
- "새로운 API 엔드포인트 파일을 만들어줘"

### 🔍 코드 검색
- "프로젝트에서 `API_KEY` 패턴을 검색해줘"
- "모든 Python 파일에서 `import requests`를 찾아줘"

### 🌿 Git 협업
- "현재 Git 상태를 확인해줘"
- "마지막 5개 커밋 이력을 보여줘"
- "HEAD~1과 현재 변경사항을 비교해줘"

### 💻 쉘 실행
- "pip list로 설치된 패키지를 확인해줘"
- "npm --version으로 Node.js 환경을 확인해줘"

### 🧠 메모리 활용
- "이 프로젝트의 기술 스택은 FastAPI라고 기억해줘"
- "이전에 저장한 프로젝트 컨텍스트를 불러와줘"

---

## ✅ 3. 확인 방법

### 백업 확인
파일 수정 시 `{PROJECT_ROOT}/.glm_backups/`에 백업이 생성됩니다.

### 로그 확인
```
glm_action_log 도구를 호출하여 작업 이력을 확인하세요.
```

### 토큰 사용량
`glm_cmd` 응답에 토큰 사용량이 포함됩니다:
```json
{
  "tokens": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

---

## 🛡️ 보안 참고사항

> [!IMPORTANT]
> - 모든 파일 작업은 `PROJECT_ROOT` 내로 제한됩니다
> - HTTP 요청 시 내부망 IP는 자동 차단됩니다
> - 쉘 명령은 화이트리스트에 등록된 것만 실행됩니다

> [!CAUTION]
> `glm_shell_exec`는 다음 명령을 차단합니다:
> - `rm -rf`, `sudo`, `su -`
> - `curl | sh`, `wget | bash`
> - 기타 위험한 패턴

---

## 🔗 다음 단계

| 문서 | 설명 |
|------|------|
| [도구 참조](TOOLS.md) | 25개 도구 상세 명세 |
| [아키텍처](ARCHITECTURE.md) | 시스템 설계 이해 |

---

<div align="center">

**문제가 있나요?** [이슈 등록](https://github.com/coreline-ai/antigravity_glm_mcp/issues)

</div>
