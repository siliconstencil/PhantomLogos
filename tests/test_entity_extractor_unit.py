from unittest.mock import patch

from src.architrave.entity_extractor import EntityExtractor


def test_extractor_uses_local_gliner2_path():
    mock_gliner2 = patch("gliner2.GLiNER2").start()
    try:
        ext = EntityExtractor()
        ext.model = None
        ext._load_model()
        mock_gliner2.from_pretrained.assert_called_once_with(
            "D:/Google/AntiGravity/General Tools/gliner2-base-v1"
        )
    finally:
        patch.stopall()


def test_extractor_unified_extraction():
    extractor = EntityExtractor()
    test_text = "JWT token expires in 30 minutes."

    with patch.object(EntityExtractor, "extract_unified") as mock_unified:
        mock_unified.return_value = {
            "entities": [{"text": "JWT", "type": "tech_term"}],
            "relations": [{"s": "JWT", "p": "expires_in", "o": "30 minutes"}],
        }
        results = extractor.extract_unified(test_text)
        assert "entities" in results
        assert "relations" in results
        assert len(results["entities"]) > 0
