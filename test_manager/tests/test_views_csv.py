import pytest
import json
import csv
import io
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from test_manager.models import Project, TestSuite, TestCase, TestStep

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
        data = [
            ["project_name", "type", "parent", "name", "description", "order", "status", "priority", "prerequisites", "expected_result"],
            ["Test Project", "project", "", "Test Project", "Test Description", "", "", "", "", ""],
            ["Test Project", "suite", "Test Project", "Test Suite", "Test Suite Description", "", "", "", "", ""],
            ["Test Project", "case", "Test Suite", "Test Case", "Test Description", "", "ACTIVE", "HIGH", "", ""],
            ["Test Project", "step", "Test Case", "", "Test Step", "1", "", "", "", "Expected Result"]
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        return output.getvalue().encode('utf-8')

    def test_csv_management_view(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_management")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "プロジェクトデータ" in content
        assert "test_data.csv" in content

    def test_csv_management_view_unauthorized(self, client):
        url = reverse("csv_management")
        response = client.get(url)
        assert response.status_code == 302

    def test_project_csv_export(self, client, admin_user):
        client.login(username="admin", password="adminpass")

        # テストデータを作成
        project = Project.objects.create(
            name="Test Project", description="Test Description"
        )
        suite = TestSuite.objects.create(
            project=project,
            name="Test Suite",
            description="Test Suite Description"
        )
        case = TestCase.objects.create(
            suite=suite,
            title="Test Case",
            description="Test Description",
            status="ACTIVE",
            priority="HIGH"
        )
        step = TestStep.objects.create(
            test_case=case,
            order=1,
            description="Test Step",
            expected_result="Expected Result"
        )

        # 別のプロジェクトのデータを作成（エクスポートされないことを確認するため）
        other_project = Project.objects.create(
            name="Other Project", description="Other Description"
        )
        other_suite = TestSuite.objects.create(
            project=other_project,
            name="Other Suite",
            description="Other Suite Description"
        )

        # プロジェクト単位のエクスポート
        url = reverse("project_csv_export", kwargs={"project_id": project.id})
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        content = response.content.decode("utf-8")

        # プロジェクトのデータが含まれていることを確認
        assert "Test Project" in content
        assert "Test Suite" in content
        assert "Test Case" in content
        assert "Test Step" in content
        assert "Expected Result" in content

        # 別のプロジェクトのデータが含まれていないことを確認
        assert "Other Project" not in content
        assert "Other Suite" not in content

    def test_csv_export(self, client, admin_user):
        client.login(username="admin", password="adminpass")

        # テストデータを作成
        project = Project.objects.create(
            name="Test Project", description="Test Description"
        )
        suite = TestSuite.objects.create(
            project=project,
            name="Test Suite",
            description="Test Suite Description"
        )
        case = TestCase.objects.create(
            suite=suite,
            title="Test Case",
            description="Test Description",
            status="ACTIVE",
            priority="HIGH"
        )
        step = TestStep.objects.create(
            test_case=case,
            order=1,
            description="Test Step",
            expected_result="Expected Result"
        )

        # エクスポート
        url = reverse("csv_export")
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        content = response.content.decode("utf-8")

        # 各レコードが含まれていることを確認
        assert "Test Project" in content
        assert "Test Suite" in content
        assert "Test Case" in content
        assert "Test Step" in content
        assert "Expected Result" in content

    def test_csv_import(self, client, admin_user, csv_data):
        client.login(username="admin", password="adminpass")

        # インポート
        url = reverse("csv_import")
        csv_file = SimpleUploadedFile(
            "test_data.csv", csv_data, content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 302
        assert response.url == reverse("project_list")

        # リダイレクト先を確認
        response = client.get(response.url)
        assert response.status_code == 200

        # データが正しくインポートされたことを確認
        assert Project.objects.count() == 1
        project = Project.objects.first()
        assert project.name == "Test Project"

        assert TestSuite.objects.count() == 1
        suite = TestSuite.objects.first()
        assert suite.name == "Test Suite"
        assert suite.project == project

        assert TestCase.objects.count() == 1
        case = TestCase.objects.first()
        assert case.title == "Test Case"
        assert case.suite == suite
        assert case.status == "ACTIVE"
        assert case.priority == "HIGH"

        assert TestStep.objects.count() == 1
        step = TestStep.objects.first()
        assert step.test_case == case
        assert step.order == 1
        assert step.description == "Test Step"
        assert step.expected_result == "Expected Result"

    def test_csv_import_no_file(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_import")
        response = client.post(url, {})
        assert response.status_code == 400

    def test_csv_import_invalid_data(self, client, admin_user):
        client.login(username="admin", password="adminpass")
        url = reverse("csv_import")
        invalid_data = (
            b"project_name,type,parent,name,description,order,status,priority,prerequisites,expected_result\r\n"
            b"Test Project,invalid,Test,Test,Test,,,,,,\r\n"
        )
        csv_file = SimpleUploadedFile(
            "test_data.csv",
            invalid_data,
            content_type="text/csv"
        )
        response = client.post(url, {"file": csv_file})
        assert response.status_code == 400
