
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from deploy_rag.app import app, models

client = TestClient(app)

@pytest.fixture
def mock_collection():
    mock = MagicMock()
    mock.query.return_value = {
        'ids': [['id1']],
        'metadatas': [[{
            'drug_id': 'DB00001',
            'smiles': 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
            'is_substrate': '1',
            'parent_doc': 'Caffeine is a stimulant.'
        }]]
    }
    return mock

@patch('deploy_rag.app.query_llm')
@patch('os.environ.get')
def test_query_endpoint(mock_env_get, mock_query_llm, mock_collection):
    # Setup mocks
    mock_env_get.side_effect = lambda k, default=None: {
        'LLM_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'fake-key'
    }.get(k, default)
    
    mock_query_llm.return_value = "This is a mocked answer."
    
    # Inject mock collection
    models["collection"] = mock_collection
    
    response = client.post("/query", json={"query": "What is caffeine?", "top_k": 1})
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "context" in data
    assert "provider" in data
    assert "citations" in data
    assert "is_substrate" in data
    
    assert data["answer"] == "This is a mocked answer."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["drug_id"] == "DB00001"
    assert data["citations"][0]["smiles"] == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
    assert data["citations"][0]["parent_doc"] == "Caffeine is a stimulant."
    assert data["is_substrate"] == "1"
