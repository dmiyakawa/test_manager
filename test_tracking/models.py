from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("manage_project", "Can manage project settings and members"),
            ("edit_tests", "Can create and edit test cases"),
            ("execute_tests", "Can execute tests and record results"),
        ]

    def __str__(self):
        return self.name


class TestSuite(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="test_suites"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TestStep(models.Model):
    test_case = models.ForeignKey(
        "TestCase", on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveIntegerField()
    description = models.TextField(help_text="実行する操作の内容")
    expected_result = models.TextField(help_text="この操作で期待される結果")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["test_case", "order"]

    def __str__(self):
        return f"ステップ {self.order}: {self.description[:50]}"


class TestCase(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "下書き"),
        ("ACTIVE", "有効"),
        ("DEPRECATED", "非推奨"),
    ]

    PRIORITY_CHOICES = [
        ("HIGH", "高"),
        ("MEDIUM", "中"),
        ("LOW", "低"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    suite = models.ForeignKey(
        TestSuite, on_delete=models.CASCADE, related_name="test_cases"
    )
    prerequisites = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")
    priority = models.CharField(
        max_length=6, choices=PRIORITY_CHOICES, default="MEDIUM"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_ordered_steps(self):
        return self.steps.all()


class TestRun(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="test_runs"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    executed_by = models.CharField(max_length=100)
    environment = models.CharField(max_length=200)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    available_suites = models.ManyToManyField(
        TestSuite,
        related_name="available_test_runs",
        help_text="このテスト実行で選択可能なテストスイート"
    )

    def __str__(self):
        return f"{self.project.name} - {self.name} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"

    def complete(self):
        self.completed_at = timezone.now()
        self.save()

    def get_available_cases(self):
        """このテスト実行で選択可能なすべてのテストケースを返す"""
        return TestCase.objects.filter(suite__in=self.available_suites.all())


class TestExecution(models.Model):
    RESULT_CHOICES = [
        ("PASS", "合格"),
        ("FAIL", "不合格"),
        ("BLOCKED", "ブロック"),
        ("SKIPPED", "スキップ"),
    ]

    test_case = models.ForeignKey(
        TestCase, on_delete=models.CASCADE, related_name="executions"
    )
    test_run = models.ForeignKey(
        TestRun, on_delete=models.CASCADE, related_name="executions"
    )
    executed_by = models.CharField(max_length=100)
    executed_at = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    notes = models.TextField(blank=True)
    actual_result = models.TextField(blank=True)
    environment = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.test_case.title} - {self.executed_at.strftime('%Y-%m-%d %H:%M')}"
