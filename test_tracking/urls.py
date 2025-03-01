from django.urls import path
from . import views, views_csv

urlpatterns = [
    # CSV import/export
    path(
        "csv/export/", views_csv.CSVExportView.as_view(), name="csv_export"
    ),
    path(
        "csv/import/", views_csv.CSVImportView.as_view(), name="csv_import"
    ),
    path("csv/", views.CSVManagementView.as_view(), name="csv_management"),
    # プロジェクト管理
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("project/create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("project/<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path(
        "project/<int:pk>/edit/",
        views.ProjectUpdateView.as_view(),
        name="project_update",
    ),
    path(
        "project/<int:pk>/members/",
        views.ProjectMemberView.as_view(),
        name="project_members",
    ),
    path(
        "project/<int:pk>/members/remove/",
        views.ProjectMemberRemoveView.as_view(),
        name="project_members_remove",
    ),
    # テストスイート
    path(
        "project/<int:project_pk>/suite/create/",
        views.TestSuiteCreateView.as_view(),
        name="suite_create",
    ),
    path("suite/<int:pk>/", views.TestSuiteDetailView.as_view(), name="suite_detail"),
    path(
        "suite/<int:pk>/edit/", views.TestSuiteUpdateView.as_view(), name="suite_update"
    ),
    path(
        "suite/<int:pk>/delete/",
        views.TestSuiteDeleteView.as_view(),
        name="suite_delete",
    ),
    # テストケース
    path(
        "suite/<int:suite_pk>/case/create/",
        views.TestCaseCreateView.as_view(),
        name="case_create",
    ),
    path("case/<int:pk>/", views.TestCaseDetailView.as_view(), name="case_detail"),
    path("case/<int:pk>/edit/", views.TestCaseUpdateView.as_view(), name="case_update"),
    path(
        "case/<int:pk>/delete/", views.TestCaseDeleteView.as_view(), name="case_delete"
    ),
    path("cases/", views.TestCaseListView.as_view(), name="case_list"),
    # テスト実行
    path(
        "case/<int:case_pk>/execute/",
        views.TestExecutionCreateView.as_view(),
        name="execution_create",
    ),
    path(
        "project/<int:project_pk>/test-run/create/",
        views.TestRunCreateView.as_view(),
        name="test_run_create",
    ),
    path(
        "test-run/<int:pk>/execute/",
        views.TestRunExecuteView.as_view(),
        name="test_run_execute",
    ),
    path(
        "test-run/<int:pk>/", views.TestRunDetailView.as_view(), name="test_run_detail"
    ),
]
