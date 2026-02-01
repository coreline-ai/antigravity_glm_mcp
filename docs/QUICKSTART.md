# 빠른 시작 가이드: Gemini GLM Agent MCP

이 가이드는 `gemini-glm-agent-mcp`를 바로 사용하기 위한 핵심 절차를 요약합니다.

## 1. 사전 준비

### API 키 발급
[Zhipu AI 오픈 플랫폼](https://open.bigmodel.cn/)에서 API 키를 발급받으세요.

> [!TIP]
> Docker 컨테이너가 필요 없습니다! API 키만 있으면 바로 사용 가능합니다.

## 2. MCP 서버 설정

제미나이(Antigravity)의 MCP 설정 파일(예: `mcp_config.json`)에 아래 내용을 추가합니다.

```json
{
  "mcpServers": {
    "gemini-glm-agent-mcp": {
      "command": "python",
      "args": [
        "/Users/hwanchoi/opensource_projects/gemini-glm-agent-mcp/src/server.py"
      ],
      "env": {
        "PROJECT_ROOT": "/Users/hwanchoi/your-current-project",
        "ZHIPU_API_KEY": "여러분의_지푸_API_키"
      }
    }
  }
}
```

### 환경변수 설명
| 변수명 | 필수 | 설명 |
|--------|------|------|
| `ZHIPU_API_KEY` | ✅ | Zhipu AI에서 발급받은 API 키 |
| `PROJECT_ROOT` | ✅ | GLM이 작업할 프로젝트 폴더의 절대 경로 |
| `GLM_MODEL` | ❌ | 사용할 모델 (기본: `glm-4-plus`) |
| `GLM_TIMEOUT` | ❌ | API 타임아웃 초 (기본: 120) |

## 3. 바로 사용해보기

제미나이 대화창에서 다음과 같이 명령해 보세요.

### 위임 작업 (ask_glm)
- "이 파일의 로직을 GLM에게 분석해달라고 해줘"
- "복잡한 알고리즘 리팩토링 계획을 GLM에게 물어봐"

### 파일 작업 (file_ops)
- "현재 파일의 `User` 클래스를 `Customer`로 수정해줘" (자동 백업 생성됨)
- "방금 수정한 내용을 이전 버전으로 돌려줘 (rollback)"
- "새로운 API 엔드포인트 파일을 만들어줘"

### 메모리 활용 (memory)
- "이 프로젝트의 기술 스택은 FastAPI라고 기억해줘 (memory_save)"
- "이전에 저장한 프로젝트 컨텍스트를 불러와줘 (memory_get)"

## 4. 확인 방법

- **백업**: 파일 수정 시 `{PROJECT_ROOT}/.glm_backups/`에 파일이 생기는지 확인하세요.
- **로그**: `glm_action_log` 도구를 호출하여 그동안의 작업 이력을 확인하세요.
- **토큰 사용량**: `ask_glm` 응답에 토큰 사용량이 포함됩니다.
