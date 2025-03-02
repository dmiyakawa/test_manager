from datetime import date
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_tracking.models import Project, TestSuite, TestCase, TestSession, TestExecution

User = get_user_model()


@pytest.mark.django_db
class TestSessionViews:
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
            description="Test Description",
            prerequisites="Test Prerequisites",
            status="DRAFT",
            priority="MEDIUM"
        )

    @pytest.fixture
    def test_session(self, project, user, suite):
        test_session = TestSession.objects.create(
            project=project,
            name="Test Session",
            executed_by=user,
            environment="Test Environment"
        )
        test_session.available_suites.add(suite)
        return test_session

    def test_test_session_execute_view_get_next_case(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # TestExecutionを作成
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            status="NOT_TESTED"
        )

        url = reverse("test_session_execute", kwargs={"pk": test_session.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)
        assert "0/1" in str(response.content)  # 進捗表示（完了数/全体数）

    def test_test_session_execute_view_get_specific_case(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # TestExecutionを作成
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            status="NOT_TESTED"
        )

        # 特定のケースを指定してGETリクエスト
        url = reverse("test_session_execute", kwargs={"pk": test_session.pk})
        url += f"?test_case_id={case.pk}"
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

    def test_test_session_execute_view_get_completed(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # すべてのテストケースを実行済みに
        TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            executed_by=user,
            environment="Test Environment",
            status="PASS"
        )

        url = reverse("test_session_execute", kwargs={"pk": test_session.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("test_session_detail", kwargs={"pk": test_session.pk})

    def test_test_session_execute_view_post_with_status(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # TestExecutionを作成
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            status="NOT_TESTED"
        )

        url = reverse("test_session_execute", kwargs={"pk": test_session.pk})
        data = {
            "test_case_id": case.pk,
            "status": "PASS",
            "result_detail": "Test Result",
            "notes": "Test Notes"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        execution.refresh_from_db()
        assert execution.status == "PASS"
        assert execution.result_detail == "Test Result"
        assert execution.notes == "Test Notes"

    def test_test_session_execute_view_post_without_status(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # TestExecutionを作成
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            status="PASS"  # 一度実行済みのケース
        )

        url = reverse("test_session_execute", kwargs={"pk": test_session.pk})
        data = {
            "test_case_id": case.pk,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        redirect_url = response.url
        assert f"test_case_id={case.pk}" in redirect_url

        # リダイレクト先のGETリクエストでケースが選択されることを確認
        response = client.get(redirect_url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

        # 実行状態がリセットされていることを確認
        execution.refresh_from_db()
        assert execution.status == "NOT_TESTED"
        assert execution.executed_at is None
        assert execution.executed_by == ""
        assert execution.result_detail == ""
        assert execution.notes == ""

    def test_test_session_skip_all_view(self, client, user, test_session, case):
        client.login(username="testuser", password="testpass")
        # TestExecutionを作成
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            status="NOT_TESTED"
        )

        url = reverse("test_session_skip_all", kwargs={"pk": test_session.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("test_session_detail", kwargs={"pk": test_session.pk})

        # 未実行のテストケースがスキップに変更されていることを確認
        execution.refresh_from_db()
        assert execution.status == "SKIPPED"
        assert execution.notes == "一括スキップ"

        # テストセッションが完了状態になっていることを確認
        test_session.refresh_from_db()
        assert test_session.completed_at is not None


@pytest.mark.django_db
class TestSessionListView:
    @pytest.fixture
    def user(self):
        return User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
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
    def test_session(self, project, user, suite):
        test_session = TestSession.objects.create(
            project=project,
            name="Test Session",
            executed_by=user,
            environment="Test Environment"
        )
        test_session.available_suites.add(suite)
        return test_session

    def test_session_list_view_empty(self, client, user):
        client.login(username="admin", password="adminpass")
        url = reverse("test_session_list")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("UTF-8")
        assert "テストセッションがありません" in content

    def test_session_list_view_with_data(self, client, user, test_session):
        client.login(username="admin", password="adminpass")
        url = reverse("test_session_list")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert test_session.name in content

    def test_session_detail_view(self, client, user, test_session):
        client.login(username="admin", password="adminpass")
        url = reverse("test_session_detail", kwargs={"pk": test_session.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert test_session.name in content
        assert test_session.environment in content

    def test_session_create_view_initial_name(self, client, user, project):
        client.login(username="admin", password="adminpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='execute_tests')
        user.user_permissions.add(permission)
        url = reverse("test_session_create", kwargs={"project_pk": project.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        expected_name = f"テストセッション ({date.today().strftime('%Y/%m/%d')})"
        assert expected_name in content

    def test_session_create_view_duplicate_name(self, client, user, project):
        client.login(username="admin", password="adminpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='execute_tests')
        user.user_permissions.add(permission)
        
        # Create a session with the default name
        base_name = f"テストセッション ({date.today().strftime('%Y/%m/%d')})"
        TestSession.objects.create(
            project=project,
            name=base_name,
            executed_by=user,
            environment="Test Environment"
        )

        # Try to create another session
        url = reverse("test_session_create", kwargs={"project_pk": project.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        expected_name = f"{base_name} (1)"
        assert expected_name in content

    def test_session_create_view(self, client, user, project):
        client.login(username="admin", password="adminpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='execute_tests')
        user.user_permissions.add(permission)
        url = reverse("test_session_create", kwargs={"project_pk": project.pk})
        data = {
            "name": "New Test Session",
            "environment": "Test Environment",
            "description": "Test Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert TestSession.objects.filter(name="New Test Session").exists()

    def test_session_create_view_unauthorized(self, client, user, project):
        # client.login(username="admin", password="adminpass")
        url = reverse("test_session_create", kwargs={"project_pk": project.pk})
        response = client.get(url)
        assert response.status_code == 302
