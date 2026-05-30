import contextlib
import os
import sys

# Absolute First: Set encoding for Windows console stability
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
if sys.stdout.encoding != "utf-8":
    with contextlib.suppress(Exception):
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if reconfig:
            reconfig(encoding="utf-8")

import json
import threading
from typing import Any

from src.architrave.model_registry import resolve_local_model
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class EntityExtractor:
    """
    Phase 11.16: Knowledge Extraction Engine (v2).
    Uses GLiNER2 for unified NER and Relation Extraction in a single pass.
    Hardened for Thread-Safety and Singleton Pattern (S5.4).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):  # noqa: ARG004
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def harvest_knowledge(text: str, session_id: str) -> None:
        """
        Centralized Knowledge Scavenger (Axis 6).
        Extracts and persists knowledge from any text source.
        """
        if not text or len(text.strip()) < 10:
            return

        # Use singleton instance
        extractor = EntityExtractor()
        results = extractor.extract_unified(text)

        if results.get("entities") or results.get("relations"):
            from cognition.sophia.hephaestus import get_reflection

            store = get_reflection()

            # Persistence (Sync calls wrapped in thread safety if needed)
            if results.get("entities"):
                store.store_entities(session_id, results["entities"])
            if results.get("relations"):
                store.store_relations(session_id, results["relations"])

            logger.info(
                f"Scavenger: Harvested {len(results['entities'])} entities from session {session_id}"
            )

    def __init__(self, model_name: str | None = None) -> None:
        if not hasattr(self, "initialized"):
            self.model_name = model_name or resolve_local_model("ner")
            self.model: Any | None = None
            self._entity_schema = {
                "tech_term": "Programming languages, frameworks, libraries, protocols, or technical concepts (e.g., Python, GLiNER2, SQLAlchemy, NER)",
                "module": "Source code files, classes, or named internal components (e.g., orchestrator.py, ReflectionStore, EntityExtractor)",
                "function": "Function or method names in code (e.g., extract_unified, store_entities, anchor_inject_node)",
                "file_path": "File or directory paths (e.g., src/clotho/ergon/elenchos.py, data/mnemosyne.db)",
                "version": "Version numbers and identifiers (e.g., v1.0.0, Phase 11.19, 1.0.28)",
                "person": "Names of people, developers, or users (e.g., Hank, Tim Cook, Urchade)",
                "organization": "Company, project, or team names (e.g., Fastino, OpenAI, Antigravity)",
                "date": "Date or time references (e.g., May 15, 2026, 2024-03-15)",
                "constraint": "System rules, hardware limits, or boundaries (e.g., 7GB VRAM, L0 Approval, NO_EMOJI, temp=0.6)",
                "duration": "Time periods or frequencies (e.g., 30 days, 60s timeout, 24 months)",
                "label": "Entity type labels or classification tags (e.g., tech_term, NER, tier_2)",
            }
            self._relation_labels = [
                "expires_in",
                "belongs_to",
                "configured_in",
                "depends_on",
                "uses",
            ]
            self.initialized = True

    def _load_model(self) -> None:
        if self.model is None:
            with self._lock:
                if self.model is None:
                    try:
                        from gliner2 import GLiNER2

                        # Monkey-patch to prevent UnicodeEncodeError on Windows (Brain emoji in _print_config)
                        GLiNER2._print_config = lambda self, config: None  # noqa: ARG005

                        # Load model to CPU explicitly
                        self.model = GLiNER2.from_pretrained(self.model_name)
                        logger.info(f"EntityExtractor: GLiNER2 loaded on CPU ({self.model_name})")
                    except Exception as e:
                        raise RuntimeError(
                            f"EntityExtractor: Failed to load GLiNER2 model '{self.model_name}' ({e})"
                        ) from e

    def extract_unified(self, text: str) -> dict[str, Any]:
        """
        Performs unified extraction (NER + Relations) in a single pass.
        Returns:
            Dict containing 'entities' and 'relations'.
        """
        self._load_model()
        if not text:
            return {"entities": [], "relations": []}

        if self.model is None:
            raise RuntimeError(
                "EntityExtractor: GLiNER2 model failed to load, cannot proceed with extraction."
            )

        # Phase 1.0.2: GLiNER2 Unified Schema
        schema = (
            self.model.create_schema()
            .entities(self._entity_schema)
            .relations(self._relation_labels)
        )

        # Perform extraction
        results = self.model.extract(text, schema=schema)

        # GLiNER2 results are structured: results['entities'] = {label: [texts...]}
        # results['relations'] = {label: [[s, o], ...]}

        raw_entities = results.get("entities", {})
        entities = [
            {"text": t, "type": label} for label, texts in raw_entities.items() for t in texts
        ]

        raw_relations = results.get("relations", {})
        relations = [
            {"s": pair[0], "p": label, "o": pair[1]}
            for label, pairs in raw_relations.items()
            for pair in pairs
            if len(pair) == 2
        ]

        return {"entities": entities, "relations": relations}

    def extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Legacy support for NER only."""
        res = self.extract_unified(text)
        return res["entities"]

    async def extract_relations_batch(
        self, text: str, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        [SRC:axis_8] Deep Path Fallback: Uses Ollama for complex relation extraction.
        Addressing P4 (boomer wrap fix) with a full LLM implementation (~40 lines).
        """
        if not text or not entities:
            return []

        try:
            entity_list = ", ".join([e["text"] for e in entities[:12]])
            prompt = f"""
            TASK: Extract semantic relationships between the provided entities.
            ENTITIES: [{entity_list}]
            CONTEXT: {text[:1800]}

            ALLOWED PREDICATES: {", ".join(self._relation_labels)}

            FORMAT: Return a JSON list of triplets.
            Structure: {{"s": "Subject", "p": "Predicate", "o": "Object"}}

            Example: [{{"s": "Antigravity", "p": "uses", "o": "Mnemosyne"}}]
            """

            from src.utils.ollama_utils import get_ollama_client

            client = get_ollama_client()

            # Use Tier 1 reasoning model for high-fidelity extraction
            critique_model = resolve_local_model("critique")
            import asyncio

            resp = await asyncio.wait_for(
                client.generate(model=critique_model, prompt=prompt, format="json"), timeout=30.0
            )
            if not resp or not resp.response:
                logger.warning("EntityExtractor: Deep Path returned empty response.")
                return []

            raw_data = json.loads(resp.response)
            # Handle both single object and list of objects
            data = raw_data if isinstance(raw_data, list) else [raw_data]

            valid_relations = [
                item
                for item in data
                if isinstance(item, dict)
                and all(k in item for k in ("s", "p", "o"))
                and item["p"] in self._relation_labels
            ]

            if valid_relations:
                logger.info(
                    f"EntityExtractor: Deep Path extracted {len(valid_relations)} relations."
                )
            return valid_relations

        except Exception as e:
            logger.debug(f"EntityExtractor: Deep Path fallback failed ({e})")
            return []
