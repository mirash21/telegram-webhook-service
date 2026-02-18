import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

def test_detailed_health_endpoint():
    """Test detailed health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "ai_agent" in data["components"]
    assert "webhook_processor" in data["components"]

def test_webhook_endpoint_success():
    """Test successful webhook processing"""
    test_data = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe"
            },
            "chat": {
                "id": 987654321,
                "type": "private"
            },
            "date": 1708234567,
            "text": "Привет"
        }
    }
    
    response = client.post(
        "/webhook/telegram",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "processed_data" in data
    assert data["processed_data"]["sent_to_ai"] == True

def test_webhook_endpoint_empty_body():
    """Test webhook with empty body"""
    response = client.post("/webhook/telegram")
    assert response.status_code == 400

def test_webhook_endpoint_invalid_json():
    """Test webhook with invalid JSON"""
    response = client.post(
        "/webhook/telegram",
        content="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422  # Unprocessable Entity

def test_stats_endpoint():
    """Test statistics endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "webhook_stats" in data
    assert "ai_agent_stats" in data

def test_cors_headers():
    """Test CORS headers"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200