from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from test_manager.models import Project


class ProjectListAPITests(APITestCase):
    def test_can_list_projects(self):
        """
        プロジェクト一覧を取得できることを確認します。
        """
        Project.objects.create(name="Project 1", description="Description 1")
        Project.objects.create(name="Project 2", description="Description 2")
        url = reverse("project-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_can_create_project(self):
        """
        プロジェクトをAPI経由で作成できることを確認します。
        """
        url = reverse("project-list")
        data = {"name": "New Project", "description": "New Description"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, "New Project")
