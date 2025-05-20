import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationViews:
    def test_login_page_renders(self, client):
        url = reverse("login")
        response = client.get(url)
        assert response.status_code == 200
        assert "ログイン" in response.content.decode()
        assert "ユーザー名" in response.content.decode()
        assert "パスワード" in response.content.decode()

    def test_login_functionality(self, client):
        # Create a test user
        user = User.objects.create_user(username="testuser", password="testpassword123")

        # Test login with correct credentials
        url = reverse("login")
        response = client.post(
            url,
            {
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 302  # Redirect after successful login
        assert response.url == reverse("project_list")  # Default redirect to home

        # Test login with incorrect credentials
        response = client.post(
            url,
            {
                "username": "testuser",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 200  # Stay on login page
        assert (
            "ユーザー名またはパスワードが正しくありません" in response.content.decode()
        )

    @pytest.mark.parametrize(
        "url_name,kwargs",
        [
            ("project_detail", {"pk": 1}),
            ("suite_detail", {"pk": 1}),
            ("case_detail", {"pk": 1}),
            ("test_session_detail", {"pk": 1}),
            ("test_session_execute", {"pk": 1}),
            ("case_list", {}),
        ],
    )
    def test_login_required(self, client, url_name, kwargs):
        url = reverse(url_name, kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_project_list_accessible_without_login(self, client):
        url = reverse("project_list")
        response = client.get(url)
        assert response.status_code == 200
