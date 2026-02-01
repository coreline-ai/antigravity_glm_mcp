# 도구 참조: Antigravity GLM MCP

> 이 문서는 `antigravity_glm_mcp` 서버에서 사용 가능한 **25개 도구**를 상세히 설명합니다.

---

## 📋 도구 목록 요약

| 카테고리 | 도구 수 | 도구 목록 |
|----------|---------|-----------|
| 지능 위임 | 3 | `glm_cmd`, `glm_bypass`, `glm_image_analyze` |
| 파일 관리 | 7 | `glm_file_*`, `glm_dir_list`, `glm_grep` |
| 코드/쉘 | 2 | `glm_code_run`, `glm_shell_exec` |
| Git 협업 | 4 | `glm_git_*` |
| 네트워크 | 2 | `glm_http_request`, `glm_web_search` |
| 메모리 | 4 | `glm_memory_*` |
| 고급 | 3 | `glm_db_query`, `glm_schedule_task`, `glm_action_log` |

---

## 🤖 지능 위임

### `glm_cmd`
복잡한 작업을 GLM-4-plus에 위임하여 처리합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `task_description` | string | ✅ | 위임할 작업 설명 |
| `context` | string | ❌ | 추가 컨텍스트 (코드, 파일 내용 등) |
| `working_dir` | string | ❌ | 작업 디렉토리 경로 |

### `glm_bypass`
GLM에 원시 프롬프트를 직접 전송합니다 (Raw Mode).

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `prompt` | string | ✅ | GLM에 보낼 원시 프롬프트 |

### `glm_image_analyze`
이미지를 분석합니다 (Vision).

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `image_path` | string | ✅ | 분석할 이미지 경로 |
| `prompt` | string | ❌ | 분석 요청 프롬프트 (기본: "Describe this image") |

---

## 📁 파일 관리

### `glm_file_read`
파일의 내용을 읽습니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 읽을 파일 경로 |
| `encoding` | string | ❌ | 인코딩 (기본: utf-8) |

### `glm_file_create`
새 파일을 생성합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 생성할 파일 경로 |
| `content` | string | ✅ | 파일 내용 |
| `overwrite` | boolean | ❌ | 기존 파일 덮어쓰기 (기본: false) |

### `glm_file_edit`
파일에서 특정 문자열을 수정합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 수정할 파일 경로 |
| `old_string` | string | ✅ | 찾을 문자열 |
| `new_string` | string | ✅ | 바꿀 문자열 |

> [!NOTE]
> 수정 전 자동으로 `.glm_backups/`에 백업이 생성됩니다.

### `glm_file_delete`
파일을 삭제합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 삭제할 파일 경로 |

> [!NOTE]
> 삭제 전 자동으로 백업이 생성됩니다.

### `glm_file_rollback`
이전 백업에서 파일을 복원합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 복원할 파일 경로 |
| `version` | integer | ❌ | 복원할 버전 (-1: 최신) |

### `glm_dir_list`
디렉토리의 파일 및 하위 폴더 목록을 조회합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `path` | string | ✅ | 조회할 디렉토리 경로 |
| `recursive` | boolean | ❌ | 하위 디렉토리 포함 (기본: false) |
| `only_directories` | boolean | ❌ | 디렉토리만 조회 (기본: false) |

### `glm_grep`
파일 내용에서 패턴을 검색합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `pattern` | string | ✅ | 검색 패턴 (정규식 지원) |
| `path` | string | ❌ | 검색 시작 경로 (기본: 프로젝트 루트) |
| `recursive` | boolean | ❌ | 하위 디렉토리 포함 (기본: true) |
| `file_pattern` | string | ❌ | 파일 필터 (예: `*.py`) |
| `case_sensitive` | boolean | ❌ | 대소문자 구분 (기본: true) |
| `max_results` | integer | ❌ | 최대 결과 수 (기본: 100) |
| `context_lines` | integer | ❌ | 컨텍스트 라인 수 (기본: 0) |

---

## 💻 코드 및 쉘 실행

### `glm_code_run`
Python 코드를 샌드박스에서 실행합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `code` | string | ✅ | 실행할 Python 코드 |
| `timeout` | integer | ❌ | 실행 제한 시간 (기본: 10초) |

> [!IMPORTANT]
> 환경변수가 필터링되어 API 키 유출이 방지됩니다.

