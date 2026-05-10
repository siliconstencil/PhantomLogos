import pytest
from unittest.mock import patch
from src.architrave.entity_extractor import EntityExtractor

# [SRC:axis_6]
def test_gliner2_unified_extraction():
    extractor = EntityExtractor()
    test_text = "JWT token expires in 30 minutes. The orchestrator.py module handles this constraint."
    
    with patch.object(EntityExtractor, 'extract_unified') as mock_unified:
        mock_unified.return_value = {
            "entities": [
                {"text": "JWT", "type": "tech_term"},
                {"text": "30 minutes", "type": "duration"}
            ],
            "relations": [
                {"s": "JWT", "p": "expires_in", "o": "30 minutes"}
            ]
        }
        
        results = extractor.extract_unified(test_text)
        
        assert "entities" in results
        assert "relations" in results
        assert len(results["entities"]) > 0
        assert results["entities"][0]["text"] == "JWT"
        
        relations = results["relations"]
        assert len(relations) == 1
        assert all(k in relations[0] for k in ["s", "p", "o"])
