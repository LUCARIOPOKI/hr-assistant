"""Integration tests for HR Assistant API."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "name" in data


def test_query_endpoint_basic(client):
    """Test query endpoint with basic request."""
    response = client.post("/api/v1/query", json={
        "query": "What is the leave policy?",
        "user_id": "test_user"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "session_id" in data
    assert isinstance(data["sources"], list)


def test_query_endpoint_with_company(client):
    """Test query with company_id."""
    response = client.post("/api/v1/query", json={
        "query": "Tell me about benefits",
        "user_id": "test_user",
        "company_id": 1,
        "top_k": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_summarize_endpoint(client):
    """Test summarization endpoint."""
    response = client.post("/api/v1/summarize", json={
        "company_id": 1,
        "summary_type": "brief",
        "audience": "employees"
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "summary_type" in data
    assert data["summary_type"] == "brief"


def test_query_missing_required_field(client):
    """Test query with missing required field."""
    response = client.post("/api/v1/query", json={
        "user_id": "test_user"
        # missing query field
    })
    assert response.status_code == 422  # Validation error


def test_summarize_missing_company_id(client):
    """Test summarize with missing company_id."""
    response = client.post("/api/v1/summarize", json={
        "summary_type": "brief"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_various_topics(client):
    """Test query with various HR topics."""
    topics = [
        "What is the remote work policy?",
        "How do I check my leave balance?",
        "What are the current job openings?",
        "Tell me about health insurance benefits",
    ]
    
    for topic in topics:
        response = client.post("/api/v1/query", json={
            "query": topic,
            "user_id": "test_user"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0
