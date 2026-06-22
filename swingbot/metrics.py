# swingbot/metrics.py
import numpy as np


def summarize(trades, risk_pct: float = 1.0) -> dict:
    if not trades:
        return {"n": 0, "win_rate": 0.0, "avg_r": 0.0, "expectancy_r": 0.0,
                "profit_factor": 0.0, "max_drawdown_r": 0.0, "sharpe": 0.0,
                "equity_final_r": 0.0}
    r = np.array([t.outcome_r for t in trades], dtype=float)
    wins = r[r > 0]
    losses = r[r < 0]
    equity = np.cumsum(r * risk_pct)
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity).max()
    sharpe = (r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else 0.0
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    return {
        "n": len(r),
        "win_rate": float((r > 0).mean()),
        "avg_r": float(r.mean()),
        "expectancy_r": float(r.mean()),
        "profit_factor": float(pf),
        "max_drawdown_r": float(dd),
        "sharpe": float(sharpe),
        "equity_final_r": float(equity[-1]),
    }
