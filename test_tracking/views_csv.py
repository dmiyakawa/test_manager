import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import Project, TestSuite, TestCase, TestStep

class CSVExportView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        export_type = kwargs.get('type')
        
        # CSVファイル名とヘッダーの定義
        file_configs = {
            'projects': {
                'filename': 'projects.csv',
                'headers': ['id', 'name', 'description'],
                'queryset': Project.objects.all(),
                'row_func': lambda obj: [obj.id, obj.name, obj.description]
            },
            'suites': {
                'filename': 'suites.csv',
                'headers': ['id', 'project_id', 'name', 'description'],
                'queryset': TestSuite.objects.all(),
                'row_func': lambda obj: [obj.id, obj.project_id, obj.name, obj.description]
            },
            'cases': {
                'filename': 'cases.csv',
                'headers': ['id', 'suite_id', 'title', 'description', 'prerequisites', 'status', 'priority'],
                'queryset': TestCase.objects.all(),
                'row_func': lambda obj: [
                    obj.id, obj.suite_id, obj.title, obj.description,
                    obj.prerequisites, obj.status, obj.priority
                ]
            },
            'steps': {
                'filename': 'steps.csv',
                'headers': ['id', 'case_id', 'order', 'description', 'expected_result'],
                'queryset': TestStep.objects.all(),
                'row_func': lambda obj: [
                    obj.id, obj.test_case_id, obj.order,
                    obj.description, obj.expected_result
                ]
            }
        }

        config = file_configs.get(export_type)
        if not config:
            return HttpResponse('Invalid export type', status=400)

        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{config["filename"]}"'},
        )

        writer = csv.writer(response)
        writer.writerow(config['headers'])

        for obj in config['queryset']:
            writer.writerow(config['row_func'](obj))

        return response

class CSVImportView(View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        import_type = kwargs.get('type')
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return HttpResponse('No file uploaded', status=400)

        # CSVファイルの文字コードを自動判定
        try:
            import chardet
            raw_data = csv_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            csv_content = raw_data.decode(encoding)
        except Exception:
            # デフォルトでUTF-8を使用
            csv_file.seek(0)
            csv_content = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_content.splitlines())
        
        # インポート処理の定義
        import_handlers = {
            'projects': self._import_projects,
            'suites': self._import_suites,
            'cases': self._import_cases,
            'steps': self._import_steps
        }

        handler = import_handlers.get(import_type)
        if not handler:
            return HttpResponse('Invalid import type', status=400)

        try:
            imported_count = handler(reader)
            return HttpResponse(f'Successfully imported {imported_count} records')
        except Exception as e:
            return HttpResponse(f'Import failed: {str(e)}', status=400)

    def _import_projects(self, reader):
        count = 0
        for row in reader:
            Project.objects.update_or_create(
                id=row['id'],
                defaults={
                    'name': row['name'],
                    'description': row['description']
                }
            )
            count += 1
        return count

    def _import_suites(self, reader):
        count = 0
        for row in reader:
            TestSuite.objects.update_or_create(
                id=row['id'],
                defaults={
                    'project_id': row['project_id'],
                    'name': row['name'],
                    'description': row['description']
                }
            )
            count += 1
        return count

    def _import_cases(self, reader):
        count = 0
        for row in reader:
            TestCase.objects.update_or_create(
                id=row['id'],
                defaults={
                    'suite_id': row['suite_id'],
                    'title': row['title'],
                    'description': row['description'],
                    'prerequisites': row['prerequisites'],
                    'status': row['status'],
                    'priority': row['priority']
                }
            )
            count += 1
        return count

    def _import_steps(self, reader):
        count = 0
        for row in reader:
            TestStep.objects.update_or_create(
                id=row['id'],
                defaults={
                    'test_case_id': row['case_id'],
                    'order': row['order'],
                    'description': row['description'],
                    'expected_result': row['expected_result']
                }
            )
            count += 1
        return count
