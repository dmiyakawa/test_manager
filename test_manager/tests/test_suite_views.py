import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_manager.models import Project, TestSuite

User = get_user_model()


@pytest.mark.django_db
class TestSuiteViews:
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
            project=project, name="Test Suite", description="Test Description"
        )

    def test_suite_detail_view(self, client, user, suite):
        client.login(username="testuser", password="testpass")
        url = reverse("suite_detail", kwargs={"pk": suite.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Suite" in str(response.content)

    def test_suite_create_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(
            content_type=content_type, codename="edit_tests"
        )
        user.user_permissions.add(permission)
        url = reverse("suite_create", kwargs={"pk": project.id})
        data = {"name": "New Suite", "description": "New Description"}
        response = client.post(url, data)
        assert response.status_code == 302
        assert TestSuite.objects.filter(name="New Suite").exists()

    def test_suite_update_view(self, client, user, project, suite):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(
            content_type=content_type, codename="edit_tests"
        )
        user.user_permissions.add(permission)
        url = reverse("suite_update", kwargs={"pk": suite.pk})
        data = {"name": "Updated Suite", "description": "Updated Description"}
        response = client.post(url, data)
        assert response.status_code == 302
        suite.refresh_from_db()
        assert suite.name == "Updated Suite"
