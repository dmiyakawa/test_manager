from rest_framework import serializers
from .models import Project, TestSuite, TestCase, TestStep, TestSession
from django.shortcuts import get_object_or_404
from .models import TestSuite, TestExecution


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestStep
        fields = ["id", "order", "description", "expected_result"]

    __test__ = False

class TestCaseSerializer(serializers.ModelSerializer):
    steps = TestStepSerializer(many=True, read_only=True)

    class Meta:
        model = TestCase
        fields = ["id", "title", "description", "status", "priority", "steps"]

    __test__ = False


class TestSuiteSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()

    class Meta:
        model = TestSuite
        fields = ["id", "name", "description", "test_cases"]

    def get_test_cases(self, obj):
        request = self.context.get("request")
        if request and request.query_params.get("include_cases") == "true":
            return TestCaseSerializer(obj.test_cases.all(), many=True).data
        # テストケースが「一つもない」ことと、テストケースを返却していないことを区別するため
        # テストケースを返却していない場合として空のリストではなくNoneを返す
        return None

    __test__ = False


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

    def create(self, validated_data):
        available_suites_data = validated_data.pop("available_suites", [])
        test_session = TestSession.objects.create(**validated_data)
        test_session.available_suites.set(available_suites_data)
        test_session.initialize_executions()

        return test_session
