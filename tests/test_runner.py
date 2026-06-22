# tests/test_runner.py
from swingbot.run_backtest import load_instrument, run_one


def test_run_one_xauusd_executes():
    res = run_one("XAUUSD")
    assert "is" in res and "oos" in res and "trades" in res
    assert res["is"]["n"] + res["oos"]["n"] == len(res["trades"])
