from django.contrib import admin
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.authtoken import views as authtoken_views
from rest_framework.urlpatterns import format_suffix_patterns

from . import views, views_csv, api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "admin-dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"
    ),
    path("csv/export/", views_csv.CSVExportView.as_view(), name="csv_export"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path(
        "users/<int:pk>/token/",
        views.UserTokenManageView.as_view(),
        name="user_token_manage",
    ),
    path(
        "project/<int:project_id>/csv/export/",
        views_csv.ProjectCSVExportView.as_view(),
        name="project_csv_export",
    ),
    path("csv/import/", views_csv.CSVImportView.as_view(), name="csv_import"),
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
    path(
        "case/<int:case_pk>/steps/", views.TestStepListView.as_view(), name="step_list"
    ),
    path("case/<int:pk>/edit/", views.TestCaseUpdateView.as_view(), name="case_update"),
    path(
        "case/<int:pk>/delete/", views.TestCaseDeleteView.as_view(), name="case_delete"
    ),
    path("cases/", views.TestCaseListView.as_view(), name="case_list"),
    path(
        "case/<int:case_pk>/execute/",
        views.TestExecutionCreateView.as_view(),
        name="execution_create",
    ),
    path(
        "project/<int:project_pk>/test-session/create/",
        views.TestSessionCreateView.as_view(),
        name="test_session_create",
    ),
    path(
        "test-session/<int:pk>/execute/",
        views.TestSessionExecuteView.as_view(),
        name="test_session_execute",
    ),
    path(
        "test-session/<int:pk>/skip-all/",
        views.TestSessionSkipAllView.as_view(),
        name="test_session_skip_all",
    ),
    path(
        "test-session/<int:pk>/",
        views.TestSessionDetailView.as_view(),
        name="test_session_detail",
    ),
    path(
        "test-sessions/", views.TestSessionListView.as_view(), name="test_session_list"
    ),
    # APIスキーマ
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        "api/api-token-auth/", authtoken_views.obtain_auth_token, name="api_token_auth"
    ),
    # プロジェクトAPI
    path("api/projects/", api.ProjectList.as_view(), name="project-list"),
    path(
        "api/projects/<int:project_id>/testsuites/",
        api.ProjectTestSuiteList.as_view(),
        name="project-test-suite-list",
    ),
    path(
        "api/testcases/<int:pk>/",
        api.TestCaseDetail.as_view(),
        name="testcase-detail",
    ),
    # テストセッションAPI
    path(
        "api/projects/<int:project_id>/test-sessions/",
        api.TestSessionCreate.as_view(),
        name="test-session-create",
    ),
    path(
        "api/test-sessions/<int:test_session_id>/execute/",
        api.execute_test_case,
        name="execute-test-case",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
