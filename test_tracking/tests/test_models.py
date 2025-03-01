import pytest
from django.utils import timezone
from test_tracking.models import Project, TestSuite, TestCase, TestStep

@pytest.mark.django_db
class TestProject:
    def test_create_project(self):
        project = Project.objects.create(
            name="テストプロジェクト",
            description="テスト用のプロジェクトです"
        )
        assert project.name == "テストプロジェクト"
        assert project.description == "テスト用のプロジェクトです"
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_str(self):
        project = Project.objects.create(name="テストプロジェクト")
        assert str(project) == "テストプロジェクト"

@pytest.mark.django_db
class TestTestSuite:
    @pytest.fixture
    def project(self):
        return Project.objects.create(name="テストプロジェクト")

    def test_create_suite(self, project):
        suite = TestSuite.objects.create(
            project=project,
            name="テストスイート1",
            description="テスト用のスイートです"
        )
        assert suite.name == "テストスイート1"
        assert suite.description == "テスト用のスイートです"
        assert suite.project == project
        assert suite.created_at is not None
        assert suite.updated_at is not None

    def test_suite_str(self, project):
        suite = TestSuite.objects.create(
            project=project,
            name="テストスイート1"
        )
        assert str(suite) == "テストスイート1"

@pytest.mark.django_db
class TestTestCase:
    @pytest.fixture
    def suite(self):
        project = Project.objects.create(name="テストプロジェクト")
        return TestSuite.objects.create(
            project=project,
            name="テストスイート1"
        )

    def test_create_case(self, suite):
        case = TestCase.objects.create(
            suite=suite,
            title="ログインテスト",
            description="ログイン機能のテスト",
            prerequisites="テストユーザーが作成されていること",
            status="ACTIVE",
            priority="HIGH"
        )
        assert case.title == "ログインテスト"
        assert case.description == "ログイン機能のテスト"
        assert case.prerequisites == "テストユーザーが作成されていること"
        assert case.status == "ACTIVE"
        assert case.priority == "HIGH"
        assert case.suite == suite
        assert case.created_at is not None
        assert case.updated_at is not None

    def test_case_str(self, suite):
        case = TestCase.objects.create(
            suite=suite,
            title="ログインテスト"
        )
        assert str(case) == "ログインテスト"

@pytest.mark.django_db
class TestTestStep:
    @pytest.fixture
    def case(self):
        project = Project.objects.create(name="テストプロジェクト")
        suite = TestSuite.objects.create(
            project=project,
            name="テストスイート1"
        )
        return TestCase.objects.create(
            suite=suite,
            title="ログインテスト"
        )

    def test_create_step(self, case):
        step = TestStep.objects.create(
            test_case=case,
            order=1,
            description="ログインボタンをクリック",
            expected_result="ログインフォームが表示される"
        )
        assert step.order == 1
        assert step.description == "ログインボタンをクリック"
        assert step.expected_result == "ログインフォームが表示される"
        assert step.test_case == case
        assert step.created_at is not None
        assert step.updated_at is not None

    def test_step_str(self, case):
        step = TestStep.objects.create(
            test_case=case,
            order=1,
            description="ログインボタンをクリック"
        )
        assert str(step) == "ステップ 1: ログインボタンをクリック"
