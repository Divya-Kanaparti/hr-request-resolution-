"""
RAG and Question Answering Test Suite
"""
import pytest

def test_rag_ask_exact_citations(client, employee_token):
    res = client.post(
        "/api/v1/rag/ask",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "query": "What is the in-network dental coverage percentage under corporate benefits?",
            "top_k": 2
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["citations"]) >= 1

    citation = data["citations"][0]
    assert citation["policy_doc_code"] == "POL-BEN-01"
    assert citation["version_number"] == "2.0" # Active version
    assert "dental" in citation["article_title"].lower()
    assert citation["section_number"] == "Sec 2.1"
    assert len(citation["quote"]) > 0

def test_rag_unmatched_query_graceful_response(client, employee_token):
    res = client.post(
        "/api/v1/rag/ask",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "query": "Can I bring my pet iguana to the international space station cafeteria?",
            "top_k": 2
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "could not find an approved HR policy" in data["answer"]
    assert len(data["citations"]) == 0

