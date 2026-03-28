
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
from deploy_rag.app import app, models

client = TestClient(app)

def test_health_endpoint_healthy():
    # Clear models and set healthy state
    models.clear()
    models["is_syncing"] = False
    models["count"] = 10
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["vector_db_count"] == 10
    assert data["is_syncing"] is False

def test_health_endpoint_initializing():
    # Set initializing state
    models.clear()
    models["is_syncing"] = True
    models["count"] = 0
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "initializing"
    assert data["vector_db_count"] == 0
    assert data["is_syncing"] is True

def test_health_endpoint_degraded():
    # Set degraded state
    models.clear()
    models["is_syncing"] = False
    models["count"] = 0
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["vector_db_count"] == 0
    assert data["is_syncing"] is False

@patch('deploy_rag.app.query_llm')
@patch('deploy_rag.app.get_rag_context')
def test_query_endpoint_sync(mock_get_rag, mock_query_llm):
    # Verify that run_query works (it's now a sync def)
    models.clear()
    models["collection"] = MagicMock()
    
    mock_get_rag.return_value = {
        "context": "some context",
        "citations": [],
        "is_substrate": "0"
    }
    mock_query_llm.return_value = "Mocked answer"
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake"}):
        response = client.post("/query", json={"query": "test query"})
    
    assert response.status_code == 200
    assert response.json()["answer"] == "Mocked answer"

def test_query_endpoint_no_collection():
    models.clear()
    response = client.post("/query", json={"query": "test query"})
    assert response.status_code == 500
    assert "Vector Database not initialized" in response.json()["detail"]

@patch('deploy_rag.app.query_llm')
@patch('deploy_rag.app.get_rag_context')
def test_query_endpoint_gemini(mock_get_rag, mock_query_llm):
    models.clear()
    models["collection"] = MagicMock()
    
    mock_get_rag.return_value = {
        "context": "some context",
        "citations": [],
        "is_substrate": "0"
    }
    mock_query_llm.return_value = "Gemini answer"
    
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "fake-gemini"}):
        response = client.post("/query", json={"query": "test query"})
    
    assert response.status_code == 200
    assert response.json()["answer"] == "Gemini answer"
    assert response.json()["provider"] == "gemini"
    mock_query_llm.assert_called_with("gemini", "fake-gemini", "test query", "some context")

@patch('deploy_rag.app.get_rag_context')
def test_query_endpoint_no_api_key(mock_get_rag):
    models.clear()
    models["collection"] = MagicMock()
    
    mock_get_rag.return_value = {
        "context": "retrieved context",
        "citations": [],
        "is_substrate": "1"
    }
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "LLM_PROVIDER": "openai"}):
        response = client.post("/query", json={"query": "test query"})
    
    assert response.status_code == 200
    assert "[Notice] API Key not found" in response.json()["answer"]
    assert response.json()["provider"] == "none"
