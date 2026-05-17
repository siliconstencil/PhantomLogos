import json
import re
import threading

from src.utils.logging_config import setup_logger

from ..mnemosyne.episodic_store import EpisodicStore
from ..mnemosyne.goal_store import GoalStore
from ..mnemosyne.meta_cognition import MetaCognitionStore
from ..mnemosyne.procedural_store import ProceduralStore

# [SRC:axis_1] Core Strategic Factory for Singleton Services.
# [SRC:axis_5] Entry point for Spatial and Codebase Mapping services.
from ..mnemosyne.rational_store import MnemosyneRationalStore
from ..mnemosyne.spatial_store import SpatialStore
from ..mnemosyne.visual_store import VisualStore

logger = setup_logger(__name__)

# --- Singleton State ---
_init_lock = threading.RLock()
_store = None
_episodic = None
_goals = None
_procedural = None
_meta = None
_pruner = None
_monitor = None

_spatial = None
_mapper = None
_semantic = None
_temporal = None
_reflection = None
_failure_memory = None
_vram_sweeper = None
_model_loader = None
_visual = None

# --- Singleton Getters ---


def _get_store():
    global _store
    with _init_lock:
        if _store is None:
            _store = MnemosyneRationalStore()
            _ensure_governance_sync(_store)
    return _store


def _ensure_governance_sync(store: MnemosyneRationalStore):
    """
    Ensures that rules.json is synchronized with Mnemosyne Axis 10.
    [SRC:axis_10] Governance Sync on startup.
    """
    try:
        # Check if rules exist. If not, force a sync.
        # Alternatively, we could check mtime, but simple check for now.
        if len(store.get_secure_rules("system")) < 5:
            logger.info("Hephaestus: Axis 10 rules missing or incomplete. Triggering sync...")
            import importlib

            sync_mod = importlib.import_module("scripts.sync_governance")
            sync_mod.sync()
    except Exception as e:
        logger.warning(f"Hephaestus: Governance sync failed ({e})")


def _get_episodic():
    global _episodic
    with _init_lock:
        if _episodic is None:
            _episodic = EpisodicStore()
    return _episodic


def _get_goals():
    global _goals
    with _init_lock:
        if _goals is None:
            _goals = GoalStore()
    return _goals


def _get_procedural():
    global _procedural
    with _init_lock:
        if _procedural is None:
            _procedural = ProceduralStore()
    return _procedural


def _get_meta():
    global _meta
    with _init_lock:
        if _meta is None:
            _meta = MetaCognitionStore()
    return _meta


def _get_pruner():
    global _pruner
    with _init_lock:
        if _pruner is None:
            from src.atropos.context_pruner import ContextPruner

            _pruner = ContextPruner()
    return _pruner


def _get_spatial():
    global _spatial
    with _init_lock:
        if _spatial is None:
            _spatial = SpatialStore()
    return _spatial


def _get_mapper():
    global _mapper
    with _init_lock:
        if _mapper is None:
            # [SRC:axis_5] Initializing CodebaseMapper with SpatialStore.
            from src.lachesis import CodebaseMapper
            from src.utils.project_path import get_project_root

            _mapper = CodebaseMapper(
                project_path=str(get_project_root()), spatial_store=_get_spatial()
            )
    return _mapper


def _ensure_spatial_index():
    """Trigger codebase mapping only if spatial index is empty (Axis 5).
    [SRC:axis_5] JIT indexing for context-aware reasoning.
    """
    mapper = _get_mapper()
    from ..mnemosyne.spatial_store import SpatialStore

    sp = SpatialStore()
    if sp.get_module_count() > 0:
        return

    logger.info("Hephaestus: Spatial index empty. Triggering JIT codebase mapping...")
    # Pillar 2: Use deep mapping for initial discovery
    mapper.map_codebase(deep=True)


def _get_semantic():
    global _semantic
    with _init_lock:
        if _semantic is None:
            from ..mnemosyne.semantic_store import SemanticStore

            _semantic = SemanticStore()
    return _semantic


