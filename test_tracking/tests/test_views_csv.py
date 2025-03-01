import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from test_tracking.models import Project, TestSuite, TestCase, TestStep

User = get_user_model()


@pytest.mark.django_db
class TestCSVViews:
    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )

    @pytest.fixture
    def csv_data(self):
        return {
            "projects": b"id,name,description\n1,Test Project,Test Description",
            "suites": b"id,project_id,name,description\n1,1,Test Suite,Test Suite Description",
            "cases": b"id,suite_id,title,description,prerequisites,status,priority\n1,1,Test Case,Test Description,,ACTIVE,HIGH",
            "steps": b"id,case_id,order,description,expected_result\n1,1,1,Test Step,Expected Result",
        }

    def test_csv_management_view(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_management")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "プロジェクト" in content
        assert "テストスイート" in content

    def test_csv_management_view_unauthorized(self, client):
        url = reverse("csv_management")
        response = client.get(url)
        assert response.status_code == 302

    def test_csv_export(self, client, admin_user):
        client.login(username="admin", password="adminpass")

        # プロジェクトを作成
        project = Project.objects.create(
            name="Test Project", description="Test Description"
        )

        # プロジェクトのエクスポート
        url = reverse("csv_export", kwargs={"type": "projects"})
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "Test Project" in str(response.content)

    def test_csv_import(self, client, admin_user, csv_data):
        client.login(username="admin", password="adminpass")

        # プロジェクトのインポート
        url = reverse("csv_import", kwargs={"type": "projects"})
        csv_file = SimpleUploadedFile(
            "projects.csv", csv_data["projects"], content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 200
        assert Project.objects.count() == 1
        project = Project.objects.first()
        assert project.name == "Test Project"

        # テストスイートのインポート
        url = reverse("csv_import", kwargs={"type": "suites"})
        csv_file = SimpleUploadedFile(
            "suites.csv", csv_data["suites"], content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 200
        assert TestSuite.objects.count() == 1

        # テストケースのインポート
        url = reverse("csv_import", kwargs={"type": "cases"})
        csv_file = SimpleUploadedFile(
            "cases.csv", csv_data["cases"], content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 200
        assert TestCase.objects.count() == 1

        # テストステップのインポート
        url = reverse("csv_import", kwargs={"type": "steps"})
        csv_file = SimpleUploadedFile(
            "steps.csv", csv_data["steps"], content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 200
        assert TestStep.objects.count() == 1

    def test_csv_import_invalid_type(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_import", kwargs={"type": "invalid"})
        csv_file = SimpleUploadedFile(
            "invalid.csv", b"invalid data", content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 400

    def test_csv_import_no_file(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_import", kwargs={"type": "projects"})
        response = client.post(url, {})
        assert response.status_code == 400
