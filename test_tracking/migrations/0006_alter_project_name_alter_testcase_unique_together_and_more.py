# Generated by Django 5.1.6 on 2025-03-01 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_tracking", "0005_alter_testrun_environment_alter_testrun_executed_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name="testcase",
            unique_together={("suite", "title")},
        ),
        migrations.AlterUniqueTogether(
            name="testsuite",
            unique_together={("project", "name")},
        ),
    ]
