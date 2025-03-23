import pytest
from fastapi.testclient import TestClient
from main import app  

@pytest.fixture
def client():
    client = TestClient(app)
    yield client

def test_verify_otp_rate_limiting(client, mocker):
    mocker.patch("app.services.otp_service.OTPService.verify_otp", return_value=False)

    for _ in range(5):  
        response = client.post("/verify_otp/", json={
            "email": "test@example.com", 
            "otp_code": "000000"
        })
        assert response.status_code == 401 
    response = client.post("/verify_otp/", json={
        "email": "test@example.com", 
        "otp_code": "000000"
    })
    assert response.status_code == 429  


def test_create_user(client):
    user_data = {
        "email": "testuser@example.com",
        "password": "StrongP@ssw0rd",  
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "1234567890",
        "date_of_birth": "1990-01-01",
        "shipping_address": "123 Main St",
        "shipping_city": "Anytown",
        "shipping_country": "Country",
        "shipping_zip_code": "12345",
        "account_status": "pending",  
        "role": "CLIENT",  
        "two_factor_enabled": False,
        "is_email_verified": False
    }
    
    response = client.post("/create_user/", json=user_data)  
    assert response.status_code == 201 
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]