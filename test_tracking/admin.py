from django.contrib import admin
from .models import Project, TestSuite, TestCase, TestRun, TestExecution


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "suite",
        "executed_by",
        "environment",
        "started_at",
        "completed_at",
    )
    list_filter = ("suite", "environment", "completed_at")
    search_fields = ("name", "description", "executed_by")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ("title", "suite", "status", "priority", "created_at")
    list_filter = ("status", "priority", "suite")
    search_fields = ("title", "description")


@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ("test_case", "result", "executed_by", "executed_at", "environment")
    list_filter = ("result", "environment")
    search_fields = ("test_case__title", "notes", "executed_by")
