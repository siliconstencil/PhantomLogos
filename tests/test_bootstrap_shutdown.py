from src.clotho.bootstrap import (
    _STARTUP_REGISTRY,
    _is_our_slm,
    _register_for_shutdown,
    _shutdown_all,
)


def test_is_our_slm_no_daemon():
    status = _is_our_slm("127.0.0.1", 18765)
    assert status == "none"


def test_startup_registry_lifo_order():
    _STARTUP_REGISTRY.clear()
    order = []
    _register_for_shutdown("first", lambda: order.append("first"))
    _register_for_shutdown("second", lambda: order.append("second"))
    _register_for_shutdown("third", lambda: order.append("third"))
    _shutdown_all()
    assert order == ["third", "second", "first"]
    assert len(_STARTUP_REGISTRY) == 0


def test_startup_registry_clear_after_shutdown():
    _STARTUP_REGISTRY.clear()
    _register_for_shutdown("dummy", lambda: None)
    _shutdown_all()
    assert len(_STARTUP_REGISTRY) == 0
