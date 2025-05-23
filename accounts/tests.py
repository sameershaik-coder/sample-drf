import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .factories import UserFactory, AdminUserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def admin_user():
    return AdminUserFactory()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.mark.django_db
class TestUserRegistration:
    def test_user_registration_successful(self, api_client):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'email' in response.data

    def test_user_registration_password_mismatch(self, api_client):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_invalid_email(self, api_client):
        url = reverse('register')
        data = {
            'email': 'invalid-email',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserAuthentication:
    def test_login_successful(self, api_client, user):
        url = reverse('login')
        data = {
            'email': user.email,
            'password': 'testpass123'  # This should match the password in UserFactory
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == user.email

    def test_login_invalid_credentials(self, api_client):
        url = reverse('login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, user):
        user.is_active = False
        user.save()
        url = reverse('login')
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data

    def test_logout_successful(self, authenticated_client):
        # First login to get refresh token
        login_url = reverse('login')
        data = {
            'email': authenticated_client.handler._force_user.email,
            'password': 'testpass123'
        }
        login_response = authenticated_client.post(login_url, data)
        refresh_token = login_response.data['refresh']

        # Then logout
        logout_url = reverse('logout')
        response = authenticated_client.post(logout_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Successfully logged out.'

    def test_logout_without_token(self, authenticated_client):
        url = reverse('logout')
        response = authenticated_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_with_invalid_token(self, authenticated_client):
        url = reverse('logout')
        response = authenticated_client.post(url, {'refresh': 'invalid-token'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserProfile:
    def test_get_own_profile(self, authenticated_client):
        url = reverse('user-detail')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'email' in response.data
        assert 'first_name' in response.data
        assert 'last_name' in response.data

    def test_update_own_profile(self, authenticated_client, user):
        url = reverse('user-detail')
        data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast'
        }
        response = authenticated_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'UpdatedFirst'
        assert response.data['last_name'] == 'UpdatedLast'

    def test_unauthenticated_access(self, api_client):
        url = reverse('user-detail')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestUserList:
    def test_admin_can_list_users(self, admin_client):
        url = reverse('user-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_list_users(self, authenticated_client):
        url = reverse('user-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
