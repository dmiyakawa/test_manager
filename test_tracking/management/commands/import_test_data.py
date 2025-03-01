import csv
from django.core.management.base import BaseCommand
from test_tracking.models import Project, TestSuite, TestCase, TestStep

class Command(BaseCommand):
    help = 'CSVファイルからテストデータをインポートします'

    def handle(self, *args, **options):
        # プロジェクトのインポート
        self.stdout.write('プロジェクトをインポートしています...')
        with open('test_data/projects.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Project.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'name': row['name'],
                        'description': row['description']
                    }
                )
        self.stdout.write(self.style.SUCCESS('プロジェクトのインポートが完了しました'))

        # テストスイートのインポート
        self.stdout.write('テストスイートをインポートしています...')
        with open('test_data/suites.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                TestSuite.objects.update_or_create(
                    id=row['id'],
                    defaults={
                        'project_id': row['project_id'],
                        'name': row['name'],
                        'description': row['description']
                    }
                )
        self.stdout.write(self.style.SUCCESS('テストスイートのインポートが完了しました'))

        # テストケースのインポート
        self.stdout.write('テストケースをインポートしています...')
        with open('test_data/cases.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
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
        self.stdout.write(self.style.SUCCESS('テストケースのインポートが完了しました'))

        # テストステップのインポート
        self.stdout.write('テストステップをインポートしています...')
        with open('test_data/steps.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
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
        self.stdout.write(self.style.SUCCESS('テストステップのインポートが完了しました'))

        self.stdout.write(self.style.SUCCESS('全てのデータのインポートが完了しました'))
