import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from app.models import User,UserSession,Product
from rest_framework import status
from unittest import mock

#Test register for buyer
@pytest.mark.django_db
def test_register_view_success():
    client = APIClient()
    data = {
        "user_name": "buyer1",
        "email": "buyer1@example.com",
        "password": "pass1234",
        "role": "buyer"
    }

    response = client.post(reverse("register"), data)
    assert response.status_code == 201
    assert "data" in response.data
    assert User.objects.filter(email="buyer1@example.com").exists()



#test register for seller
@pytest.mark.django_db
def test_register_view_invalid_email():
    client = APIClient()
    data = {
        "user_name": "testuser",
        "email": "bademail",
        "password": "pass123",
        "role": "buyer"
    }

    response = client.post(reverse("register"), data)
    assert response.status_code == 400
    assert "error" in response.data



#Login_View
@pytest.mark.django_db
def test_login_view_success(user_factory):
    user = user_factory(email="buyer@example.com", password="pass1234")
    client = APIClient()

    response = client.post(reverse("login"), {
        "email": "buyer@example.com",
        "password": "pass1234"
    })
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data

  
#Login Session
@pytest.mark.django_db
def test_login_with_existing_session(user_factory):
    user = user_factory(email="buyer@example.com", password="pass1234")

    # Simulate an active session
    UserSession.objects.create(
        user=user,
        refresh_token="abc123",
        user_agent="TestAgent",
        ip_address="127.0.0.1"
    )

    client = APIClient()
    response = client.post(
        reverse('login'),
        {"email": "buyer@example.com", "password": "pass1234"}
    )

    assert response.status_code == 403
    assert response.data["message"] == "There is already an active session using your account"


@pytest.mark.django_db
def test_login_invalid_credentials():
    client = APIClient()
    response = client.post(reverse("login"), {
        "email": "wrong@example.com",
        "password": "nope"
    })
    assert response.status_code == 401


@pytest.mark.django_db
def test_user_view(authenticated_buyer):
    client, buyer = authenticated_buyer

    # Hit the endpoint
    response = client.get(reverse("user_view"))  

    # Check status
    assert response.status_code == 200

    # Check returned data
    assert response.data["id"] == buyer.id
    assert response.data["user_name"] == buyer.user_name
    assert response.data["email"] == buyer.email
    assert response.data["role"] == buyer.role
    assert response.data["deposit"] == buyer.deposit


#Test deopist
@pytest.mark.django_db
def test_deposit_success(authenticated_buyer):
    client, buyer = authenticated_buyer

    response = client.post(reverse("deposit"), {"coin": 10})
    assert response.status_code == 200
    buyer.refresh_from_db()
    assert response.data["deposit"] == buyer.deposit


@pytest.mark.django_db
def test_deposit_invalid_coin(authenticated_buyer):
    client, buyer = authenticated_buyer
    response = client.post(reverse('deposit'), {'coin': 3})  # invalid coin
    assert response.status_code == 400


@pytest.mark.django_db
def test_deposit_non_integer_coin(authenticated_buyer):
    client, buyer = authenticated_buyer
    response = client.post(reverse('deposit'), {'coin': 'abc'})
    assert response.status_code == 400
    assert 'Invalid coin format' in response.data['detail']




#Test product creation
@pytest.mark.django_db
def test_product_create_by_seller(authenticated_seller):
    client, seller = authenticated_seller
    data = {"product_name": "Coke", "cost": 20, "amount_available": 5}
    response = client.post(reverse("product_create"), data)
    assert response.status_code == 201
    assert response.data["product_name"] == "Coke"

@pytest.mark.django_db
def test_product_create_psoitive_cost(authenticated_seller):
    client, seller = authenticated_seller
    data = {"product_name": "Coke", "cost": 0, "amount_available": 5}
    response = client.post(reverse("product_create"), data)
    assert response.status_code == 400
    


@pytest.mark.django_db
def test_product_create_by_seller_invalid(authenticated_seller):
    client, seller = authenticated_seller
    data = {"product_name": "Coke", "cost": 9, "amount_available": 7}
    response = client.post(reverse("product_create"), data)
    assert response.status_code == 400




@pytest.mark.django_db
def test_product_create_permission_denied(authenticated_buyer):
    client, buyer = authenticated_buyer
    response = client.post(reverse('product_create'), {'product_name': 'Test', 'amount_available': 10, 'cost': 50})
    assert response.status_code == 403
    assert 'User Permission denied' in response.data['message']


