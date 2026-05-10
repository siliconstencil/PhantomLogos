import pytest
from unittest.mock import patch
from src.architrave.entity_extractor import EntityExtractor

# [SRC:axis_6]
@pytest.mark.asyncio
async def test_entity_extraction():
    extractor = EntityExtractor()
    test_text = "JWT token expires in 30 minutes. The orchestrator.py module handles this constraint."
    
    with patch.object(EntityExtractor, 'extract_unified') as mock_unified:
        mock_unified.return_value = {
            "entities": [
                {"text": "JWT", "type": "tech_term"},
                {"text": "30 minutes", "type": "duration"},
                {"text": "orchestrator.py", "type": "module"}
            ],
            "relations": []
        }
        entities = extractor.extract_entities(test_text)
        assert len(entities) == 3
        assert entities[0]["type"] == "tech_term"

@pytest.mark.asyncio
async def test_relation_logic_stub():
    extractor = EntityExtractor()
    test_text = "JWT token expires in 30 minutes."
    
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
        # In current implementation, extract_relations_batch calls extract_unified
        relations = await extractor.extract_relations_batch(test_text, [], None)
        assert len(relations) == 1
        assert relations[0]["p"] == "expires_in"
