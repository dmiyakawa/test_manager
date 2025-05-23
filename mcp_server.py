import datetime
from logging import DEBUG, INFO, Formatter, FileHandler, getLogger

import requests
from mcp.server.fastmcp import FastMCP

API_TOKEN = "db295f9804e905c3106fc68bab8c13e1c12777a7"
DJANGO_API_BASE_URL = "http://localhost:8888"  # Consider making this an env variable

logger = getLogger(__name__)
handler = FileHandler("./mcp.log")
logger.addHandler(handler)
logger.setLevel(DEBUG)
handler.setLevel(DEBUG)
handler.setFormatter(Formatter("%(asctime)s %(levelname)7s %(message)s"))

mcp = FastMCP("Test Manager on MCP")


@mcp.resource("tm://projects")
def get_projects():
    """シナリオテストのプロジェクト一覧を取得する"""
    logger.debug("get_projects()")

    api_url = f"{DJANGO_API_BASE_URL}/api/projects/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        # Raise HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()
        return response.json()
    except RuntimeError as e:
        return {"error": f"Failed to fetch projects: {str(e)}"}


@mcp.resource("tm://test_sessions/{project_id}")
def get_test_sessions(project_id):
    """指定したプロジェクトIDのテストセッション一覧を取得する"""
    logger.debug(f"get_test_sessions(project_id: {project_id})")

    api_url = f"{DJANGO_API_BASE_URL}/api/projects/{project_id}/test-sessions/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        return response.json()
    except RuntimeError as e:
        return {"error": f"Failed to fetch projects: {str(e)}"}


@mcp.resource("tm://test_executions/{session_id}")
def get_test_execution_detail(session_id: int):
    """指定したテストセッションのテスト実行状況を取得する"""
    logger.debug(f"get_test_execution_detail(session_id: {session_id})")

    api_url = f"{DJANGO_API_BASE_URL}/api/test-sessions/{session_id}/execute/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        return response.json()
    except RuntimeError as e:
        return {"error": f"Failed to fetch projects: {str(e)}"}



@mcp.tool()
def create_new_test_session(project_id: int, session_name: str = None) -> int:
    """指定したプロジェクトに対して新しいテストセッションを作成して、そのテストセッションのIDを得る"""
    if not session_name:
        now = datetime.datetime.now()
        session_name = "MCPセッション {}".format(now.strftime("%Y-%m-%d %H:%M"))
    logger.debug(f"create_new_session(project_id: {project_id}, session_name: {session_name})")

    api_url = f"{DJANGO_API_BASE_URL}/api/projects/{project_id}/test-sessions/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    try:
        data = {
            "project": project_id,
            "name": session_name,
            "description": "Description",
            "executed_by": "testuser",
            "environment": "Test Env",
        }
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        # Raise HTTPError for bad responses (4xx or 5xx)
        # response.raise_for_status()
        return response.json()
    except RuntimeError as e:
        return {"error": f"Failed to fetch projects: {str(e)}"}
        return response.json()
    except RuntimeError as e:
        return {"error": f"Failed to fetch projects: {str(e)}"}
