import csv
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from .models import Project, TestSuite, TestCase, TestStep


class ProjectCSVExportView(View):
    @method_decorator(login_required)
    def get(self, request, project_id, *args, **kwargs):
        project = get_object_or_404(Project, pk=project_id)
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="test_data_{project.name}.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow([
            "type",
            "id",
            "parent_id",
            "name",
            "description",
            "prerequisites",
            "status",
            "priority",
            "expected_result"
        ])

        # プロジェクトのエクスポート
        writer.writerow([
            "project",
            project.id,
            "",  # 親ID（プロジェクトの場合は空）
            project.name,
            project.description,
            "",  # prerequisites
            "",  # status
            "",  # priority
            ""   # expected_result
        ])

        # プロジェクトに属するテストスイートのエクスポート
        for suite in project.test_suites.all():
            writer.writerow([
                "suite",
                suite.id,
                project.id,  # 親ID（プロジェクトID）
                suite.name,
                suite.description,
                "",  # prerequisites
                "",  # status
                "",  # priority
                ""   # expected_result
            ])

            # スイートに属するテストケースのエクスポート
            for case in suite.test_cases.all():
                writer.writerow([
                    "case",
                    case.id,
                    suite.id,  # 親ID（スイートID）
                    case.title,
                    case.description,
                    case.prerequisites,
                    case.status,
                    case.priority,
                    ""  # expected_result
                ])

                # テストケースに属するステップのエクスポート
                for step in case.steps.all():
                    writer.writerow([
                        "step",
                        step.id,
                        case.id,  # 親ID（ケースID）
                        str(step.order),  # orderをname列として使用
                        step.description,
                        "",  # prerequisites
                        "",  # status
                        "",  # priority
                        step.expected_result
                    ])

        return response


class CSVExportView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="test_data.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow([
            "type",
            "id",
            "parent_id",
            "name",
            "description",
            "prerequisites",
            "status",
            "priority",
            "expected_result"
        ])

        # プロジェクトのエクスポート
        for project in Project.objects.all():
            writer.writerow([
                "project",
                project.id,
                "",  # 親ID（プロジェクトの場合は空）
                project.name,
                project.description,
                "",  # prerequisites
                "",  # status
                "",  # priority
                ""   # expected_result
            ])

            # プロジェクトに属するテストスイートのエクスポート
            for suite in project.test_suites.all():
                writer.writerow([
                    "suite",
                    suite.id,
                    project.id,  # 親ID（プロジェクトID）
                    suite.name,
                    suite.description,
                    "",  # prerequisites
                    "",  # status
                    "",  # priority
                    ""   # expected_result
                ])

                # スイートに属するテストケースのエクスポート
                for case in suite.test_cases.all():
                    writer.writerow([
                        "case",
                        case.id,
                        suite.id,  # 親ID（スイートID）
                        case.title,
                        case.description,
                        case.prerequisites,
                        case.status,
                        case.priority,
                        ""  # expected_result
                    ])

                    # テストケースに属するステップのエクスポート
                    for step in case.steps.all():
                        writer.writerow([
                            "step",
                            step.id,
                            case.id,  # 親ID（ケースID）
                            str(step.order),  # orderをname列として使用
                            step.description,
                            "",  # prerequisites
                            "",  # status
                            "",  # priority
                            step.expected_result
                        ])

        return response


class CSVImportView(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return HttpResponse("No file uploaded", status=400)

        # CSVファイルの文字コードを自動判定
        try:
            import chardet
            raw_data = csv_file.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]
            csv_content = raw_data.decode(encoding)
        except Exception:
            # デフォルトでUTF-8を使用
            csv_file.seek(0)
            csv_content = csv_file.read().decode("utf-8")

        lines = csv_content.splitlines()
        if not lines:
            raise ValueError("Empty CSV file")

        # ヘッダー行を取得
        headers = [h.strip() for h in lines[0].split(",")]
        if len(headers) != 9:  # 必要なカラム数を確認
            raise ValueError("Invalid CSV format: incorrect number of columns")

        # 必要なヘッダーが存在することを確認
        required_headers = [
            "type", "id", "parent_id", "name", "description",
            "prerequisites", "status", "priority", "expected_result"
        ]
        if not all(h in headers for h in required_headers):
            raise ValueError("Invalid CSV format: missing required headers")

        # DictReaderを作成
        reader = csv.DictReader(lines)
        
        # 一時保存用の辞書
        imported_objects = {
            "project": {},
            "suite": {},
            "case": {},
            "step": {}
        }

        try:
            with transaction.atomic():
                for row in reader:
                    try:
                        record_type = row["type"]
                        record_id = int(row["id"])
                        parent_id = row["parent_id"]
                        if parent_id:
                            parent_id = int(parent_id)
                        name = row["name"]
                        description = row["description"]
                        if record_type not in ["project", "suite", "case", "step"]:
                            raise ValueError(f"Invalid record type: {record_type}")

                        if record_type == "project":
                            obj, created = Project.objects.update_or_create(
                                id=record_id,
                                defaults={
                                    "name": name,
                                    "description": description
                                }
                            )
                            imported_objects["project"][record_id] = obj

                        elif record_type == "suite":
                            project = imported_objects["project"].get(parent_id)
                            if not project:
                                project = Project.objects.get(id=parent_id)
                                imported_objects["project"][parent_id] = project

                            obj, created = TestSuite.objects.update_or_create(
                                id=record_id,
                                defaults={
                                    "project": project,
                                    "name": name,
                                    "description": description
                                }
                            )
                            imported_objects["suite"][record_id] = obj

                        elif record_type == "case":
                            suite = imported_objects["suite"].get(parent_id)
                            if not suite:
                                suite = TestSuite.objects.get(id=parent_id)
                                imported_objects["suite"][parent_id] = suite

                            obj, created = TestCase.objects.update_or_create(
                                id=record_id,
                                defaults={
                                    "suite": suite,
                                    "title": name,
                                    "description": description,
                                    "prerequisites": row["prerequisites"] or "",
                                    "status": row["status"] or "DRAFT",
                                    "priority": row["priority"] or "MEDIUM"
                                }
                            )
                            imported_objects["case"][record_id] = obj

                        elif record_type == "step":
                            case = imported_objects["case"].get(parent_id)
                            if not case:
                                case = TestCase.objects.get(id=parent_id)
                                imported_objects["case"][parent_id] = case

                            obj, created = TestStep.objects.update_or_create(
                                id=record_id,
                                defaults={
                                    "test_case": case,
                                    "order": int(name),  # orderはname列から取得
                                    "description": description,
                                    "expected_result": row["expected_result"] or ""
                                }
                            )
                            imported_objects["step"][record_id] = obj

                    except (KeyError, ValueError, json.JSONDecodeError) as e:
                        print(f"Row data: {row}")  # デバッグ用
                        print(f"Error: {str(e)}")  # デバッグ用
                        raise ValueError(f"Invalid data format: {str(e)}")

            return HttpResponse("Successfully imported all records")
        except ValueError as e:
            print(f"Validation error: {str(e)}")  # デバッグ用
            return HttpResponse(f"Import failed: {str(e)}", status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")  # デバッグ用
            return HttpResponse(f"Import failed: Unexpected error occurred", status=400)
