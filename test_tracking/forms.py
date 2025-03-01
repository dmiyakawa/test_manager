from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Project, TestSuite, TestCase, TestStep

User = get_user_model()


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectMemberForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    permissions = forms.MultipleChoiceField(
        choices=[
            ("manage_project", "プロジェクト管理"),
            ("edit_tests", "テスト編集"),
            ("execute_tests", "テスト実行"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )


class TestSuiteForm(forms.ModelForm):
    class Meta:
        model = TestSuite
        fields = ["name", "description"]


class TestStepForm(forms.ModelForm):
    class Meta:
        model = TestStep
        fields = ["order", "description", "expected_result"]
        widgets = {"order": forms.HiddenInput()}


TestStepFormSet = inlineformset_factory(
    TestCase, TestStep, form=TestStepForm, extra=1, can_delete=True
)


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ["title", "description", "prerequisites", "status", "priority"]
