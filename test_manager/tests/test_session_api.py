import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from test_manager.models import Project, TestSuite, TestCase, TestSession, TestExecution
import json


@pytest.fixture
def project(db):
    return Project.objects.create(name="Test Project")


@pytest.fixture
def test_suite(db, project):
    return TestSuite.objects.create(project=project, name="Test Suite")


@pytest.fixture
def test_case(db, test_suite):
    return TestCase.objects.create(suite=test_suite, title="Test Case")


@pytest.fixture
def api_client(db):
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = Token.objects.create(user=user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


def test_create_test_session(api_client, project, test_suite):
    url = reverse("test-session-create")
    data = {
        "project": project.id,
        "name": "Test Session 1",
        "description": "Test Description",
        "executed_by": "testuser",
        "environment": "Test Env",
        "available_suites": [test_suite.id],
    }
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Test Session 1"
    assert response.data["description"] == "Test Description"
    assert TestSession.objects.count() == 1
    test_session = TestSession.objects.first()
    assert test_session.executions.count() == 1


def test_create_test_session_without_available_suites(api_client, project):
    url = reverse("test-session-create")
    data = {
        "project": project.id,
        "name": "Test Session 1",
        "description": "Test Description",
        "executed_by": "testuser",
        "environment": "Test Env",
    }
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_execute_test_case(api_client, project, test_suite, test_case):
    """TestExecutionのGET APIをテストする。"""
    test_session = TestSession.objects.create(project=project, name="Test Session")
    test_session.available_suites.add(test_suite)
    execution = TestExecution.objects.create(
        test_session=test_session, test_case=test_case
    )
    url = reverse("execute-test-case", kwargs={"test_session_id": test_session.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["test_session_id"] == test_session.id
    assert "remaining_test_cases" in response_data


def test_execute_test_case_completion(api_client, project, test_suite, test_case):
    """1件のテストケースがあるTestExecutionでその1件をPASSで完了させた際のテスト"""
    test_session = TestSession.objects.create(
        project=project,
        name="Test Session 1",
        executed_by="testuser",
        environment="Test Env",
    )
    test_session.available_suites.add(test_suite)
    execution = TestExecution.objects.create(
        test_session=test_session, test_case=test_case
    )
    execution_url = reverse(
        "execute-test-case", kwargs={"test_session_id": test_session.id}
    )

    # GETして1件残っていることを確認する
    response = api_client.get(execution_url)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["test_session_id"] == test_session.id
    assert "remaining_test_cases" in response_data
    assert len(response_data["remaining_test_cases"]) == 1
    assert response_data["remaining_test_cases"][0]["id"] == test_case.id

    # 対象の1件をPASSで完了とする
    data = {
        "test_case_id": test_case.id,
        "status": "PASS",
        "result_detail": "Test Result",
        "notes": "Test Notes",
    }
    response = api_client.post(
        execution_url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_200_OK

    execution = TestExecution.objects.get(
        test_session=test_session, test_case=test_case
    )
    assert execution.status == "PASS"
    assert execution.result_detail == "Test Result"
    assert execution.notes == "Test Notes"

    response = api_client.get(execution_url)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["test_session_id"] == test_session.id
    assert "remaining_test_cases" in response_data
    assert len(response_data["remaining_test_cases"]) == 0


def test_get_execute_test_case_not_found(api_client, project, test_suite, test_case):
    url = reverse("execute-test-case", kwargs={"test_session_id": 999})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_post_execute_test_case_api_not_found(
    api_client, project, test_suite, test_case
):
    url = reverse("execute-test-case", kwargs={"test_session_id": 999})
    data = {
        "test_case_id": test_case.id,
        "status": "PASS",
        "result_detail": "Test Result",
        "notes": "Test Notes",
    }
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
