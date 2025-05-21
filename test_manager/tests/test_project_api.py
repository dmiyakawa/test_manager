from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from test_manager.models import Project

User = get_user_model()


class ProjectListAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )
        self.token = Token.objects.create(user=self.user)
        self.project1 = Project.objects.create(
            name="Project 1", description="Description 1"
        )
        self.project2 = Project.objects.create(
            name="Project 2", description="Description 2"
        )
        self.url = reverse("project-list")

    def test_list_projects_unauthenticated(self):
        """
        認証なしでプロジェクト一覧を取得しようとすると401エラーになることを確認します。
        """
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_projects_authenticated(self):
        """
        認証済みユーザーがプロジェクト一覧を取得できることを確認します。
        """
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        project_names = [p["name"] for p in response.data]
        self.assertIn("Project 1", project_names)
        self.assertIn("Project 2", project_names)

    def test_create_project_unauthenticated(self):
        """
        認証なしでプロジェクトを作成しようとすると401エラーになることを確認します。
        """
        data = {"name": "New Project Unauth", "description": "New Description"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_project_authenticated(self):
        """
        認証済みユーザーがAPI経由でプロジェクトを作成できることを確認します。
        """
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {"name": "New Project Auth", "description": "New Description"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 3)  # setUpで2つ作成済み
        self.assertTrue(Project.objects.filter(name="New Project Auth").exists())


class APITokenAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )
        self.url = reverse("api_token_auth")

    def test_obtain_token_success(self):
        """
        正しい認証情報でAPIトークンを取得できることを確認します。
        """
        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertTrue(
            Token.objects.filter(user=self.user, key=response.data["token"]).exists()
        )

    def test_obtain_token_failure_wrong_password(self):
        """
        誤ったパスワードでAPIトークンを取得しようとすると400エラーになることを確認します。
        """
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_obtain_token_failure_nonexistent_user(self):
        """
        存在しないユーザーでAPIトークンを取得しようとすると400エラーになることを確認します。
        """
        data = {"username": "nonexistent", "password": "somepassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)
