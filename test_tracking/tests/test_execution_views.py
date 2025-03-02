import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_tracking.models import Project, TestSuite, TestCase

User = get_user_model()


@pytest.mark.django_db
class TestTestExecutionViews:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="Test Project", description="Test Description"
        )

    @pytest.fixture
    def suite(self, project):
        return TestSuite.objects.create(
            project=project,
            name="Test Suite",
            description="Test Description"
        )

    @pytest.fixture
    def case(self, suite):
        return TestCase.objects.create(
            suite=suite,
            title="Test Case",
            description="Test Description"
        )

    def test_execution_create_view(self, client, user, project, case):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='execute_tests')
        user.user_permissions.add(permission)
        url = reverse("execution_create", kwargs={"case_pk": case.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

    def test_execution_create_view_unauthorized(self, client, user, case):
        url = reverse("execution_create", kwargs={"case_pk": case.pk})
        response = client.get(url)
        assert response.status_code == 302
