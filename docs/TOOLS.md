# 도구 참조: Gemini GLM Agent MCP

이 문서는 `gemini-glm-agent-mcp` 서버에서 사용 가능한 11개의 도구를 나열합니다.

## 질문 위임

### `ask_glm`
복잡한 작업을 GLM-4-plus에 위임하여 처리합니다.
- **입력**: `task_description` (문자열), `context` (선택적 문자열), `working_dir` (선택적 문자열).
- **출력**: GLM으로부터 처리된 결과.

## 파일 작업

모든 파일 작업은 호스트 시스템에서 수행됩니다.

### `glm_file_read`
파일의 내용을 읽습니다.
- **입력**: `path` (문자열), `encoding` (선택적 문자열).

### `glm_file_create`
새 파일을 생성합니다.
- **입력**: `path` (문자열), `content` (문자열), `overwrite` (불리언).

### `glm_file_edit`
파일에서 특정 문자열을 수정합니다.
- **입력**: `path` (문자열), `old_string` (문자열), `new_string` (문자열).
- **참고**: 수정 전 자동으로 백업을 생성합니다.

### `glm_file_delete`
파일을 삭제합니다.
- **입력**: `path` (문자열).
- **참고**: 삭제 전 자동으로 백업을 생성합니다.

### `glm_file_rollback`
이전 백업에서 파일을 복원합니다.
- **입력**: `path` (문자열), `version` (정수, 최신 버전은 -1).

## 메모리 관리

### `glm_memory_save`
세션 간에 공유할 컨텍스트 또는 정보를 저장합니다.
- **입력**: `key` (문자열), `value` (문자열), `category` (문자열).

### `glm_memory_get`
특정 메모리 항목을 검색합니다.
- **입력**: `key` (문자열).

### `glm_memory_list`
저장된 모든 메모리를 나열합니다.
- **입력**: `category` (선택적 문자열).

### `glm_memory_delete`
특정 메모리 항목을 삭제합니다.
- **입력**: `key` (문자열).

## 로깅

### `glm_action_log`
GLM 에이전트가 수행한 작업 로그를 검색합니다.
- **입력**: `limit` (선택적 정수).
