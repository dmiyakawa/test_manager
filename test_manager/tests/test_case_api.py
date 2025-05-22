import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from test_manager.models import TestCase, TestStep, TestSuite, Project
from django.contrib.auth.models import User
from test_manager.serializers import TestCaseSerializer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def project(db):
    return Project.objects.create(name="Test Project")


@pytest.fixture
def test_suite(db, project):
    return TestSuite.objects.create(project=project, name="Test Suite")


@pytest.fixture
def test_case(db, test_suite):
    return TestCase.objects.create(
        suite=test_suite, title="Test Case Title", description="Test Case Description"
    )


@pytest.fixture
def test_steps(db, test_case):
    steps = [
        TestStep.objects.create(
            test_case=test_case,
            order=1,
            description="Step 1 Description",
            expected_result="Step 1 Expected Result",
        ),
        TestStep.objects.create(
            test_case=test_case,
            order=2,
            description="Step 2 Description",
            expected_result="Step 2 Expected Result",
        ),
    ]
    return steps


@pytest.mark.django_db
def test_get_test_case_detail_authenticated(
    api_client, test_case, test_steps, project, test_suite, user
):
    api_client.force_authenticate(user=user)
    url = reverse("testcase-detail", kwargs={"pk": test_case.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    expected_data = TestCaseSerializer(test_case).data
    assert response.data == expected_data


@pytest.mark.django_db
def test_get_test_case_detail_unauthenticated(api_client, test_case):
    url = reverse("testcase-detail", kwargs={"pk": test_case.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_test_case_detail_not_found(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("testcase-detail", kwargs={"pk": 999})  # Non-existent ID
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_test_case_detail_contains_steps(api_client, test_case, test_steps, user):
    api_client.force_authenticate(user=user)
    url = reverse("testcase-detail", kwargs={"pk": test_case.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "steps" in response.data
    assert len(response.data["steps"]) == len(test_steps)

    # Verify step data
    for i, step in enumerate(test_steps):
        assert response.data["steps"][i]["order"] == step.order
        assert response.data["steps"][i]["description"] == step.description
        assert response.data["steps"][i]["expected_result"] == step.expected_result


@pytest.mark.django_db
def test_get_test_case_detail_steps_ordered(api_client, test_case, user):
    api_client.force_authenticate(user=user)
    # Create steps out of order
    step1 = TestStep.objects.create(
        test_case=test_case, order=2, description="Step 2", expected_result=""
    )
    step2 = TestStep.objects.create(
        test_case=test_case, order=1, description="Step 1", expected_result=""
    )

    url = reverse("testcase-detail", kwargs={"pk": test_case.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["steps"]) == 2
    # Verify steps are ordered by 'order' field
    assert response.data["steps"][0]["description"] == "Step 1"
    assert response.data["steps"][1]["description"] == "Step 2"
