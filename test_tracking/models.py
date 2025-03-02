from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
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

    class Meta:
        unique_together = ["project", "name"]

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

    class Meta:
        unique_together = ["suite", "title"]

    def __str__(self):
        return self.title

    def get_ordered_steps(self):
        return self.steps.all()


class TestSession(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="test_sessions"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    executed_by = models.CharField(max_length=100, blank=True)
    environment = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    # 完了した時刻。完了フラグの意味も兼ねる
    completed_at = models.DateTimeField(null=True, blank=True)
    available_suites = models.ManyToManyField(
        TestSuite,
        related_name="available_test_sessions",
        help_text="このテストセッションで選択可能なテストスイート"
    )

    def __str__(self):
        return f"{self.project.name} - {self.name} (started_at: {self.started_at.strftime('%Y-%m-%d %H:%M')})"

    def complete(self):
        self.completed_at = timezone.now()
        self.save()

    def initialize_executions(self):
        """選択されたテストケースに対するTestExecutionを作成する"""
        for test_case in self.get_available_cases():
            TestExecution.objects.get_or_create(
                test_session=self,
                test_case=test_case,
                defaults={
                    'environment': self.environment,
                    'executed_by': self.executed_by,
                }
            )

    def get_next_execution(self):
        """次に実行すべきTestExecutionを返す"""
        return self.executions.filter(status="NOT_TESTED").first()

    def get_available_cases(self) -> TestCase:
        """このテスト実行で選択可能なすべてのテストケースを返す"""
        return TestCase.objects.filter(suite__in=self.available_suites.all())

    def get_available_cases_and_executions(self):
        ret = []
        for test_case in self.get_available_cases():
            execution = self.executions.filter(test_case=test_case).first()
            ret.append((test_case, execution))
        return ret


class TestExecution(models.Model):
    STATUS_CHOICES = [
        ("NOT_TESTED", "未テスト"),
        ("PASS", "合格"),
        ("FAIL", "不合格"),
        ("BLOCKED", "ブロック"),
        ("SKIPPED", "スキップ"),
    ]

    test_case = models.ForeignKey(
        TestCase, on_delete=models.CASCADE, related_name="executions"
    )
    test_session = models.ForeignKey(
        TestSession, on_delete=models.CASCADE, related_name="executions"
    )
    executed_by = models.CharField(max_length=100, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="NOT_TESTED")
    notes = models.TextField(blank=True)
    result_detail = models.TextField("詳細", blank=True)
    environment = models.CharField(max_length=200, blank=True)

    def __str__(self):
        if self.status == "NOT_TESTED":
            return f"{self.test_case.title} - ({self.status})"
        else:
            return f"{self.test_case.title} - {self.status} (executed_at: {self.executed_at.strftime('%Y-%m-%d %H:%M')})"
