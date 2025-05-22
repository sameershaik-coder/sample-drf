import pytest
from pytest_factoryboy import register
from accounts.factories import UserFactory, AdminUserFactory

# Register factories
register(UserFactory)
register(AdminUserFactory)

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure we use the test database"""
    pass
