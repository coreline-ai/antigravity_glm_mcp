# Repository Guidelines

## 프로젝트 구조 및 모듈 구성
- `src/server.py`가 MCP 도구를 등록하고 호출합니다. 새 도구는 `src/tools/`에 Pydantic 파라미터 모델과 `ToolResponse`를 함께 정의하세요.
- 공통 인프라(`config.py`, `sandbox.py`, `backup.py`, `glm_client.py`)는 `src/core/`에 있습니다. 경로 검증·백업·HTTP 로직을 재사용해 보안 일관성을 유지합니다.
- 문서는 `docs/`, 단위 테스트는 `tests/core/`와 `tests/tools/`, 통합 스모크는 `tests/local_tools_test.py`, `tests/simple_test.py`에 있습니다. 런타임 데이터는 `data/`와 `.glm_backups/`(git ignore)에 남습니다.

## 환경 및 설정
- Python 3.11+ 필요. 기본 설치: `python -m pip install -r requirements.txt`. 린트/테스트 추가 패키지: `python -m pip install -e .[dev]`.
- MCP 빠른 설정: `python scripts/install.py` 실행 후 `ZHIPU_API_KEY`, `PROJECT_ROOT`, 선택적 모델/베이스 URL을 입력합니다. 이미 설치했다면 `--skip-deps`로 건너뜁니다.
- 비밀 값은 `.env` 또는 로컬 MCP 설정에만 보관하고 저장소에 커밋하지 마세요.

## 빌드·실행·개발 명령
- 서버 수동 실행: `python src/server.py` (MCP 클라이언트와 함께 사용).
- 린트: `ruff check src tests` (`ruff`는 `dev` 익스트라에 포함).
- 패키징은 hatchling 기반이며 로컬 개발 시 추가 빌드 단계가 없습니다.

## 코딩 스타일 및 네이밍
- Python, 4-스페이스 인덴트, 타입 힌트 권장. 도구 입력은 Pydantic `BaseModel`+검증자를 사용하고 이름은 `glm_*` 패턴을 유지합니다.
- `ToolResponse`에 명확한 `code/message/data`를 채우고, 블로킹 대신 비동기 I/O(`asyncio.to_thread`, `httpx.AsyncClient`)를 선호합니다.
- `config.PROJECT_ROOT`와 `SandboxValidator`를 준수하며 하드코딩된 경로·비밀을 피합니다. 새 파라미터와 핸들러는 동일한 `*_ops.py`에 배치합니다.

## 테스트 가이드
- 빠른 단위 테스트: `python -m pytest tests/core tests/tools` (오프라인).
- 네트워크/API 확인: `python tests/local_tools_test.py`(웹 검색/HTTP), `python tests/simple_test.py`(GLM). 실행 전 `PROJECT_ROOT`, `ZHIPU_API_KEY`를 export 합니다.
- 비동기 테스트는 `@pytest.mark.asyncio`로 표시하고 HTTP·파일 I/O는 가급적 모킹해 결정성을 유지하세요.

## 커밋 및 PR 가이드
- 커밋은 짧은 명령형 제목, 이모지 선택 사항(예: `feat: tighten sandbox rollback`, `🚀 improve glm_cmd errors`). 한 커밋에 한 가지 변경만 담습니다.
- PR에는 동작 변화 요약, 연관 이슈, 실행한 테스트 명령, 설정/환경 영향 여부를 적습니다. 출력 형식/UI가 변할 때만 스크린샷을 첨부합니다.
- `.env`, `data/`, `.glm_backups/`, 생성 로그, API 키는 절대 커밋하지 마세요. 샌드박스·쉘·보안 변경 시 위험과 완화책을 설명합니다.

## 보안 및 데이터 처리
- 파일 작업은 반드시 `PROJECT_ROOT` 내에서 수행하고 원시 `Path` 대신 `SandboxValidator`와 `BackupManager`를 거칩니다.
- `glm_http_request`, `glm_shell_exec`의 SSRF/IP 차단과 화이트리스트를 유지하세요. 검토 없이 필터를 완화하지 않습니다.
- 수정/삭제 전에 자동 백업이 동작합니다. 복구는 수동 복사보다 `glm_file_rollback`으로 검증하세요.
