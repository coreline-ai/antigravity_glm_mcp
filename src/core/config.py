"""설정 모듈
프로젝트 전반의 설정과 경로 상수를 중앙에서 관리합니다.
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    def __init__(self):
        self._project_root: Optional[Path] = None

    @property
    def PROJECT_ROOT(self) -> Path:
        """프로젝트 루트 디렉토리"""
        if self._project_root:
            return self._project_root
            
        root = os.getenv("PROJECT_ROOT")
        if not root:
             self._project_root = Path(os.getcwd())
        else:
             self._project_root = Path(root).resolve()
        return self._project_root

    @property
    def DATA_DIR(self) -> Path:
        """데이터 저장 디렉토리"""
        return self.PROJECT_ROOT / "data"

    @property
    def BACKUP_DIR(self) -> Path:
        """백업 디렉토리"""
        return self.PROJECT_ROOT / ".glm_backups"

    @property
    def LOG_FILE(self) -> Path:
        """작업 로그 파일"""
        return self.DATA_DIR / "action_logs.jsonl"

    @property
    def SCHEDULE_FILE(self) -> Path:
        """예약 작업 파일"""
        return self.DATA_DIR / "schedule.json"

    @property
    def ZHIPU_API_KEY(self) -> Optional[str]:
        """ZhipuAI API 키"""
        return os.getenv("ZHIPU_API_KEY")

    @property
    def GLM_MODEL(self) -> str:
        """GLM 모델명"""
        return os.getenv("GLM_MODEL", "glm-4-plus")

    @property
    def GLM_TIMEOUT(self) -> int:
        """API 요청 타임아웃 (초)"""
        return int(os.getenv("GLM_TIMEOUT", "120"))

    @property
    def GLM_BASE_URL(self) -> str:
        """API 베이스 URL"""
        return os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

    @property
    def MEMORY_DIR(self) -> Path:
        """메모리 저장 디렉토리"""
        return self.DATA_DIR / "memory"

# 싱글톤 인스턴스
config = Config()
