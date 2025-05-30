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

    def get_total_test_cases(self):
        """プロジェクト内の全テストケース数を返す"""
        return TestCase.objects.filter(suite__project=self).count()


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

    __test__ = False


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

    __test__ = False


class TestStep(models.Model):
    test_case = models.ForeignKey(
        "TestCase", on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveIntegerField()
    description = models.TextField(help_text="実行する操作の内容")
    expected_result = models.TextField(help_text="この操作で期待される結果", blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["test_case", "order"]

    def __str__(self):
        return f"ステップ {self.order}: {self.description[:50]}"

    __test__ = False


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

    def __str__(self):
        return f"{self.project.name} - {self.name} (started_at: {self.started_at.strftime('%Y-%m-%d %H:%M')})"

    def skip_remainings(self):
        """未実行のテストケースをスキップに変更し、同時にこのTestSessionを完了状態にする"""
        self.executions.filter(status="NOT_TESTED").update(
            status="SKIPPED",
            executed_at=timezone.now(),
            notes="一括スキップ",
        )
        self.complete()

    def complete(self):
        """テストセッションを完了状態にする"""
        self.completed_at = timezone.now()
        self.save()

    def initialize_executions(self, selected_test_cases):
        """選択されたテストケースに対するTestExecutionを作成する"""
        for test_case in selected_test_cases:
            TestExecution.objects.get_or_create(
                test_session=self,
                test_case=test_case,
                defaults={
                    "environment": self.environment,
                    "executed_by": self.executed_by,
                },
            )

    def get_next_execution(self):
        """次に実行すべきTestExecutionを返す"""
        return self.executions.filter(status="NOT_TESTED").first()

    def get_available_cases_and_executions(self):
        ret = []
        for execution in self.executions.all().select_related('test_case').order_by('test_case__title'):
            ret.append((execution.test_case, execution))
        return ret

    def get_involved_suites(self):
        case_ids = self.executions.values_list('test_case_id', flat=True)
        return TestSuite.objects.filter(test_cases__id__in=case_ids).distinct().order_by('name')

    __test__ = False


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
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="NOT_TESTED"
    )
    notes = models.TextField(blank=True)
    result_detail = models.TextField("詳細", blank=True)
    environment = models.CharField(max_length=200, blank=True)

    def __str__(self):
        if self.status == "NOT_TESTED":
            return f"{self.id} {self.test_case.title} - {self.status}"
        else:
            return f"{self.id} {self.test_case.title} - {self.status} (executed_at: {self.executed_at.strftime('%Y-%m-%d %H:%M')})"

    __test__ = False
