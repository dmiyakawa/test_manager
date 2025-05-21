from rest_framework import serializers
from .models import Project, TestSuite, TestCase, TestSession


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ["id", "title", "description", "status", "priority"]


class TestSuiteSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()

    class Meta:
        model = TestSuite
        fields = ["id", "name", "description", "test_cases"]

    def get_test_cases(self, obj):
        request = self.context.get("request")
        if request and request.query_params.get("include_cases") == "true":
            return TestCaseSerializer(obj.test_cases.all(), many=True).data
        return []


class TestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSession
        fields = [
            "id",
            "project",
            "name",
            "description",
            "executed_by",
            "environment",
            "available_suites",
        ]
