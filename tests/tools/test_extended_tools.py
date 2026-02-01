import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.models import ErrorCode

# 도구 함수 Import
from src.tools.dir_ops import glm_dir_list, DirListParams
from src.tools.code_ops import glm_code_run, CodeRunParams
from src.tools.web_ops import glm_web_search, WebSearchParams
from src.tools.git_ops import glm_git_status, GitStatusParams
from src.tools.http_ops import glm_http_request, HttpRequestParams
from src.tools.db_ops import glm_db_query, DbQueryParams
from src.tools.schedule_ops import glm_schedule_task, ScheduleTaskParams

@pytest.mark.asyncio
async def test_dir_list():
    # 현재 디렉토리 조회
    params = DirListParams(path=".")
    response = await glm_dir_list(params)
    assert response.success
    assert response.code == ErrorCode.SUCCESS
    assert "items" in response.data
    # requirements.txt가 있어야 함
    items = [item["name"] for item in response.data["items"]]
    assert "requirements.txt" in items

@pytest.mark.asyncio
async def test_code_run():
    code = "print('Hello ' + 'World')"
    params = CodeRunParams(code=code)
    response = await glm_code_run(params)
    assert response.success
    assert response.data["stdout"] == "Hello World"
    assert response.data["exit_code"] == 0

@pytest.mark.asyncio
async def test_web_search_mock():
    # DuckDuckGo Mocking
    with patch("src.tools.web_ops.DDGS") as MockDDGS:
        mock_instance = MockDDGS.return_value
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.text.return_value = [
            {"title": "Test Result", "href": "http://example.com", "body": "Test Body"}
        ]
        
        params = WebSearchParams(query="test")
        response = await glm_web_search(params)
        
        assert response.success
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Test Result"

@pytest.mark.asyncio
async def test_git_status():
    # Git 저장소이므로 status가 성공해야 함
    params = GitStatusParams()
    response = await glm_git_status(params)
    
    # git이 설치되어 있고 저장소라면 성공
    if response.success:
        assert "branch" in response.data
    else:
        # CI 환경 등 git이 없을 수 있음
        pytest.skip("Git execution failed")

@pytest.mark.asyncio
async def test_http_request():
    url = "https://www.google.com"
    params = HttpRequestParams(url=url, method="GET")
    response = await glm_http_request(params)
    
    if response.success:
        assert response.data["status"] == 200
    else:
        # 네트워크 문제 시 스킵
        pytest.skip(f"Network request failed: {response.message}")

@pytest.mark.asyncio
async def test_db_query():
    # 테스트용 DB
    db_path = "test_db.sqlite"
    
    try:
        # 테이블 생성
        params = DbQueryParams(db_path=db_path, query="CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
        await glm_db_query(params)
        
        # 데이터 삽입
        params = DbQueryParams(db_path=db_path, query="INSERT INTO test (name) VALUES (?)", params=["Test User"])
        await glm_db_query(params)
        
        # 조회
        params = DbQueryParams(db_path=db_path, query="SELECT * FROM test")
        response = await glm_db_query(params)
        
        assert response.success
        assert len(response.data["rows"]) >= 1
        assert response.data["rows"][0]["name"] == "Test User"
        
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

@pytest.mark.asyncio
async def test_schedule_task():
    # 작업 추가
    params = ScheduleTaskParams(action="add", name="Test Task", cron="* * * * *", command="echo test")
    response = await glm_schedule_task(params)
    assert response.success
    task_id = response.data["id"]
    
    # 목록 조회
    params = ScheduleTaskParams(action="list")
    response = await glm_schedule_task(params)
    assert response.success
    assert len(response.data["tasks"]) >= 1
    
    # 작업 삭제
    params = ScheduleTaskParams(action="remove", task_id=task_id)
    response = await glm_schedule_task(params)
    assert response.success
