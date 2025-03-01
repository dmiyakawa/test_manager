from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Prefetch, Count
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms
from .models import Project, TestSuite, TestCase, TestRun, TestExecution
from .forms import ProjectForm, ProjectMemberForm, TestSuiteForm, TestCaseForm, TestStepForm
from .mixins import ProjectManagerRequired, TestEditorRequired, TestExecutorRequired

User = get_user_model()

class CSVManagementView(UserPassesTestMixin, View):
    template_name = 'test_tracking/csv_management.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        import_types = {
            'projects': {
                'title': 'プロジェクト',
                'filename': 'projects.csv',
                'headers': ['id', 'name', 'description']
            },
            'suites': {
                'title': 'テストスイート',
                'filename': 'suites.csv',
                'headers': ['id', 'project_id', 'name', 'description']
            },
            'cases': {
                'title': 'テストケース',
                'filename': 'cases.csv',
                'headers': ['id', 'suite_id', 'title', 'description', 'prerequisites', 'status', 'priority']
            },
            'steps': {
                'title': 'テストステップ',
                'filename': 'steps.csv',
                'headers': ['id', 'case_id', 'order', 'description', 'expected_result']
            }
        }
        return render(request, self.template_name, {'import_types': import_types})


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'test_tracking/project_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # 作成者に全ての権限を付与
        assign_perm('manage_project', self.request.user, self.object)
        assign_perm('edit_tests', self.request.user, self.object)
        assign_perm('execute_tests', self.request.user, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})

class ProjectUpdateView(ProjectManagerRequired, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'test_tracking/project_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # プロジェクトメンバー管理用のコンテキストを追加
        project_users = get_users_with_perms(self.object, attach_perms=True)
        context['project_members'] = [
            user for user in User.objects.filter(id__in=project_users.keys())
        ]
        context['available_users'] = User.objects.exclude(
            id__in=project_users.keys()
        ).exclude(is_superuser=True)
        return context

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})

class ProjectMemberView(ProjectManagerRequired, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectMemberForm(request.POST)
        
        if form.is_valid():
            user = form.cleaned_data['user']
            permissions = form.cleaned_data['permissions']
            
            for perm in permissions:
                assign_perm(perm, user, project)
            
            messages.success(request, 'メンバーを追加しました')
        else:
            messages.error(request, 'メンバーの追加に失敗しました')
        
        return redirect('project_update', pk=pk)

class ProjectMemberRemoveView(ProjectManagerRequired, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user_id = request.POST.get('user')
        user = get_object_or_404(User, id=user_id)
        
        remove_perm('manage_project', user, project)
        remove_perm('edit_tests', user, project)
        remove_perm('execute_tests', user, project)
        
        messages.success(request, 'メンバーを削除しました')
        return redirect('project_update', pk=pk)


class TestRunCreateView(CreateView):
    model = TestRun
    template_name = 'test_tracking/test_run_form.html'
    fields = ['name', 'description', 'executed_by', 'environment']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suite'] = get_object_or_404(TestSuite, pk=self.kwargs['suite_pk'])
        return context

    def form_valid(self, form):
        form.instance.suite = get_object_or_404(TestSuite, pk=self.kwargs['suite_pk'])
        response = super().form_valid(form)
        
        # 選択されたテストケースをセッションに保存
        selected_cases = self.request.POST.getlist('selected_cases')
        self.request.session['selected_cases'] = selected_cases
        
        return response

    def get_success_url(self):
        return reverse_lazy('test_run_execute', kwargs={'pk': self.object.pk})


class TestRunExecuteView(View):
    template_name = 'test_tracking/test_run_execute.html'

    def get(self, request, pk):
        test_run = get_object_or_404(TestRun, pk=pk)
        executed_cases = test_run.executions.values_list('test_case_id', flat=True)
        selected_cases = request.session.get('selected_cases', [])
        remaining_cases = [int(case_id) for case_id in selected_cases if int(case_id) not in executed_cases]

        if not remaining_cases:
            if not test_run.completed_at:
                test_run.complete()
            return redirect('test_run_detail', pk=test_run.pk)

        current_case = TestCase.objects.get(pk=remaining_cases[0])
        total_count = len(selected_cases)
        completed_count = len(executed_cases)
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0

        return render(request, self.template_name, {
            'test_run': test_run,
            'current_case': current_case,
            'total_count': total_count,
            'completed_count': completed_count,
            'progress': progress,
        })

    def post(self, request, pk):
        test_run = get_object_or_404(TestRun, pk=pk)
        test_case = get_object_or_404(TestCase, pk=request.POST['test_case_id'])

        TestExecution.objects.create(
            test_run=test_run,
            test_case=test_case,
            executed_by=test_run.executed_by,
            environment=test_run.environment,
            result=request.POST['result'],
            actual_result=request.POST['actual_result'],
            notes=request.POST['notes']
        )

        return redirect('test_run_execute', pk=pk)


class TestRunDetailView(DetailView):
    model = TestRun
    template_name = 'test_tracking/test_run_detail.html'
    context_object_name = 'test_run'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        executions = self.object.executions.all()
        context.update({
            'pass_count': executions.filter(result='PASS').count(),
            'fail_count': executions.filter(result='FAIL').count(),
            'blocked_count': executions.filter(result='BLOCKED').count(),
            'skipped_count': executions.filter(result='SKIPPED').count(),
        })
        return context


class ProjectListView(ListView):
    model = Project
    template_name = 'test_tracking/project_list.html'
    context_object_name = 'projects'


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'test_tracking/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 最近の実行結果を取得（全テストスイートの全テストケースから）
        recent_executions = TestExecution.objects.filter(
            test_case__suite__project=self.object
        ).select_related('test_case').order_by('-executed_at')[:10]
        context['recent_executions'] = recent_executions
        return context


class TestSuiteCreateView(TestEditorRequired, CreateView):
    model = TestSuite
    form_class = TestSuiteForm
    template_name = 'test_tracking/suite_form.html'

    def form_valid(self, form):
        form.instance.project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.kwargs['project_pk']})

