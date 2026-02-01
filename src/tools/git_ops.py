"""
git_ops.py - Git 통합 도구

Git 저장소 상태를 조회하고 변경사항을 커밋합니다.
"""

import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator

class GitStatusParams(BaseModel):
    """Git 상태 조회 파라미터"""
    repo_path: Optional[str] = Field(None, description="저장소 경로 (기본값: 현재 프로젝트 루트)")

class GitCommitParams(BaseModel):
    """Git 커밋 파라미터"""
    message: str = Field(..., description="커밋 메시지")
    add_all: bool = Field(True, description="커밋 전 모든 변경사항 스테이징 여부 (git add -A)")
    repo_path: Optional[str] = Field(None, description="저장소 경로 (기본값: 현재 프로젝트 루트)")

async def run_git_command(args: List[str], cwd: Optional[str] = None) -> str:
    process = await asyncio.create_subprocess_exec(
        "git", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"Git command failed: {stderr.decode().strip()}")
        
    return stdout.decode().strip()

async def glm_git_status(params: GitStatusParams) -> ToolResponse:
    try:
        # 안전한 경로 검증
        if params.repo_path:
            validator = get_sandbox_validator()
            if not validator.validate_path(params.repo_path):
                 return ToolResponse(
                    success=False,
                    code=ErrorCode.SANDBOX_VIOLATION,
                    message=f"저장소 경로 접근 차단됨 (샌드박스 위반): {params.repo_path}"
                )

        # 1. 브랜치 확인
        branch = await run_git_command(["branch", "--show-current"], cwd=params.repo_path)
        
        # 2. 변경사항 확인 (요약)
        status_porcelain = await run_git_command(["status", "--porcelain"], cwd=params.repo_path)
        
        files = []
        if status_porcelain:
            for line in status_porcelain.splitlines():
                if len(line) > 3:
                    files.append({
                        "status": line[:2],
                        "path": line[3:]
                    })

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"Git 상태 조회 성공 ({branch})",
            data={
                "branch": branch,
                "changed_count": len(files),
                "changes": files
            }
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Git 상태 조회 실패: {str(e)}"
        )

async def glm_git_commit(params: GitCommitParams) -> ToolResponse:
    try:
        # 안전한 경로 검증
        if params.repo_path:
            validator = get_sandbox_validator()
            if not validator.validate_path(params.repo_path):
                 return ToolResponse(
                    success=False,
                    code=ErrorCode.SANDBOX_VIOLATION,
                    message=f"저장소 경로 접근 차단됨 (샌드박스 위반): {params.repo_path}"
                )

        # 1. 스테이징
        if params.add_all:
            await run_git_command(["add", "-A"], cwd=params.repo_path)
            
        # 2. 커밋
        await run_git_command(["commit", "-m", params.message], cwd=params.repo_path)
        
        # 3. 결과 확인 (마지막 커밋 로그)
        log = await run_git_command(["log", "-1", "--oneline"], cwd=params.repo_path)

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message="Git 커밋 성공",
            data={
                "commit_log": log
            }
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Git 커밋 실패: {str(e)}"
        )


class GitLogParams(BaseModel):
    """Git 로그 조회 파라미터"""
    n: int = Field(10, description="조회할 커밋 수 (기본값: 10)")
    oneline: bool = Field(True, description="한 줄 요약 형식")
    repo_path: Optional[str] = Field(None, description="저장소 경로 (기본값: 현재 프로젝트 루트)")


class GitDiffParams(BaseModel):
    """Git diff 파라미터"""
    ref: Optional[str] = Field(None, description="비교 대상 (예: 'HEAD~1', 'main', 커밋 해시). 미지정 시 스테이징 변경사항 표시")
    file_path: Optional[str] = Field(None, description="특정 파일만 비교 (옵션)")
    stat_only: bool = Field(False, description="변경 통계만 표시")
    repo_path: Optional[str] = Field(None, description="저장소 경로 (기본값: 현재 프로젝트 루트)")


async def glm_git_log(params: GitLogParams) -> ToolResponse:
    """Git 커밋 이력 조회"""
    try:
        # 안전한 경로 검증
        if params.repo_path:
            validator = get_sandbox_validator()
            if not validator.validate_path(params.repo_path):
                return ToolResponse(
                    success=False,
                    code=ErrorCode.SANDBOX_VIOLATION,
                    message=f"저장소 경로 접근 차단됨 (샌드박스 위반): {params.repo_path}"
                )

        # 로그 포맷 설정
        if params.oneline:
            log_format = "--oneline"
        else:
            log_format = "--format=%H|%an|%ae|%s|%ci"
        
        log_output = await run_git_command(
            ["log", f"-{params.n}", log_format],
            cwd=params.repo_path
        )
        
        commits = []
        if log_output:
            for line in log_output.splitlines():
                if params.oneline:
                    parts = line.split(" ", 1)
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1] if len(parts) > 1 else ""
                    })
                else:
                    parts = line.split("|")
                    if len(parts) >= 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "message": parts[3],
                            "date": parts[4]
                        })

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"Git 로그 조회 성공: {len(commits)}개 커밋",
            data={
                "count": len(commits),
                "commits": commits
            }
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Git 로그 조회 실패: {str(e)}"
        )


async def glm_git_diff(params: GitDiffParams) -> ToolResponse:
    """Git 변경 사항 비교"""
    try:
        # 안전한 경로 검증
        if params.repo_path:
            validator = get_sandbox_validator()
            if not validator.validate_path(params.repo_path):
                return ToolResponse(
                    success=False,
                    code=ErrorCode.SANDBOX_VIOLATION,
                    message=f"저장소 경로 접근 차단됨 (샌드박스 위반): {params.repo_path}"
                )

        args = ["diff"]
        
        if params.stat_only:
            args.append("--stat")
        
        if params.ref:
            args.append(params.ref)
        
        if params.file_path:
            args.extend(["--", params.file_path])
        
        diff_output = await run_git_command(args, cwd=params.repo_path)
        
        # diff 통계 요약
        additions = 0
        deletions = 0
        files_changed = set()
        
        for line in diff_output.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                if not line.endswith("/dev/null"):
                    path = line[4:].strip()
                    if path.startswith("b/") or path.startswith("a/"):
                        path = path[2:]
                    files_changed.add(path)
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"Git diff 조회 성공: {len(files_changed)}개 파일, +{additions}/-{deletions}",
            data={
                "ref": params.ref or "staged",
                "files_changed": len(files_changed),
                "additions": additions,
                "deletions": deletions,
                "diff": diff_output if not params.stat_only else None,
                "stat": diff_output if params.stat_only else None
            }
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Git diff 조회 실패: {str(e)}"
        )
