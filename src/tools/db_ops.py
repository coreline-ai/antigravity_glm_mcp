"""
db_ops.py - 데이터베이스 작업 도구

SQLite 데이터베이스에 쿼리를 실행합니다.
"""

import sqlite3
import json
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator

class DbQueryParams(BaseModel):
    """DB 쿼리 파라미터"""
    db_path: str = Field("data/app.db", description="SQLite DB 파일 경로")
    query: str = Field(..., description="SQL 쿼리문")
    params: Optional[List[Any]] = Field(None, description="쿼리 파라미터 (?)")
    read_only: bool = Field(False, description="읽기 전용 모드 여부")

async def glm_db_query(params: DbQueryParams) -> ToolResponse:
    try:
        # 샌드박스 검증
        validator = get_sandbox_validator()
        if not validator.validate_path(params.db_path):
            return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"DB 파일 접근 차단됨 (샌드박스 위반): {params.db_path}"
            )

        # DB 연결 (컨텍스트 매니저 사용)
        # check_same_thread=False는 비동기 환경에서 필요할 수 있음
        with sqlite3.connect(params.db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row  # 딕셔너리처럼 접근 가능
            cursor = conn.cursor()
            
            # 실행
            if params.params:
                cursor.execute(params.query, params.params)
            else:
                cursor.execute(params.query)
            
            result_data = None
            affected_rows = 0
            
            # SELECT 문인 경우 결과 반환
            if params.query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                result_data = [dict(row) for row in rows]
            else:
                if params.read_only:
                    return ToolResponse(
                        success=False,
                        code=ErrorCode.INVALID_PARAMS,
                        message="읽기 전용 모드에서는 SELECT 문만 허용됩니다."
                    )
                conn.commit()
                affected_rows = cursor.rowcount

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message="쿼리 실행 성공",
            data={
                "rows": result_data,
                "affected_rows": affected_rows
            }
        )

    except sqlite3.Error as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"DB 오류: {str(e)}"
        )
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"예기치 않은 오류: {str(e)}"
        )