#Product View
@pytest.mark.django_db
def test_product_view_get(product_factory, authenticated_buyer):
    client, _ = authenticated_buyer  # use APIClient with auth

    # Create products
    product1 = product_factory(product_name="Product 1", cost=100, amount_available=5)
    product2 = product_factory(product_name="Product 2", cost=200, amount_available=10)

    response = client.get(reverse("product_view"))
    assert response.status_code == 200
    assert len(response.data["data"]) >= 2



#Test product Update
@pytest.mark.django_db
def test_product_update_success(authenticated_seller, product_factory):
    client, seller = authenticated_seller
    product = product_factory(seller=seller, product_name="Coke", cost=20, amount_available=10)

    # PATCH request to update cost
    response = client.patch(
        reverse("product_update", kwargs={"pk": product.id}),
        {"cost": 25}  # valid cost
    )

    assert response.status_code == 200
    assert response.data["data"]["cost"] == 25

@pytest.mark.django_db
def test_product_update_invalid_cost(authenticated_seller, product_factory):
    client, seller = authenticated_seller
    product = product_factory(seller=seller, product_name="Coke", cost=20, amount_available=10)

    # PATCH with invalid cost (not multiple of 5)
    response = client.patch(
        reverse("product_update", kwargs={"pk": product.id}),
        {"cost": 22}
    )

    assert response.status_code == 400
    assert "cost" in response.data

@pytest.mark.django_db
def test_product_delete_success(authenticated_seller, product_factory):
    client, seller = authenticated_seller
    product = product_factory(seller=seller, product_name="Coke", cost=20, amount_available=10)

    response = client.delete(reverse("product_update", kwargs={"pk": product.id}))
    assert response.status_code == 200
    assert response.data["message"] == "Product deleted successfully"
    assert not Product.objects.filter(id=product.id).exists()

