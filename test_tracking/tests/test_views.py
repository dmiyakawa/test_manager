import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm
from test_tracking.models import Project, TestSuite, TestCase, TestStep, TestIteration, TestExecution

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

    def test_project_update_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        assign_perm("manage_project", user, project)
        url = reverse("project_update", kwargs={"pk": project.pk})
        data = {
            "name": "Updated Project",
            "description": "Updated Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Updated Project"


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
            project=project,
            name="Test Suite",
            description="Test Description"
        )

    def test_suite_detail_view(self, client, user, suite):
        client.login(username="testuser", password="testpass")
        url = reverse("suite_detail", kwargs={"pk": suite.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Suite" in str(response.content)

    def test_suite_create_view(self, client, user, project):
        client.login(username="testuser", password="testpass")
        assign_perm("edit_tests", user, project)
        url = reverse("suite_create", kwargs={"project_pk": project.pk})
        data = {
            "name": "New Suite",
            "description": "New Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert TestSuite.objects.filter(name="New Suite").exists()

    def test_suite_update_view(self, client, user, project, suite):
        client.login(username="testuser", password="testpass")
        assign_perm("edit_tests", user, project)
        url = reverse("suite_update", kwargs={"pk": suite.pk})
        data = {
            "name": "Updated Suite",
            "description": "Updated Description"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        suite.refresh_from_db()
        assert suite.name == "Updated Suite"


@pytest.mark.django_db
class TestCaseViews:
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

    def test_case_list_view(self, client, user, case):
        client.login(username="testuser", password="testpass")
        url = reverse("case_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

    def test_case_detail_view(self, client, user, case):
        client.login(username="testuser", password="testpass")
        url = reverse("case_detail", kwargs={"pk": case.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

    def test_case_detail_view_with_executions(self, client, user, case):
        client.login(username="testuser", password="testpass")
        # テスト実行を作成
        test_iteration = TestIteration.objects.create(
            project=case.suite.project,
            name="Test Iteration",
            executed_by=user,
            environment="Test Environment"
        )
        execution = TestExecution.objects.create(
            test_iteration=test_iteration,
            test_case=case,
            executed_by=user,
            environment="Test Environment",
            result="PASS",
            actual_result="Test Result",
            notes="Test Notes"
        )
        url = reverse("case_detail", kwargs={"pk": case.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Iteration" in str(response.content)
        assert "PASS" in str(response.content)


@pytest.mark.django_db
class TestIterationViews:
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
    def test_iteration(self, project, user, suite):
        test_iteration = TestIteration.objects.create(
            project=project,
            name="Test Iteration",
            executed_by=user,
            environment="Test Environment"
        )
        test_iteration.available_suites.add(suite)
        return test_iteration

    def test_test_iteration_execute_view_get(self, client, user, test_iteration, case):
        client.login(username="testuser", password="testpass")
        # セッションにテストケースを設定
        session = client.session
        session["selected_cases"] = [str(case.pk)]
        session.save()

        url = reverse("test_iteration_execute", kwargs={"pk": test_iteration.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)
        assert "0/1" in str(response.content)  # 進捗表示（完了数/全体数）

    def test_test_iteration_execute_view_get_completed(self, client, user, test_iteration, case):
        client.login(username="testuser", password="testpass")
        # すべてのテストケースを実行済みに
        TestExecution.objects.create(
            test_iteration=test_iteration,
            test_case=case,
            executed_by=user,
            environment="Test Environment",
            result="PASS"
        )
        session = client.session
        session["selected_cases"] = [str(case.pk)]
        session.save()

        url = reverse("test_iteration_execute", kwargs={"pk": test_iteration.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("test_iteration_detail", kwargs={"pk": test_iteration.pk})

    def test_test_iteration_execute_view_post(self, client, user, test_iteration, case):
        client.login(username="testuser", password="testpass")
        url = reverse("test_iteration_execute", kwargs={"pk": test_iteration.pk})
        data = {
            "test_case_id": case.pk,
            "result": "PASS",
            "actual_result": "Test Result",
            "notes": "Test Notes"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert TestExecution.objects.filter(test_iteration=test_iteration, test_case=case).exists()


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
        assign_perm("execute_tests", user, project)
        url = reverse("execution_create", kwargs={"case_pk": case.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Case" in str(response.content)

    def test_execution_create_view_unauthorized(self, client, user, case):
        client.login(username="testuser", password="testpass")
        url = reverse("execution_create", kwargs={"case_pk": case.pk})
        response = client.get(url)
        assert response.status_code == 403
