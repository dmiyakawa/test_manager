from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Project, TestSuite, TestSession, TestExecution, TestCase
from .serializers import (
    ProjectSerializer,
    TestSuiteSerializer,
    TestSessionSerializer,
    TestCaseSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProjectTestSuiteList(generics.ListAPIView):
    serializer_class = TestSuiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        return TestSuite.objects.filter(project_id=project_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class TestSessionList(generics.ListCreateAPIView):
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        return TestSession.objects.filter(project=project).order_by("-started_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        test_session = serializer.save(
            executed_by=request.user.username, project=project
        )

        available_suites_data = request.data.get("available_suites", [])
        if (
            not available_suites_data
        ):  # If not provided, use all suites from the project
            available_suites = TestSuite.objects.filter(project=project)
        else:
            available_suites = []
            for suite_id in available_suites_data:
                suite = get_object_or_404(
                    TestSuite, pk=suite_id, project=project
                )  # Ensure suite belongs to project
                available_suites.append(suite)

        test_session.available_suites.set(available_suites)
        test_session.initialize_executions()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def execute_test_case(request, test_session_id):
    """
    POSTの場合は指定されたTestCaseについて状況を記録する。
    """
    try:
        test_session = get_object_or_404(TestSession, pk=test_session_id)

        if request.method == "POST":
            test_case = TestCase.objects.get(id=request.data.get("test_case_id"))
            execution = test_session.executions.get(test_case=test_case)

            # テスト実行フォームからの送信の場合
            execution.status = request.data["status"]
            execution.executed_by = test_session.executed_by
            execution.executed_at = timezone.now()
            execution.environment = test_session.environment
            execution.result_detail = request.data.get("result_detail", "")
            execution.notes = request.data.get("notes", "")
            execution.save()

        executions = test_session.executions.all()
        total_count = executions.count()
        completed_count = executions.exclude(status="NOT_TESTED").count()
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0

        remaining_test_cases = [
            TestCaseSerializer(ne.test_case).data
            for ne in executions.filter(status="NOT_TESTED")
        ]
        if not remaining_test_cases:
            if not test_session.completed_at:
                test_session.complete()
            response_data = {
                "test_session_id": test_session.id,
                "test_session_name": test_session.name,
                "completed": True,
                "total_count": total_count,
                "completed_count": completed_count,
                "progress": 100,
                "remaining_test_cases": [],
            }
        else:
            response_data = {
                "test_session_id": test_session.id,
                "test_session_name": test_session.name,
                "completed": False,
                "total_count": total_count,
                "completed_count": completed_count,
                "progress": progress,
                "remaining_test_cases": remaining_test_cases,
            }
        return Response(response_data, status=status.HTTP_200_OK)
    except TestSession.DoesNotExist:
        return Response(
            {"error": "TestSession not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except TestCase.DoesNotExist:
        return Response(
            {"error": "TestCase not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except TestExecution.DoesNotExist:
        return Response(
            {"error": "TestExecution not found"}, status=status.HTTP_404_NOT_FOUND
        )


class TestCaseDetail(generics.RetrieveAPIView):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
