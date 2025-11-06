import pytest
from rest_framework.test import APIClient
from app.models import User, Product

import uuid

from app.models import UserSession


@pytest.fixture
def user_factory(db, django_user_model):
    def create_user(**kwargs):
        password = kwargs.pop("password", "pass1234")
        user = django_user_model.objects.create_user(**kwargs)
        user.set_password(password)
        user.save()
        return user
    return create_user


@pytest.fixture
def authenticated_buyer(user_factory):
    user = user_factory(email="buyer@test.com", role="buyer", user_name="buyer")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def authenticated_seller(user_factory):
    user = user_factory(email="seller@test.com", role="seller", user_name="seller")
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user



import itertools
counter = itertools.count()

@pytest.fixture
def product_factory(user_factory):
    def create_product(**kwargs):
        seller = kwargs.pop(
            "seller", 
            user_factory(
                role="seller", 
                email=f"s{next(counter)}@t.com", 
                user_name=f"seller{next(counter)}"
            )
        )
        return Product.objects.create(seller=seller, **kwargs)
    return create_product



@pytest.fixture
def user_session_factory(user_factory):
    def create_session(user=None, **kwargs):
        if user is None:
            user = user_factory(
                email=f"user{uuid.uuid4()}@test.com",
                user_name=f"user{uuid.uuid4()}",
                role="buyer"
            )
        return UserSession.objects.create(
            user=user,
            refresh_token=kwargs.get("refresh_token", str(uuid.uuid4())),
            user_agent=kwargs.get("user_agent", "test-agent"),
            ip_address=kwargs.get("ip_address", "127.0.0.1")
        )
    return create_session
