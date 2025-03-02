import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from test_tracking.models import Project, TestSuite, TestCase, TestSession, TestExecution

User = get_user_model()


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
        test_session = TestSession.objects.create(
            project=case.suite.project,
            name="Test Session",
            executed_by=user,
            environment="Test Environment"
        )
        execution = TestExecution.objects.create(
            test_session=test_session,
            test_case=case,
            executed_by=user,
            environment="Test Environment",
            status="PASS",
            result_detail="Test Result",
            notes="Test Notes"
        )
        url = reverse("case_detail", kwargs={"pk": case.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert "Test Session" in str(response.content)
        assert "PASS" in str(response.content)


@pytest.mark.django_db
class TestCaseCreateUpdateViews:
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

    def test_case_create_view(self, client, user, suite):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='edit_tests')
        user.user_permissions.add(permission)
        url = reverse("case_create", kwargs={"suite_pk": suite.pk})
        data = {
            "title": "New Test Case",
            "description": "Test Description",
            "prerequisites": "Test Prerequisites",
            "status": "DRAFT",
            "priority": "MEDIUM",
            "steps-TOTAL_FORMS": "1",
            "steps-INITIAL_FORMS": "0",
            "steps-MIN_NUM_FORMS": "0",
            "steps-MAX_NUM_FORMS": "1000",
            "steps-0-description": "Test Step",
            "steps-0-expected_result": "Expected Result",
            "steps-0-order": "0"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert TestCase.objects.filter(title="New Test Case").exists()

    def test_case_update_view(self, client, user, suite):
        client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Project)
        permission = Permission.objects.get(content_type=content_type, codename='edit_tests')
        user.user_permissions.add(permission)
        
        case = TestCase.objects.create(
            suite=suite,
            title="Test Case",
            description="Test Description",
            prerequisites="Test Prerequisites",
            status="DRAFT",
            priority="MEDIUM"
        )
        
        url = reverse("case_update", kwargs={"pk": case.pk})
        data = {
            "title": "Updated Test Case",
            "description": "Updated Description",
            "prerequisites": "Updated Prerequisites",
            "status": "ACTIVE",
            "priority": "HIGH",
            "steps-TOTAL_FORMS": "0",
            "steps-INITIAL_FORMS": "0",
            "steps-MIN_NUM_FORMS": "0",
            "steps-MAX_NUM_FORMS": "1000"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        case.refresh_from_db()
        assert case.title == "Updated Test Case"
        assert case.status == "ACTIVE"
        assert case.priority == "HIGH"
