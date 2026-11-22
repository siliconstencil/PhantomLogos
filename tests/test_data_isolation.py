import os
from pathlib import Path

from src.utils.project_path import get_data_dir, get_project_root, to_absolute_path


def test_data_dir_is_redirected_by_the_environment():
    """The test session must not resolve database paths inside the real data/ directory."""
    assert os.environ.get("PHANTOM_DATA_DIR"), "PHANTOM_DATA_DIR is not set for the test session"
    data_dir = Path(get_data_dir())
    assert data_dir != get_project_root() / "data"
    assert str(data_dir).startswith(os.environ["PHANTOM_DATA_DIR"])


def test_data_relative_paths_follow_the_data_dir():
    """A 'data/...' relative path resolves inside the redirected data directory."""
    resolved = Path(to_absolute_path("data/mnemosyne.db"))
    assert resolved.parent == Path(get_data_dir())


def test_non_data_paths_still_resolve_against_the_project_root():
    """Paths outside data/ keep their old meaning."""
    assert Path(to_absolute_path("dashboard/index.html")) == (
        get_project_root() / "dashboard" / "index.html"
    )


def test_the_cache_stores_resolve_inside_the_redirected_data_dir():
    """The cache stores must not hardcode the real data directory."""
    from src.architrave.context_cache import ContextCacheStore

    store = ContextCacheStore(start_sweep=False)
    assert Path(store.db_path).parent == Path(get_data_dir())
