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
    completed = serializers.SerializerMethodField()
    # New field to accept test case IDs for creation
    selected_case_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True # Assuming selecting cases is mandatory for API creation too
                      # If not, set required=False and handle default in API view
    )

    class Meta:
        model = TestSession
        fields = [
            "id",
            "project", # This is often read-only or set by the view context
            "name",
            "description",
            "executed_by", # Also often set by view context (request.user)
            "environment",
            # "available_suites", # REMOVED
            "selected_case_ids", # ADDED for input
            "completed",
        ]
        read_only_fields = ('project', 'executed_by', 'completed') # 'id' is also read-only by default

    def get_completed(self, obj):
        executions = obj.executions.all()
        if not executions.exists():
            # If no executions, it means no cases were selected, or they were all removed.
            # Consider if this means "completed" or not.
            # If a session can be created with no cases, it's arguably complete.
            # If cases are mandatory, then this state (no executions) shouldn't happen post-initialization.
            return True # Or False, depending on desired logic for empty sessions
        return all(execution.status != "NOT_TESTED" for execution in executions)

    def create(self, validated_data):
        selected_ids = validated_data.pop("selected_case_ids")
        
        # 'project' and 'executed_by' should be passed by the view to serializer.save()
        # and will be in validated_data if not read_only and provided in request,
        # or added by the view.
        # Example: project = validated_data.pop('project') or self.context['view'].kwargs.get('project_pk')
        # For now, assume they are correctly in validated_data or passed to TestSession.objects.create()
        # via **validated_data by the view's serializer.save(project=..., executed_by=...)

        test_session_instance = TestSession.objects.create(**validated_data)

        # Fetch TestCase objects. Ensure they belong to the session's project for security/consistency.
        # The project instance should be available, either from validated_data or context.
        project_instance = test_session_instance.project # Assumes project is set on instance

        # Validate that all selected_case_ids belong to the project
        selected_test_cases = TestCase.objects.filter(
            id__in=selected_ids,
            suite__project=project_instance
        )

        if len(selected_test_cases) != len(selected_ids):
            # Find missing/invalid IDs for a more informative error
            valid_ids_found = {tc.id for tc in selected_test_cases}
            invalid_ids = [id for id in selected_ids if id not in valid_ids_found]
            raise serializers.ValidationError(
                f"Invalid or non-project TestCase IDs: {invalid_ids}. "
                f"Ensure all selected cases belong to project '{project_instance.name}'."
            )
        
        if not selected_test_cases.exists() and self.fields['selected_case_ids'].required:
             raise serializers.ValidationError("At least one valid test case must be selected.")


        # Call the modified initialize_executions method
        # This method is now on the model instance.
        test_session_instance.initialize_executions(selected_test_cases)
        
        return test_session_instance

    # We might need a 'test_cases' field for read operations if we want to list
    # the cases associated with a session via its executions.
    # For example, a SerializerMethodField:
    # test_cases = TestCaseSerializer(many=True, read_only=True, source='get_session_test_cases')
    # def get_session_test_cases(self, obj):
    # return [execution.test_case for execution in obj.executions.all().select_related('test_case')]
    # This would go into Meta.fields for output. For now, focusing on create.
