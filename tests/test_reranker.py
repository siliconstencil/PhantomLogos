from src.muscle.reranker import JinaReranker


def test_reranker_path_hardening():
    # Verify reranker model name matches standard
    r = JinaReranker()
    assert r.rerank_model == "jina-reranker-v3:latest"


def test_reranker_fallback_normalization():
    r = JinaReranker()
    query = "python programming"
    docs = ["Python is great", "Java is old", "The sky is blue"]
    results = r.rerank(query, docs)

    assert "results" in results
    for res in results["results"]:
        assert 0 <= res["score"] <= 1
        assert res["text"] in docs


def test_registry_alignment():
    from src.architrave.model_registry import ROLE_TO_MODEL

    assert ROLE_TO_MODEL["reranker"]["primary"] == "jina-reranker-v3:latest"
