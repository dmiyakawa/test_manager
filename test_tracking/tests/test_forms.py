import pytest
from test_tracking.forms import ProjectForm, TestStepForm, TestStepFormSet
from test_tracking.models import Project, TestCase, TestStep


@pytest.mark.django_db
class TestProjectForm:
    def test_valid_form(self):
        form = ProjectForm(
            {"name": "テストプロジェクト", "description": "テスト用のプロジェクトです"}
        )
        assert form.is_valid()

    def test_invalid_form(self):
        form = ProjectForm({})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_save_form(self):
        form = ProjectForm(
            {"name": "テストプロジェクト", "description": "テスト用のプロジェクトです"}
        )
        project = form.save()
        assert project.name == "テストプロジェクト"
        assert project.description == "テスト用のプロジェクトです"


@pytest.mark.django_db
class TestTestStepForm:
    @pytest.fixture
    def test_case(self):
        project = Project.objects.create(name="テストプロジェクト")
        suite = project.test_suites.create(name="テストスイート")
        return TestCase.objects.create(
            suite=suite, title="ログインテスト", status="ACTIVE", priority="HIGH"
        )

    def test_valid_form(self, test_case):
        form = TestStepForm(
            {
                "order": 1,
                "description": "ログインボタンをクリック",
                "expected_result": "ログインフォームが表示される",
                "test_case": test_case.id,
            }
        )
        assert form.is_valid()

    def test_invalid_form(self):
        form = TestStepForm({})
        assert not form.is_valid()
        assert "description" in form.errors
        assert "expected_result" in form.errors
        assert "test_case" in form.errors


@pytest.mark.django_db
class TestTestStepFormSet:
    @pytest.fixture
    def test_case(self):
        project = Project.objects.create(name="テストプロジェクト")
        suite = project.test_suites.create(name="テストスイート")
        return TestCase.objects.create(
            suite=suite, title="ログインテスト", status="ACTIVE", priority="HIGH"
        )

    def test_empty_formset(self, test_case):
        formset = TestStepFormSet(instance=test_case)
        assert len(formset.forms) == 1  # extra=1の設定により

    def test_save_formset(self, test_case):
        data = {
            "steps-TOTAL_FORMS": "2",
            "steps-INITIAL_FORMS": "0",
            "steps-MIN_NUM_FORMS": "0",
            "steps-MAX_NUM_FORMS": "1000",
            "steps-0-order": "1",
            "steps-0-description": "ログインボタンをクリック",
            "steps-0-expected_result": "ログインフォームが表示される",
            "steps-0-test_case": test_case.id,
            "steps-1-order": "2",
            "steps-1-description": "ログイン情報を入力",
            "steps-1-expected_result": "ホーム画面に遷移する",
            "steps-1-test_case": test_case.id,
        }
        formset = TestStepFormSet(data, instance=test_case)
        assert formset.is_valid()
        steps = formset.save()
        assert len(steps) == 2
        assert steps[0].order == 1
        assert steps[1].order == 2

    def test_delete_step(self, test_case):
        # 既存のステップを作成
        step = TestStep.objects.create(
            test_case=test_case,
            order=1,
            description="ログインボタンをクリック",
            expected_result="ログインフォームが表示される",
        )

        data = {
            "steps-TOTAL_FORMS": "1",
            "steps-INITIAL_FORMS": "1",
            "steps-MIN_NUM_FORMS": "0",
            "steps-MAX_NUM_FORMS": "1000",
            "steps-0-id": step.id,
            "steps-0-order": "1",
            "steps-0-description": "ログインボタンをクリック",
            "steps-0-expected_result": "ログインフォームが表示される",
            "steps-0-DELETE": "on",
            "steps-0-test_case": test_case.id,
        }
        formset = TestStepFormSet(data, instance=test_case)
        assert formset.is_valid()
        formset.save()
        assert TestStep.objects.count() == 0
