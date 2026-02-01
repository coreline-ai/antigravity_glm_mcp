"""파일 백업 관리자

파일 수정/삭제 전 자동 백업 생성 및 버전 관리.
- 원자적 쓰기 (temp → rename)
- 최대 버전 관리 (기본 10개)
- 오래된 버전 자동 정리
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from src.models import BackupInfo


class BackupManager:
    """파일 백업 관리자

    파일 변경 전 자동으로 백업을 생성하고 버전을 관리합니다.
    """

    def __init__(self, backup_dir: Path, max_versions: int = 10):
        """
        Args:
            backup_dir: 백업 저장 디렉토리
            max_versions: 파일당 최대 백업 버전 수
        """
        self.backup_dir = Path(backup_dir)
        self.max_versions = max_versions
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_backup_filename(self, file_path: Path, version: int) -> str:
        """백업 파일명 생성

        형식: {원본파일명}.{타임스탬프}.{버전}.bak

        Args:
            file_path: 원본 파일 경로
            version: 버전 번호

        Returns:
            백업 파일명
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{file_path.name}.{timestamp}.{version}.bak"

    def _parse_backup_filename(self, backup_filename: str) -> tuple[str, datetime, int]:
        """백업 파일명 파싱

        Args:
            backup_filename: 백업 파일명

        Returns:
            (원본파일명, 생성시각, 버전번호)
        """
        parts = backup_filename.rsplit(".", 3)  # 뒤에서부터 3개 분리
        if len(parts) != 4:
            raise ValueError(f"잘못된 백업 파일명: {backup_filename}")

        original_name = parts[0]
        timestamp_str = parts[1]
        version = int(parts[2])

        created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        return original_name, created_at, version

    async def create_backup(self, file_path: Path) -> str:
        """파일 백업 생성 (원자적 쓰기)

        Args:
            file_path: 백업할 파일 경로

        Returns:
            생성된 백업 파일 전체 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 현재 백업 목록 조회
        existing_backups = await self.list_backups(file_path)
        next_version = len(existing_backups) + 1

        # 백업 파일명 생성
        backup_filename = self._get_backup_filename(file_path, next_version)
        backup_path = self.backup_dir / backup_filename
        temp_path = self.backup_dir / f"{backup_filename}.tmp"

        # 원자적 쓰기: temp 파일 → rename
        await asyncio.to_thread(shutil.copy2, file_path, temp_path)
        await asyncio.to_thread(temp_path.rename, backup_path)

        # 버전 정리
        await self._cleanup_old_versions(file_path)

        return str(backup_path)

    async def restore_backup(self, file_path: Path, version: int = -1) -> bool:
        """백업에서 복원

        Args:
            file_path: 복원할 파일 경로
            version: 복원할 버전 (인덱스 기반, -1은 최신)

        Returns:
            성공 여부
        """
        file_path = Path(file_path)
        backups = await self.list_backups(file_path)

        if not backups:
            return False

        # 버전 인덱스 처리
        try:
            backup_to_restore = backups[version]
        except IndexError:
            return False

        # 원자적 쓰기로 복원
        backup_path = Path(backup_to_restore.backup_path)
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

        try:
            await asyncio.to_thread(shutil.copy2, backup_path, temp_path)
            await asyncio.to_thread(temp_path.rename, file_path)
            return True
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            return False

    async def list_backups(self, file_path: Path) -> list[BackupInfo]:
        """백업 목록 조회 (최신순 정렬)

        Args:
            file_path: 원본 파일 경로

        Returns:
            백업 정보 리스트 (최신순)
        """
        file_path = Path(file_path)
        pattern = f"{file_path.name}.*.*.bak"

        backups = []
        for backup_file in self.backup_dir.glob(pattern):
            try:
                original_name, created_at, version = self._parse_backup_filename(backup_file.name)
                size_bytes = backup_file.stat().st_size

                backup_info = BackupInfo(
                    file_path=str(file_path),
                    backup_path=str(backup_file),
                    version=version,
                    created_at=created_at,
                    size_bytes=size_bytes,
                )
                backups.append(backup_info)
            except (ValueError, IndexError):
                # 잘못된 파일명은 무시
                continue

        # 최신순 정렬 (version 번호 기준 내림차순 - 더 안정적)
        backups.sort(key=lambda b: b.version, reverse=True)
        return backups

    async def _cleanup_old_versions(self, file_path: Path):
        """오래된 백업 버전 정리

        최대 버전 수를 초과하면 가장 오래된 버전부터 삭제.

        Args:
            file_path: 원본 파일 경로
        """
        backups = await self.list_backups(file_path)

        # 최대 버전 초과 시 오래된 것부터 삭제
        if len(backups) > self.max_versions:
            to_delete = backups[self.max_versions :]  # 인덱스 초과분
            for backup in to_delete:
                backup_path = Path(backup.backup_path)
                if backup_path.exists():
                    await asyncio.to_thread(backup_path.unlink)
