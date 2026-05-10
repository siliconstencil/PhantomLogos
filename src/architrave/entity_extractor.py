import os
import sys

# Absolute First: Set encoding for Windows console stability
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import logging
from typing import List, Dict, Any, Optional

import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Phase 11.16: Knowledge Extraction Engine (v2).
    Uses GLiNER2 for unified NER and Relation Extraction in a single pass.
    Hardened for Thread-Safety and Singleton Pattern (S5.4).
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(EntityExtractor, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "fastino/gliner2-base-v1"):
        if not hasattr(self, 'initialized'):
            self.model_name = model_name
            self.model: Optional[Any] = None
            self._entity_labels = ["tech_term", "module", "duration", "constraint", "version"]
            self._relation_labels = ["expires_in", "belongs_to", "configured_in", "depends_on", "uses"]
            self.initialized = True
        
    def _load_model(self):
        if self.model is None:
            with self._lock:
                if self.model is None:
                    try:
                        from gliner2 import GLiNER2
                        # Monkey-patch to prevent UnicodeEncodeError on Windows (Brain emoji in _print_config)
                        GLiNER2._print_config = lambda self, config: None
                        
                        # Load model to CPU explicitly
                        self.model = GLiNER2.from_pretrained(self.model_name)
                        logger.info(f"EntityExtractor: GLiNER2 loaded on CPU ({self.model_name})")
                    except Exception as e:
                        logger.error(f"EntityExtractor: Failed to load GLiNER2 ({e})")
                        raise

    def extract_unified(self, text: str) -> Dict[str, Any]:
        """
        Performs unified extraction (NER + Relations) in a single pass.
        Returns:
            Dict containing 'entities' and 'relations'.
        """
        self._load_model()
        if not text:
            return {"entities": [], "relations": []}
            
        try:
            # Create unified schema
            schema = (
                self.model.create_schema()
                .entities(self._entity_labels)
                .relations(self._relation_labels)
            )
            
            # Perform extraction
            results = self.model.extract(text, schema=schema)
            
            # Normalize output
            # GLiNER2 returns { 'entities': {...}, 'relations': {...} }
            raw_entities = results.get("entities", {})
            raw_relations = results.get("relations", {})
            
            entities = []
            for label, texts in raw_entities.items():
                for t in texts:
                    entities.append({"text": t, "type": label})
                    
            relations = []
            for label, pairs in raw_relations.items():
                for pair in pairs:
                    if len(pair) == 2:
                        relations.append({
                            "s": pair[0],
                            "p": label,
                            "o": pair[1]
                        })
                        
            return {
                "entities": entities,
                "relations": relations
            }
        except Exception as e:
            logger.error(f"EntityExtractor: Extraction failed ({e})")
            return {"entities": [], "relations": []}

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Legacy support for NER only."""
        res = self.extract_unified(text)
        return res["entities"]

    async def extract_relations_batch(self, text: str, entities: List[Dict[str, Any]], bridge: Any) -> List[Dict[str, Any]]:
        """Legacy support/Fallback for relations."""
        res = self.extract_unified(text)
        return res["relations"]