### `glm_shell_exec`
제한적 쉘 명령을 실행합니다 (화이트리스트 기반).

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `command` | string | ✅ | 실행할 명령어 |
| `cwd` | string | ❌ | 작업 디렉토리 |
| `timeout` | integer | ❌ | 실행 제한 시간 (기본: 60초, 최대: 300초) |

**허용 명령어**: `pip`, `npm`, `yarn`, `python`, `node`, `ls`, `cat`, `grep`, `find`, `echo`, `curl`, `make` 등

> [!CAUTION]
> `rm -rf`, `sudo`, `curl | sh` 등 위험한 명령은 원천 차단됩니다.

---

## 🌿 Git 협업

### `glm_git_status`
Git 상태를 조회합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `repo_path` | string | ❌ | 저장소 경로 (기본: 프로젝트 루트) |

### `glm_git_commit`
변경사항을 커밋합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `message` | string | ✅ | 커밋 메시지 |
| `add_all` | boolean | ❌ | 모든 변경사항 스테이징 (기본: true) |
| `repo_path` | string | ❌ | 저장소 경로 |

### `glm_git_log`
커밋 이력을 조회합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `n` | integer | ❌ | 조회할 커밋 수 (기본: 10) |
| `oneline` | boolean | ❌ | 한 줄 요약 형식 (기본: true) |
| `repo_path` | string | ❌ | 저장소 경로 |

### `glm_git_diff`
변경 사항을 비교합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `ref` | string | ❌ | 비교 대상 (예: `HEAD~1`, `main`) |
| `file_path` | string | ❌ | 특정 파일만 비교 |
| `stat_only` | boolean | ❌ | 통계만 표시 (기본: false) |
| `repo_path` | string | ❌ | 저장소 경로 |

---

## 🌐 네트워크

### `glm_http_request`
HTTP 요청을 수행합니다 (SSRF 방지 적용).

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `url` | string | ✅ | 요청 URL |
| `method` | string | ❌ | HTTP 메소드 (기본: GET) |
| `headers` | object | ❌ | HTTP 헤더 |
| `body` | any | ❌ | 요청 본문 |
| `timeout` | integer | ❌ | 타임아웃 (기본: 30초) |

> [!IMPORTANT]
> 내부망 IP (127.0.0.1, 169.254.169.254 등)로의 요청은 차단됩니다.

### `glm_web_search`
DuckDuckGo를 통해 웹 검색을 수행합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✅ | 검색어 |
| `max_results` | integer | ❌ | 최대 결과 수 (기본: 5) |

---

## 🧠 메모리 관리

### `glm_memory_save`
세션 간 공유할 정보를 저장합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `key` | string | ✅ | 메모리 키 |
| `value` | string | ✅ | 저장할 값 |
| `category` | string | ❌ | 카테고리 (기본: general) |
| `ttl_hours` | integer | ❌ | 만료 시간 (시간) |

### `glm_memory_get`
저장된 메모리를 조회합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `key` | string | ✅ | 메모리 키 |

### `glm_memory_list`
저장된 모든 메모리를 나열합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `category` | string | ❌ | 카테고리 필터 |
| `limit` | integer | ❌ | 최대 개수 (기본: 20) |

### `glm_memory_delete`
메모리를 삭제합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `key` | string | ✅ | 삭제할 메모리 키 |

---

## 🔧 고급 기능

### `glm_db_query`
SQLite 데이터베이스 쿼리를 실행합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✅ | SQL 쿼리문 |
| `db_path` | string | ❌ | DB 파일 경로 |
| `params` | array | ❌ | 쿼리 파라미터 |
| `read_only` | boolean | ❌ | 읽기 전용 모드 (기본: false) |

### `glm_schedule_task`
작업 예약을 관리합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `action` | string | ✅ | 동작: add, list, remove |
| `name` | string | ❌ | 작업 이름 |
| `cron` | string | ❌ | cron 표현식 |
| `command` | string | ❌ | 실행할 명령어 |
| `task_id` | string | ❌ | 삭제할 작업 ID |

### `glm_action_log`
에이전트가 수행한 작업 로그를 조회합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `limit` | integer | ❌ | 조회할 로그 수 (기본: 20) |
| `offset` | integer | ❌ | 시작 오프셋 |
| `action_filter` | string | ❌ | 액션 타입 필터 |
