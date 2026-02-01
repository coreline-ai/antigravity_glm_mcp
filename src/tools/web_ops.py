"""
web_ops.py - 웹 검색 도구

DuckDuckGo 검색 엔진을 활용하여 웹 정보를 검색합니다.
"""

import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field

# DuckDuckGo 라이브러리 (설치 필요)
try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False

from src.models import ErrorCode, ToolResponse

class WebSearchParams(BaseModel):
    """웹 검색 파라미터"""
    query: str = Field(..., description="검색어")
    max_results: int = Field(5, description="최대 결과 개수 (기본 5)")

async def glm_web_search(params: WebSearchParams) -> ToolResponse:
    if not HAS_DDG:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message="duckduckgo-search 라이브러리가 설치되지 않았습니다. 'pip install duckduckgo-search'를 실행해주세요."
        )

    try:
        # 동기 라이브러리 블로킹 방지를 위해 별도 스레드에서 실행
        def run_search():
            search_results = []
            with DDGS() as ddgs:
                for r in ddgs.text(params.query, max_results=params.max_results):
                    search_results.append({
                        "title": r.get("title"),
                        "href": r.get("href"),
                        "body": r.get("body")
                    })
            return search_results

        results = await asyncio.to_thread(run_search)

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message=f"검색 완료: {len(results)}건",
            data={
                "query": params.query,
                "results": results
            }
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"웹 검색 실패: {str(e)}"
        )
