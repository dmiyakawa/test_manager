import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_tracking.models import Project

User = get_user_model()


@pytest.mark.django_db
class TestProjectViews:
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

    def test_project_list_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        url = reverse("project_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Project" in str(response.content)
        # 「テスト実行」という文字列が含まれていないことを確認
        assert "テスト実行" not in str(response.content)
        # 「テストラン」という文字列が含まれていないことを確認
        assert "テストラン" not in str(response.content)

    def test_project_create_view(self, client, user):
        client.login(username="testuser", password="testpass")
        url = reverse("project_create")
        data = {
            "name": "New Project",
            "description": "New Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Project.objects.filter(name="New Project").exists()

    def test_project_detail_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        url = reverse("project_detail", kwargs={"pk": project.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert project.name in str(response.content)
        assert project.description in str(response.content)

    def test_project_update_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='manage_project')
        user.user_permissions.add(permission)
        url = reverse("project_update", kwargs={"pk": project.pk})
        data = {
            "name": "Updated Project",
            "description": "Updated Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Updated Project"
