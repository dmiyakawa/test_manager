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


@pytest.mark.django_db
class TestUserManagementViews:
    @pytest.fixture
    def superuser(self):
        return User.objects.create_superuser(
            username="superuser", password="superpassword123", email="super@example.com"
        )

    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(
            username="regularuser",
            password="regularpassword123",
            email="regular@example.com",
        )

    def test_user_list_view_permissions(self, client, superuser, regular_user):
        # Anonymous user
        url = reverse("user_list")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse("login"))

        # Regular user
        client.login(username="regularuser", password="regularpassword123")
        response = client.get(url)
        assert response.status_code == 403  # Forbidden for non-superusers
        client.logout()

        # Superuser
        client.login(username="superuser", password="superpassword123")
        response = client.get(url)
        assert response.status_code == 200
        assert "ユーザー管理" in response.content.decode()
        assert "superuser" in response.content.decode()
        assert "regularuser" in response.content.decode()

    def test_user_update_view_permissions_and_functionality(
        self, client, superuser, regular_user
    ):
        url = reverse("user_update", kwargs={"pk": regular_user.pk})

        # Anonymous user
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse("login"))

        # Regular user
        client.login(username="regularuser", password="regularpassword123")
        response = client.get(url)
        assert response.status_code == 403
        client.logout()

        # Superuser - GET
        client.login(username="superuser", password="superpassword123")
        response = client.get(url)
        assert response.status_code == 200
        assert f"ユーザー編集: {regular_user.username}" in response.content.decode()

        # Superuser - POST (update names)
        new_first_name = "Reg"
        new_last_name = "Ular"
        response = client.post(
            url,
            {
                "first_name": new_first_name,
                "last_name": new_last_name,
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("user_list")
        
        regular_user.refresh_from_db()
        assert regular_user.first_name == new_first_name
        assert regular_user.last_name == new_last_name

        # 302のresponseにはcontextは含まれないのでリダイレクト先の messages を確認する
        response = client.get(response.url)
        assert response.status_code == 200
        assert response.context is not None
        messages = [m.message for m in list(response.context['messages'])]
        assert "ユーザー情報を更新しました。" in messages

    def test_user_token_manage_view_permissions_and_functionality(
        self, client, superuser, regular_user
    ):
        from rest_framework.authtoken.models import Token

        url = reverse("user_token_manage", kwargs={"pk": regular_user.pk})

        # Anonymous user
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse("login"))

        # Regular user
        client.login(username="regularuser", password="regularpassword123")
        response = client.get(url)
        assert response.status_code == 403
        client.logout()

        # Superuser - GET (token creation)
        client.login(username="superuser", password="superpassword123")
        response = client.get(url)
        assert response.status_code == 200
        assert f"APIトークン管理: {regular_user.username}" in response.content.decode()
        token_obj = Token.objects.get(user=regular_user)
        assert token_obj.key in response.content.decode()
        messages = [m.message for m in list(response.context["messages"])]
        assert f"{regular_user.username} のAPIトークンを新規発行しました。" in messages

        original_token_key = token_obj.key

        # Superuser - POST (token re-generation)
        response = client.post(url)
        assert response.status_code == 200
        regular_user.refresh_from_db()
        new_token_obj = Token.objects.get(user=regular_user)
        assert new_token_obj.key != original_token_key
        assert new_token_obj.key in response.content.decode()
        messages = [m.message for m in list(response.context["messages"])]
        assert f"{regular_user.username} のAPIトークンを再発行しました。" in messages