class TestSuiteUpdateView(TestEditorRequired, UpdateView):
    model = TestSuite
    form_class = TestSuiteForm
    template_name = 'test_tracking/suite_form.html'

    def get_success_url(self):
        return reverse_lazy('suite_detail', kwargs={'pk': self.object.pk})

class TestSuiteDeleteView(TestEditorRequired, DeleteView):
    model = TestSuite
    template_name = 'test_tracking/suite_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.project.pk})

class TestSuiteListView(ListView):
    model = TestSuite
    template_name = 'test_tracking/suite_list.html'
    context_object_name = 'suites'


class TestSuiteDetailView(DetailView):
    model = TestSuite
    template_name = 'test_tracking/suite_detail.html'
    context_object_name = 'suite'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_cases'] = self.object.test_cases.all()
        context['recent_test_runs'] = self.object.test_runs.order_by('-started_at')[:5]
        return context


class TestCaseCreateView(TestEditorRequired, CreateView):
    model = TestCase
    form_class = TestCaseForm
    template_name = 'test_tracking/case_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['steps_formset'] = TestStepForm(self.request.POST)
        else:
            context['steps_formset'] = TestStepForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        steps_formset = context['steps_formset']
        form.instance.suite = get_object_or_404(TestSuite, pk=self.kwargs['suite_pk'])
        
        if steps_formset.is_valid():
            self.object = form.save()
            steps_formset.instance = self.object
            steps_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('suite_detail', kwargs={'pk': self.kwargs['suite_pk']})

class TestCaseUpdateView(TestEditorRequired, UpdateView):
    model = TestCase
    form_class = TestCaseForm
    template_name = 'test_tracking/case_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['steps_formset'] = TestStepForm(self.request.POST, instance=self.object)
        else:
            context['steps_formset'] = TestStepForm(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        steps_formset = context['steps_formset']
        
        if steps_formset.is_valid():
            self.object = form.save()
            steps_formset.instance = self.object
            steps_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('case_detail', kwargs={'pk': self.object.pk})

class TestCaseDeleteView(TestEditorRequired, DeleteView):
    model = TestCase
    template_name = 'test_tracking/case_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('suite_detail', kwargs={'pk': self.object.suite.pk})

class TestCaseListView(ListView):
    model = TestCase
    template_name = 'test_tracking/case_list.html'
    context_object_name = 'cases'


class TestCaseDetailView(DetailView):
    model = TestCase
    template_name = 'test_tracking/case_detail.html'
    context_object_name = 'case'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['executions'] = self.object.executions.order_by('-executed_at')
        return context


class TestExecutionCreateView(TestExecutorRequired, CreateView):
    model = TestExecution
    template_name = 'test_tracking/execution_form.html'
    fields = ['test_run', 'executed_by', 'result', 'notes', 'actual_result', 'environment']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        test_case = get_object_or_404(TestCase, pk=self.kwargs['case_pk'])
        context['test_case'] = test_case
        context['test_runs'] = test_case.suite.test_runs.filter(completed_at__isnull=True)
        return context

    def form_valid(self, form):
        form.instance.test_case = get_object_or_404(TestCase, pk=self.kwargs['case_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('case_detail', kwargs={'pk': self.kwargs['case_pk']})

    def get_permission_object(self):
        return get_object_or_404(TestCase, pk=self.kwargs['case_pk']).suite.project
