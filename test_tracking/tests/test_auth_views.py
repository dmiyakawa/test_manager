import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAuthenticationViews:
    @pytest.mark.parametrize("url_name,kwargs", [
        ("project_detail", {"pk": 1}),
        ("suite_detail", {"pk": 1}),
        ("case_detail", {"pk": 1}),
        ("test_session_detail", {"pk": 1}),
        ("test_session_execute", {"pk": 1}),
        ("case_list", {}),
    ])
    def test_login_required(self, client, url_name, kwargs):
        url = reverse(url_name, kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith('/accounts/login/')

    def test_project_list_accessible_without_login(self, client):
        url = reverse("project_list")
        response = client.get(url)
        assert response.status_code == 200
