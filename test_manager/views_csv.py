import csv
from logging import getLogger
import io

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from .models import Project, TestSuite, TestCase, TestStep


_logger = getLogger("views")

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
            "project_name",
            "type",
            "parent",
            "name",
            "description",
            "order",
            "status",
            "priority",
            "prerequisites",
            "expected_result"
        ])

        # プロジェクトのエクスポート
        writer.writerow([
            project.name,  # project_name
            "project",  # type
            "",  # parent（プロジェクトの場合は空）
            project.name,  # name
            project.description,  # description
            "",  # order
            "",  # status
            "",  # priority
            "",  # prerequisites
            ""  # expected_result
        ])

        # プロジェクトに属するテストスイートのエクスポート
        for suite in project.test_suites.all():
            writer.writerow([
                project.name,  # project_name
                "suite",  # type
                project.name,  # parent（プロジェクト名）
                suite.name,  # name
                suite.description,  # description
                "",  # order
                "",  # status
                "",  # priority
                "",  # prerequisites
                ""  # expected_result
            ])

            # スイートに属するテストケースのエクスポート
            for case in suite.test_cases.all():
                writer.writerow([
                    project.name,  # project_name
                    "case",  # type
                    suite.name,  # parent（スイート名）
                    case.title,  # name
                    case.description,  # description
                    "",  # order
                    case.status,  # status
                    case.priority,  # priority
                    case.prerequisites,  # prerequisites
                    ""  # expected_result
                ])

                # テストケースに属するステップのエクスポート
                for step in case.steps.all():
                    writer.writerow([
                        project.name,  # project_name
                        "step",  # type
                        case.title,  # parent（テストケースのタイトル）
                        "",  # name（空欄）
                        step.description,  # description
                        str(step.order),  # order
                        "",  # status
                        "",  # priority
                        "",  # prerequisites
                        step.expected_result  # expected_result
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
            "project_name",
            "type",
            "parent",
            "name",
            "description",
            "order",
            "status",
            "priority",
            "prerequisites",
            "expected_result"
        ])

        # プロジェクトのエクスポート
        for project in Project.objects.all():
            writer.writerow([
                project.name,  # project_name
                "project",  # type
                "",  # parent（プロジェクトの場合は空）
                project.name,  # name
                project.description,  # description
                "",  # order
                "",  # status
                "",  # priority
                "",  # prerequisites
                ""  # expected_result
            ])

            # プロジェクトに属するテストスイートのエクスポート
            for suite in project.test_suites.all():
                writer.writerow([
                    project.name,  # project_name
                    "suite",  # type
                    project.name,  # parent（プロジェクト名）
                    suite.name,  # name
                    suite.description,  # description
                    "",  # order
                    "",  # status
                    "",  # priority
                    "",  # prerequisites
                    ""  # expected_result
                ])

                # スイートに属するテストケースのエクスポート
                for case in suite.test_cases.all():
                    writer.writerow([
                        project.name,  # project_name
                        "case",  # type
                        suite.name,  # parent（スイート名）
                        case.title,  # name
                        case.description,  # description
                        "",  # order
                        case.status,  # status
                        case.priority,  # priority
                        case.prerequisites,  # prerequisites
                        ""  # expected_result
                    ])

                    # テストケースに属するステップのエクスポート
                    for step in case.steps.all():
                        writer.writerow([
                            project.name,  # project_name
                            "step",  # type
                            case.title,  # parent（テストケースのタイトル）
                            "",  # name（空欄）
                            step.description,  # description
                            str(step.order),  # order
                            "",  # status
                            "",  # priority
                            "",  # prerequisites
                            step.expected_result  # expected_result
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
            _logger.debug(f"Try {encoding} for decoding a file")
            csv_content = raw_data.decode(encoding)
        except Exception:
            # デフォルトでUTF-8を使用する
            _logger.debug("Try utf-8 for decoding a file (fallback)")
            csv_file.seek(0)
            csv_content = csv_file.read().decode("utf-8")

        try:
            # CSVに改行が含まれていると破綻する。あくまでヘッダの雑判定のためだけに使うべき
            lines = csv_content.splitlines()
            if not lines:
                return HttpResponse("Empty CSV file", status=400)

            # ヘッダー行を取得して必要なカラムがあるかを確認する
            required_headers = {
                "type", "name", "description", "prerequisites",
                "status", "priority", "expected_result", "order",
                "project_name", "parent"
            }
            headers = [h.strip() for h in lines[0].split(",")]
            if len(headers) != 10:  # 必要なカラム数を確認
                return HttpResponse("Invalid CSV format: incorrect number of columns", status=400)

            if not all(h in headers for h in required_headers):
                return HttpResponse("Invalid CSV format: missing required headers", status=400)

            
            # 一時保存用の辞書
            imported_objects = {
                "project": {},
                "suite": {},
                "case": {},
                "step": {}
            }

            with transaction.atomic():
                current_project = None
                current_suite = None
                current_case = None

                # Excel方言の改行対応を含むCSVを読むためにファイルオブジェクトにくるむ                
                reader = csv.DictReader(io.StringIO(csv_content, newline=''))

                for row_num, row in enumerate(reader, 1):
                    # print(f"{row_num}: {row['expected_result']}", file=f, flush=True)
                    try:
                        record_type = row["type"]

                        if record_type == "project":
                            current_project, created = Project.objects.update_or_create(
                                name=row["name"],
                                defaults={
                                    "description": row["description"]
                                }
                            )
                            imported_objects["project"][row["name"]] = current_project

                        elif record_type == "suite":
                            project_name = row["project_name"]
                            if not project_name:
                                raise ValueError("Suite found without project_name")

                            current_project = imported_objects["project"].get(project_name)
                            if not current_project:
                                current_project = Project.objects.get(name=project_name)
                                imported_objects["project"][project_name] = current_project

                            current_suite, created = TestSuite.objects.update_or_create(
                                project=current_project,
                                name=row["name"],
                                defaults={
                                    "description": row["description"]
                                }
                            )
                            imported_objects["suite"][f"{project_name}:{row['name']}"] = current_suite

                        elif record_type == "case":
                            project_name = row["project_name"]
                            parent_name = row["parent"]  # スイート名
                            if not project_name or not parent_name:
                                raise ValueError("Case found without project_name or parent")

                            current_project = imported_objects["project"].get(project_name)
                            if not current_project:
                                current_project = Project.objects.get(name=project_name)
                                imported_objects["project"][project_name] = current_project

                            current_suite = TestSuite.objects.get(project=current_project, name=parent_name)
                            imported_objects["suite"][f"{project_name}:{parent_name}"] = current_suite

                            current_case, created = TestCase.objects.update_or_create(
                                suite=current_suite,
                                title=row["name"],
                                defaults={
                                    "description": row["description"],
                                    "prerequisites": row["prerequisites"] or "",
                                    "status": row["status"] or "DRAFT",
                                    "priority": row["priority"] or "MEDIUM"
                                }
                            )
                            imported_objects["case"][f"{parent_name}:{row['name']}"] = current_case

                        elif record_type == "step":
                            project_name = row["project_name"]
                            parent_name = row["parent"]  # テストケースのタイトル
                            if not project_name or not parent_name:
                                raise ValueError(f"Step found without project_name or parent (row_num: {row_num})")

                            if not row["order"]:
                                raise ValueError("Step order is required")

                            current_project = imported_objects["project"].get(project_name)
                            if not current_project:
                                current_project = Project.objects.get(name=project_name)
                                imported_objects["project"][project_name] = current_project

                            current_case = TestCase.objects.get(
                                suite__project=current_project,
                                title=parent_name
                            )

                            TestStep.objects.update_or_create(
                                test_case=current_case,
                                order=int(row["order"]),
                                defaults={
                                    "description": row["description"],
                                    "expected_result": row["expected_result"] or ""
                                }
                            )
                        else:
                            raise ValueError(f"Invalid record_type {record_type}")
                    except (KeyError, ValueError) as e:
                        raise ValueError(f"Invalid data format: {str(e)}")

            messages.success(request, "CSVファイルのインポートが完了しました")
            return redirect("project_list")
        except ValueError as e:
            return HttpResponse(f"Import failed: {str(e)}", status=400)
        except Exception as e:
            return HttpResponse(f"Import failed: Unexpected error occurred", status=400)
