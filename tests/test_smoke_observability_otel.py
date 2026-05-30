from src.atropos.observability import AtroposMonitor, get_otel_tracer, init_opentelemetry


def test_init_opentelemetry_no_packages():
    tracer = init_opentelemetry()
    assert tracer is None or hasattr(tracer, "start_as_current_span")


def test_get_otel_tracer_default():
    tracer = get_otel_tracer()
    assert tracer is None or hasattr(tracer, "start_as_current_span")


def test_atropos_monitor_init_otel():
    monitor = AtroposMonitor()
    assert hasattr(monitor, "_otel_ready")
    assert hasattr(monitor, "_tracer")
