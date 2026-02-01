"""샌드박스 검증 모듈

파일 작업 시 경로 검증 및 보안 차단.
"""
from pathlib import Path
from typing import Union


class SandboxViolationError(Exception):
    """샌드박스 제약 위반 예외"""

    pass


# 금지된 패턴 목록
FORBIDDEN_PATTERNS = [
    ".env",  # 환경 변수 파일
    ".env.local",
    ".env.production",
    ".git/",  # .git 디렉토리 (단, .gitignore는 허용)
    "__pycache__/",  # Python 캐시
    "*.pyc",
    "*.pyo",
    ".DS_Store",  # macOS 파일
    "node_modules/",  # Node.js 종속성
]


class SandboxValidator:
    """샌드박스 경로 검증기

    프로젝트 폴더 내부로 파일 작업을 제한하고,
    위험한 패턴(Path Traversal, 민감 파일 등)을 차단합니다.
    """

    def __init__(self, project_root: Union[str, Path]):
        """초기화

        Args:
            project_root: 프로젝트 루트 디렉토리 (절대 경로)
        """
        self.project_root = Path(project_root).resolve()

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """경로 정규화

        상대 경로를 절대 경로로 변환하고, symlink를 해석합니다.

        Args:
            path: 검증할 경로 (상대 또는 절대)

        Returns:
            정규화된 절대 경로
        """
        path_obj = Path(path)

        # 상대 경로면 프로젝트 루트 기준으로 해석
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj

        # 경로 정규화 (.., symlink 해석)
        try:
            resolved = path_obj.resolve()
        except (OSError, RuntimeError):
            # resolve() 실패 시 (순환 symlink 등)
            resolved = path_obj.absolute()

        return resolved

    def validate_path(self, path: Union[str, Path]) -> bool:
        """경로가 샌드박스 내부인지 검증

        Args:
            path: 검증할 경로

        Returns:
            True (안전), False (위험)
        """
        try:
            resolved = self.resolve_path(path)

            # 1. 프로젝트 루트 내부인지 확인
            try:
                resolved.relative_to(self.project_root)
            except ValueError:
                # relative_to() 실패 = 프로젝트 외부
                return False

            # 2. 금지 패턴 확인
            if self.is_forbidden_pattern(str(resolved)):
                return False

            return True

        except Exception:
            # 예외 발생 시 보수적으로 차단
            return False

    def is_forbidden_pattern(self, path: Union[str, Path]) -> bool:
        """금지된 패턴인지 확인

        Args:
            path: 검증할 경로

        Returns:
            True (금지됨), False (허용됨)
        """
        path_str = str(path)

        for pattern in FORBIDDEN_PATTERNS:
            # 와일드카드 패턴
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if prefix in path_str:
                    return True
            # 디렉토리 패턴
            elif pattern.endswith("/"):
                dir_name = pattern[:-1]
                # .git/ 패턴이지만 .gitignore는 허용
                if dir_name == ".git" and path_str.endswith(".gitignore"):
                    continue
                if f"/{dir_name}/" in path_str or path_str.startswith(
                    dir_name + "/"
                ):
                    return True
            # 정확한 파일명 패턴
            else:
                if pattern in path_str:
                    return True

        return False