def _get_temporal():
    global _temporal
    with _init_lock:
        if _temporal is None:
            from ..mnemosyne.temporal_store import TemporalStore

            _temporal = TemporalStore()
    return _temporal


def _get_reflection():
    global _reflection
    with _init_lock:
        if _reflection is None:
            from ..mnemosyne.reflection_store import ReflectionStore

            _reflection = ReflectionStore()
    return _reflection


def _get_failure_memory():
    global _failure_memory
    with _init_lock:
        if _failure_memory is None:
            from ..mnemosyne.semantic_store import FailureMemoryStore

            _failure_memory = FailureMemoryStore()
    return _failure_memory


def _get_monitor():
    global _monitor
    with _init_lock:
        if _monitor is None:
            from src.atropos.observability import AtroposMonitor

            _monitor = AtroposMonitor()
    return _monitor


def _get_sweeper():
    global _vram_sweeper
    with _init_lock:
        if _vram_sweeper is None:
            from src.utils.service_locator import get_sweeper

            _vram_sweeper = get_sweeper()
    return _vram_sweeper


def _get_loader():
    global _model_loader
    with _init_lock:
        if _model_loader is None:
            from src.utils.service_locator import get_model_loader

            _model_loader = get_model_loader()
    return _model_loader


def _get_visual():
    global _visual
    with _init_lock:
        if _visual is None:
            _visual = VisualStore()
    return _visual


# --- Shared Schemas ---

# [SRC:axis_1] Logic Schemas moved to eidos.py

# --- Text Utilities ---


def strip_thinking_block(text: str) -> str:
    """Removes <think>...</think> blocks from text."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_first_json_block(text: str) -> str | None:
    """
    Finds the first balanced JSON block (starting with {) in the text.
    Returns the raw JSON string or None if not found.
    """
    brace_depth = 0
    json_start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if brace_depth == 0:
                json_start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and json_start >= 0:
                return text[json_start : i + 1]
    return None


def extract_tool_calls(text: str) -> list[dict]:
    """
    Robustly extracts tool-call JSON blocks from text.
    Handles nested structures by finding balanced brackets.
    """
    results = []
    start_idx = 0
    while True:
        idx = text.find("{", start_idx)
        if idx == -1:
            break

        # Try to find balancing }
        depth = 0
        end_idx = -1
        for i in range(idx, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break

        if end_idx != -1:
            snippet = text[idx:end_idx]
            try:
                data = json.loads(snippet)
                if isinstance(data, dict) and "tool" in data and "input" in data:
                    results.append(data)
            except json.JSONDecodeError:
                pass
            start_idx = end_idx
        else:
            start_idx = idx + 1

    return results


def get_sophia_instructions(tools: list[str]) -> dict:
    """Returns the standardized instructions for Sophia's reasoning."""
    return {
        "tool": f"""
TOOL USAGE AND STRUCTURE GUIDELINES:
You MUST provide your response in valid JSON format matching this schema:
{{
  "thought": "your internal reasoning and citations [SRC:axis_N]",
  "technical_claims": [{{"claim": "type", "value": "val", "evidence": "why"}}],
  "tool_calls": [{{"thought": "why", "tool": "name", "input": "params"}}],
  "final_response": "answer if no tools needed"
}}

Available tools: {", ".join(tools)}

MANDATORY: Every technical claim (VRAM, NGL, Paths) MUST be listed in 'technical_claims'.
Failure to provide valid JSON or missing timestamps in 'thought' will result in rejection.
""",
        "timestamp": """
TEMPORAL ANCHORING:
Every response MUST start with a timestamp in this format: [H:MM AM/PM PT] (e.g., [1:20 PM PT])
Failure to use this format is a rule violation and will result in response rejection.
""",
        "citation": """
CITATION AND SOURCE REQUIREMENT:
For every piece of information or claim, cite the corresponding axis ID from the CONTEXT.
Format: [SRC:axis_N] (e.g., [SRC:axis_6], [SRC:axis_10])
""",
    }
