import inspect

import omega_quant.monitor.live_monitor as lm


def test_live_monitor_does_not_import_execution_paths():
    src = inspect.getsource(lm)
    assert "omega_quant.execution" not in src
    assert "place_limit_order" not in src