@pytest.mark.django_db
def test_non_seller_cannot_update(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(seller=buyer, product_name="Coke", cost=20, amount_available=10)

    response = client.patch(
        reverse("product_update", kwargs={"pk": product.id}),
        {"cost": 25}
    )
    assert response.status_code == 403



#Test buyers buying product
@pytest.mark.django_db
def test_buy_view_success(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(cost=10, amount_available=3)
    buyer.deposit = 50
    buyer.save()

    response = client.post(reverse("buy_view"), {"product_id": product.id, "amount": 2})
    assert response.status_code == 200
    assert response.data["product"]["total_cost"] == 20
    assert response.data["total_spent"] == 20

@pytest.mark.django_db
def test_buy_insufficient_deposit(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(amount_available=5, cost=50)
    buyer.deposit = 10
    buyer.save()
    response = client.post(reverse('buy_view'), {'product_id': product.id, 'amount': 1})
    assert response.status_code == 400
    assert 'Insufficient deposit' in response.data['detail']

@pytest.mark.django_db
def test_buy_invalid_amount(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(amount_available=5, cost=10)
    buyer.deposit = 50
    buyer.save()
    response = client.post(reverse('buy_view'), {'product_id': product.id, 'amount': "three"})
    assert response.status_code == 400
    assert 'Amount must be an integer' in response.data['detail']


@pytest.mark.django_db
def test_buy_positive_amount(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(amount_available=5, cost=10)
    buyer.deposit = 50
    buyer.save()
    response = client.post(reverse('buy_view'), {'product_id': product.id, 'amount': 0})
    assert response.status_code == 400
    assert 'Amount must be a positive integer' in response.data['detail']



@pytest.mark.django_db
def test_buy_missing_product_id(authenticated_buyer):
    client, buyer = authenticated_buyer
    buyer.deposit = 100
    buyer.save()

    # POST request without product_id
    response = client.post(reverse('buy_view'), {'amount': 1})

    assert response.status_code == 400
    assert 'Product ID is required' in response.data['detail']


@pytest.mark.django_db
def test_buy_amount_greater_than_amunt_available(authenticated_buyer, product_factory):
    client, buyer = authenticated_buyer
    product = product_factory(amount_available=5, cost=10)
    buyer.deposit = 50
    buyer.save()
    response = client.post(reverse('buy_view'), {'product_id': product.id, 'amount': 10})
    assert response.status_code == 400
    assert 'Not enough product available' in response.data['detail']


@pytest.mark.django_db
def test_deposit_denied_for_seller(authenticated_seller):
    client, seller = authenticated_seller

    # Try to deposit as a seller
    response = client.post(reverse("deposit"), {"coin": 5})

    assert response.status_code == 403
    assert response.data["detail"] == "Only buyers can deposit."




@pytest.mark.django_db
def test_only_buyers_buy(authenticated_seller, product_factory):
    client, seller = authenticated_seller
    product = product_factory(amount_available=5, cost=10)
    
    response = client.post(reverse('buy_view'), {'product_id': product.id, 'amount': 10})
    
    assert response.status_code == 403
    assert 'Only buyers can buy' in response.data['detail']




#Deposit

@pytest.mark.django_db
def test_reset_deposit_buyer(authenticated_buyer):
    client, buyer = authenticated_buyer

    # Give the buyer some deposit first
    buyer.deposit = 50
    buyer.save(update_fields=['deposit'])

    # Call the endpoint
    response = client.post(reverse("reset_deposit"))

    # Assert response
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Deposit reset successfully"

    # Refresh from DB and check deposit
    buyer.refresh_from_db()
    assert buyer.deposit == 0


@pytest.mark.django_db
def test_reset_deposit_non_buyer(authenticated_seller):
    client, seller = authenticated_seller

    response = client.post(reverse("reset_deposit"))

    # Should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == "Only buyers can reset deposit"
    





@pytest.mark.django_db
def test_logout_all_view(authenticated_buyer, user_session_factory):
    client, buyer = authenticated_buyer

    # Create some sessions for this user
    session1 = user_session_factory(user=buyer)
    session2 = user_session_factory(user=buyer)

    # Ensure sessions exist before logout
    assert UserSession.objects.filter(user=buyer).count() == 2

    # Call the logout_all endpoint
    response = client.post(reverse("logout_all"))

    # Assert response is successful
    assert response.status_code == 200
    assert response.data["message"] == "Session Terminated"

    # Ensure all sessions are deleted
    assert UserSession.objects.filter(user=buyer).count() == 0






from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Should raise ValueError when no email is provided"""
    user_manager = User.objects  # instance of your custom UserManager
    with pytest.raises(ValueError) as excinfo:
        user_manager.create_user(email="", password="testpass123")
    assert "Users must have an email address" in str(excinfo.value)



@pytest.mark.django_db
def test_create_superuser_sets_required_flags():
    """Should create a superuser with correct flags set"""
    user_manager = User.objects
    admin = user_manager.create_superuser(email="admin@example.com", password="adminpass123")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True
    assert admin.email == "admin@example.com"
    assert admin.check_password("adminpass123") is True




import importlib


@pytest.mark.django_db
def test_asgi_application_loads_settings(monkeypatch):
    """Should load Django settings and return a valid ASGI application"""
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'Vendor.settings')

    # Import (or reload) your actual asgi.py file to trigger its code
    asgi_module = importlib.import_module("Vendor.asgi")
    importlib.reload(asgi_module)

    assert hasattr(asgi_module, "application")
    assert callable(asgi_module.application)






import sys


@pytest.mark.django_db
def test_manage_main(monkeypatch):
    """Test manage.py main() executes properly"""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "Vendor.settings")
    called = {}

    # Mock execute_from_command_line to avoid actually running commands
    def fake_execute_from_command_line(args):
        called["executed"] = True
        assert args == sys.argv

    monkeypatch.setattr("django.core.management.execute_from_command_line", fake_execute_from_command_line)

    # Import and reload manage.py to run all top-level code
    manage_module = importlib.import_module("manage")
    importlib.reload(manage_module)

    # Call main directly
    manage_module.main()
    assert "executed" in called


import runpy

@pytest.mark.django_db
def test_manage_entrypoint(monkeypatch):
    """Simulate running manage.py as __main__ to cover the entry point"""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "Vendor.settings")
    called = {}

    def fake_execute_from_command_line(args):
        called["executed"] = True

    monkeypatch.setattr("django.core.management.execute_from_command_line", fake_execute_from_command_line)

    # Run the module as __main__, which executes the bottom line
    runpy.run_module("manage", run_name="__main__")

    assert "executed" in called




@pytest.mark.django_db
def test_manage_importerror(monkeypatch):
    """Trigger the ImportError branch in manage.py safely"""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "Vendor.settings")

    
    original_import = __import__

    
    with mock.patch("builtins.__import__") as mock_import:
        def side_effect(name, *args, **kwargs):
            if name == "django.core.management":
                raise ImportError("No module named django")
            return original_import(name, *args, **kwargs)  # call original import safely

        mock_import.side_effect = side_effect

        
        manage_module = importlib.import_module("manage")
        importlib.reload(manage_module)

        
        with pytest.raises(ImportError) as excinfo:
            manage_module.main()

        assert "Couldn't import Django" in str(excinfo.value)




@pytest.mark.django_db
def test_wsgi_application_loads(monkeypatch):
    """Ensure wsgi.py loads and application is callable"""

    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "Vendor.settings")

    
    wsgi_module = importlib.import_module("Vendor.wsgi")
    importlib.reload(wsgi_module)

    
    assert hasattr(wsgi_module, "application")
    assert callable(wsgi_module.application)
