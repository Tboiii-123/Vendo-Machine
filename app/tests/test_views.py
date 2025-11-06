import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from app.models import User,UserSession
from rest_framework import status

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



#Test User_view
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

  
@pytest.mark.django_db
def test_login_invalid_credentials(db, django_user_model):
    client = APIClient()
    response = client.post(reverse('login_view'), {'email': 'wrong@test.com', 'password': 'wrongpass'})
    assert response.status_code == 401
    assert response.data['message'] == "Invalid credentials"
      


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
def test_product_create_permission_denied(authenticated_buyer):
    client, buyer = authenticated_buyer
    response = client.post(reverse('product_create'), {'product_name': 'Test', 'amount_available': 10, 'cost': 50})
    assert response.status_code == 403
    assert 'User Permission denied' in response.data['message']




#Product
@pytest.mark.django_db
def test_product_view_get(product_factory, authenticated_buyer):
    client, _ = authenticated_buyer  # use APIClient with auth

    # Create products
    product1 = product_factory(product_name="Product 1", cost=100, amount_available=5)
    product2 = product_factory(product_name="Product 2", cost=200, amount_available=10)

    response = client.get(reverse("product_view"))
    assert response.status_code == 200
    assert len(response.data["data"]) >= 2



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
def test_deposit_denied_for_seller(authenticated_seller):
    client, seller = authenticated_seller

    # Try to deposit as a seller
    response = client.post(reverse("deposit"), {"coin": 5})

    assert response.status_code == 403
    assert response.data["detail"] == "Only buyers can deposit."







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

    # Check sessions exist before logout
    assert UserSession.objects.filter(user=buyer).count() == 2

    # Call the endpoint
    response = client.post(reverse("logout_all"))

    # Assert response
    assert response.status_code == 200
    assert response.data["message"] == "Session Terminated"

    # Assert sessions deleted
    assert UserSession.objects.filter(user=buyer).count() == 0




