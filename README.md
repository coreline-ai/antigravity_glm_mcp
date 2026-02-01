# Gemini GLM Agent MCP

> Gemini (Antigravity)와 GLM-4-plus를 연결하는 MCP 서버

이 프로젝트는 Gemini가 GLM-4-plus 모델과 협업하여 복잡한 코딩 작업을 수행하고, 호스트 시스템의 파일을 안전하게 관리하며, 컨텍스트를 유지할 수 있도록 돕는 모델 컨텍스트 프로토콜(MCP) 서버입니다.

## ✨ 특징

- **Docker 불필요**: GLM API를 직접 호출하여 별도의 컨테이너 설정이 필요 없습니다
- **작업 위임**: `ask_glm` 도구를 통해 복잡한 작업을 GLM-4-plus에 전달하여 처리
- **파일 관리**: 호스트 시스템의 파일 읽기, 생성, 수정, 삭제 지원 (샌드박스 보안 적용)
- **자동 백업**: 파일 수정 및 삭제 전 `.glm_backups/` 폴더에 자동으로 원본 백업 생성
- **메모리 유지**: 세션 간 정보를 공유할 수 있는 메모리 강화 도구 제공
- **보안**: `PROJECT_ROOT` 기반의 경로 검증을 통해 외부 파일 접근 차단

## 📚 문서

상세한 아키텍처 및 도구 설명은 `docs/` 폴더를 참조하세요:

- [아키텍처 가이드](docs/ARCHITECTURE.md)
- [도구 참조](docs/TOOLS.md)
- [빠른 시작](docs/QUICKSTART.md)

## 🚀 빠른 시작

### 1. API 키 발급
[Zhipu AI 오픈 플랫폼](https://open.bigmodel.cn/)에서 API 키를 발급받으세요.

### 2. 자동 설치 (추천)
설정 과정을 자동으로 처리하는 스크립트를 제공합니다. 터미널에서 아래 명령어를 실행하세요:

```bash
python3 scripts/install.py
```

스크립트가 실행되면 다음 정보를 입력하면 됩니다:
- **API Key**: 발급받은 Zhipu AI 키
- **프로젝트 경로**: GLM이 작업할 대상 폴더 (엔터 치면 현재 폴더)

### 3. 수동 설정 (대안)
자동 설치가 안 되거나 직접 설정하고 싶다면 아래 방법을 따르세요.

#### MCP 설정 파일 수정
Gemini/Claude 데스크탑의 MCP 설정에 추가:

```json
{
  "mcpServers": {
    "gemini-glm-agent": {
      "command": "python",
      "args": ["src/server.py"],
      "cwd": "/path/to/gemini-glm-agent-mcp",
      "env": {
        "PROJECT_ROOT": "/path/to/your/project",
        "ZHIPU_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 3. 사용하기
Gemini 채팅창에서:
- "GLM에게 이 코드를 분석해달라고 해줘"
- "이 파일의 함수명을 변경해줘"

## 🔧 환경변수

| 변수명 | 필수 | 설명 |
|--------|------|------|
| `ZHIPU_API_KEY` | ✅ | Zhipu AI API 키 |
| `PROJECT_ROOT` | ✅ | 작업 대상 프로젝트 폴더 경로 |
| `GLM_MODEL` | ❌ | 사용할 모델 (기본: `glm-4-plus`) |
| `GLM_TIMEOUT` | ❌ | API 타임아웃 초 (기본: 120) |

## 📁 프로젝트 구조

```
gemini-glm-agent-mcp/
├── src/
│   ├── server.py          # MCP 서버 진입점
│   ├── core/
│   │   ├── glm_client.py   # GLM API 직접 호출 클라이언트
│   │   ├── glm_executor.py # 작업 실행기
│   │   ├── sandbox.py      # 경로 보안 검증
│   │   └── backup.py       # 자동 백업 관리
│   └── tools/
│       ├── ask_glm.py      # GLM 질문 위임
│       ├── file_ops.py     # 파일 작업
│       └── memory_ops.py   # 메모리 관리
├── docs/                   # 문서
└── tests/                  # 테스트
```

## 🧪 테스트

```bash
python3 -m pytest tests/
```

## 📄 라이선스

MIT License
