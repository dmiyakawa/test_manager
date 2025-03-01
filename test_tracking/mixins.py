from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Project

class ProjectPermissionMixin(UserPassesTestMixin):
    """
    プロジェクトの権限をチェックするミックスイン
    project_permissionに必要な権限名を指定する
    """
    project_permission = None

    def get_project(self):
        if hasattr(self, 'project'):
            return self.project
        
        # プロジェクトIDの取得を試みる
        project_pk = None
        if hasattr(self, 'kwargs'):
            project_pk = self.kwargs.get('project_pk')
            if not project_pk and 'pk' in self.kwargs:
                # プロジェクト直接の操作の場合
                project_pk = self.kwargs.get('pk')
            elif not project_pk and 'suite_pk' in self.kwargs:
                # テストスイート経由の場合
                from .models import TestSuite
                suite = get_object_or_404(TestSuite, pk=self.kwargs['suite_pk'])
                project_pk = suite.project_id
            elif not project_pk and 'case_pk' in self.kwargs:
                # テストケース経由の場合
                from .models import TestCase
                case = get_object_or_404(TestCase, pk=self.kwargs['case_pk'])
                project_pk = case.suite.project_id

        if project_pk:
            self.project = get_object_or_404(Project, pk=project_pk)
            return self.project
        return None

    def test_func(self):
        if self.request.user.is_superuser:
            return True

        if not self.project_permission:
            raise ValueError("project_permission must be set")

        project = self.get_project()
        if not project:
            return True  # プロジェクト一覧など、特定のプロジェクトに紐付かない場合

        return self.request.user.has_perm(f'test_tracking.{self.project_permission}', project)

class ProjectManagerRequired(ProjectPermissionMixin):
    project_permission = 'manage_project'

class TestEditorRequired(ProjectPermissionMixin):
    project_permission = 'edit_tests'

class TestExecutorRequired(ProjectPermissionMixin):
    project_permission = 'execute_tests'
