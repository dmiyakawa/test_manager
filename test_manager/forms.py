from logging import getLogger
from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Project, TestSuite, TestCase, TestStep, TestSession

User = get_user_model()

_logger = getLogger("model")


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
    __test__ = False

    class Meta:
        model = TestSuite
        fields = ["name", "description"]


class TestStepForm(forms.ModelForm):
    __test__ = False

    class Meta:
        model = TestStep
        fields = ["order", "description", "expected_result", "test_case"]
        widgets = {
            "order": forms.HiddenInput(),
            "test_case": forms.HiddenInput(),
            # "description": forms.Textarea(attrs={'rows':8, 'cols':50}),
            # "expected_result": forms.Textarea(attrs={'rows':8, 'cols':50}),
        }


TestStepFormSet = inlineformset_factory(
    TestCase, TestStep, form=TestStepForm, extra=0, can_delete=True
)
TestStepFormSet.__test__ = False


class TestCaseForm(forms.ModelForm):
    __test__ = False

    class Meta:
        model = TestCase
        fields = ["title", "description", "prerequisites", "status", "priority"]


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class TestSessionForm(forms.ModelForm):
    selected_cases = forms.ModelMultipleChoiceField(
        queryset=TestCase.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="テストケースを選択"
    )

    class Meta:
        model = TestSession
        fields = ['name', 'description', 'environment', 'selected_cases']

    def __init__(self, *args, **kwargs):
        project = kwargs.get('initial', {}).get('project')
        super().__init__(*args, **kwargs)
        if project:
            self.fields['selected_cases'].queryset = TestCase.objects.filter(suite__project=project).order_by('suite__name', 'title')
        else:
            self.fields['selected_cases'].queryset = TestCase.objects.none()
            self.fields['selected_cases'].disabled = True
