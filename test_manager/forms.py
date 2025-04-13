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
