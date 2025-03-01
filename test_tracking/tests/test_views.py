import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
from test_tracking.models import Project, TestSuite, TestCase, TestExecution

User = get_user_model()


@pytest.mark.django_db
class TestProjectViews:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="testpass")

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="テストプロジェクト", description="テスト用のプロジェクトです"
        )

    def test_project_list_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        assign_perm("view_project", user, project)
        url = reverse("project_list")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "テストプロジェクト" in content

    def test_project_create_view(self, client, user):
        client.login(username="testuser", password="testpass")
        url = reverse("project_create")
        data = {"name": "新規プロジェクト", "description": "新規プロジェクトの説明"}
        response = client.post(url, data)
        assert response.status_code == 302
        project = Project.objects.get(name="新規プロジェクト")
        assert project.description == "新規プロジェクトの説明"

    def test_project_update_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        assign_perm("manage_project", user, project)
        url = reverse("project_update", kwargs={"pk": project.pk})
        data = {"name": "更新後のプロジェクト", "description": "更新後の説明"}
        response = client.post(url, data)
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "更新後のプロジェクト"
        assert project.description == "更新後の説明"


@pytest.mark.django_db
class TestSuiteViews:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="testpass")

    @pytest.fixture
    def project(self):
        return Project.objects.create(name="テストプロジェクト")

    @pytest.fixture
    def suite(self, project):
        return TestSuite.objects.create(
            project=project,
            name="テストスイート",
            description="テストスイートの説明"
        )

    def test_suite_detail_view(self, client, user, project, suite):
        client.login(username="testuser", password="testpass")
        assign_perm("view_project", user, project)
        url = reverse("suite_detail", kwargs={"pk": suite.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "テストスイート" in content
        assert "テストスイートの説明" in content

    def test_suite_create_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        assign_perm("edit_tests", user, project)
        url = reverse("suite_create", kwargs={"project_pk": project.pk})
        data = {
            "name": "新規スイート",
            "description": "新規スイートの説明"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        suite = TestSuite.objects.get(name="新規スイート")
        assert suite.description == "新規スイートの説明"
        assert suite.project == project

    def test_suite_update_view(self, client, user, project, suite):
        client.login(username="testuser", password="testpass")
        assign_perm("edit_tests", user, project)
        url = reverse("suite_update", kwargs={"pk": suite.pk})
        data = {
            "name": "更新後のスイート",
            "description": "更新後の説明"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        suite.refresh_from_db()
        assert suite.name == "更新後のスイート"
        assert suite.description == "更新後の説明"

@pytest.mark.django_db
class TestTestExecutionViews:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="testpass")

    @pytest.fixture
    def test_case(self):
        project = Project.objects.create(name="テストプロジェクト")
        suite = TestSuite.objects.create(project=project, name="テストスイート")
        return TestCase.objects.create(
            suite=suite, title="ログインテスト", status="ACTIVE", priority="HIGH"
        )

    def test_execution_create_view(self, client, user, test_case):
        client.login(username="testuser", password="testpass")
        assign_perm("execute_tests", user, test_case.suite.project)

        # テスト実行を作成
        test_run = test_case.suite.project.test_runs.create(
            name="テスト実行1",
            executed_by="testuser",
            environment="テスト環境",
            project=test_case.suite.project
        )
        test_run.available_suites.add(test_case.suite)

        url = reverse("execution_create", kwargs={"case_pk": test_case.pk})
        data = {
            "test_run": test_run.pk,
            "executed_by": "testuser",
            "environment": "テスト環境",
            "result": "PASS",
            "actual_result": "テスト成功",
            "notes": "テスト備考",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        execution = TestExecution.objects.get(test_case=test_case)
        assert execution.result == "PASS"
        assert execution.actual_result == "テスト成功"

    def test_execution_create_view_unauthorized(self, client, user, test_case):
        client.login(username="testuser", password="testpass")
        url = reverse("execution_create", kwargs={"case_pk": test_case.pk})
        response = client.get(url, follow=True)
        assert response.status_code == 403
