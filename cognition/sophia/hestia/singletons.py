import threading

from cognition.mnemosyne.episodic_store import EpisodicStore
from cognition.mnemosyne.goal_store import GoalStore
from cognition.mnemosyne.meta_cognition import MetaCognitionStore
from cognition.mnemosyne.procedural_store import ProceduralStore
from cognition.mnemosyne.rational_store import MnemosyneRationalStore
from cognition.mnemosyne.spatial_store import SpatialStore
from cognition.mnemosyne.visual_store import VisualStore
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

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


def _get_store():
    global _store
    with _init_lock:
        if _store is None:
            _store = MnemosyneRationalStore()
            _ensure_governance_sync(_store)
    return _store


def _ensure_governance_sync(store: MnemosyneRationalStore):
    try:
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
            from src.lachesis import CodebaseMapper
            from src.utils.project_path import get_project_root

            _mapper = CodebaseMapper(
                project_path=str(get_project_root()), spatial_store=_get_spatial()
            )
    return _mapper


def _ensure_spatial_index():
    mapper = _get_mapper()
    from cognition.mnemosyne.spatial_store import SpatialStore as _SpatialStore

    sp = _SpatialStore()
    if sp.get_module_count() > 0:
        return

    logger.info("Hephaestus: Spatial index empty. Triggering JIT codebase mapping...")
    mapper.map_codebase(deep=True)


def _get_semantic():
    global _semantic
    with _init_lock:
        if _semantic is None:
            from cognition.mnemosyne.semantic_store import SemanticStore

            _semantic = SemanticStore()
    return _semantic


def _get_temporal():
    global _temporal
    with _init_lock:
        if _temporal is None:
            from cognition.mnemosyne.temporal_store import TemporalStore

            _temporal = TemporalStore()
    return _temporal


def _get_reflection():
    global _reflection
    with _init_lock:
        if _reflection is None:
            from cognition.mnemosyne.reflection_store import ReflectionStore

            _reflection = ReflectionStore()
    return _reflection


def _get_failure_memory():
    global _failure_memory
    with _init_lock:
        if _failure_memory is None:
            from cognition.mnemosyne.semantic_store import FailureMemoryStore

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
