import pytest
from django.urls import reverse
from rest_framework import status
from test_manager.models import Project, TestSuite, TestCase, TestSession, TestExecution


@pytest.fixture
def project(db):
    return Project.objects.create(name="Test Project")


@pytest.fixture
def test_suite(db, project):
    return TestSuite.objects.create(project=project, name="Test Suite")


@pytest.fixture
def test_case(db, test_suite):
    return TestCase.objects.create(suite=test_suite, title="Test Case")


from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from rest_framework.test import APIClient


@pytest.fixture
def api_client(db):
    user = User.objects.create_user(username="testuser", password="testpassword")
    token = Token.objects.create(user=user)
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


def test_get_project_list(api_client, project):
    url = reverse("project-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Test Project"


def test_get_project_test_suite_list(api_client, project, test_suite):
    url = reverse("project-test-suite-list", kwargs={"project_id": project.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Test Suite"


def test_get_project_test_suite_list_with_test_cases(
    api_client, project, test_suite, test_case
):
    url = (
        reverse("project-test-suite-list", kwargs={"project_id": project.id})
        + "?include_cases=true"
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Test Suite"
    assert len(response.data[0]["test_cases"]) == 1
    assert response.data[0]["test_cases"][0]["title"] == "Test Case"
