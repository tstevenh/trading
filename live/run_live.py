"""Edgewise — Phase 2 paper-trading alert runner.
Each run: for the 3 locked strategies, fetch live data, evaluate the latest CLOSED
M15 bar, and (a) alert NEW entry signals, (b) manage open paper positions to their
exit (incl. ETH's partial+breakeven), journaling everything. Telegram alerts only —
no orders. Run once (cron) or with --loop SECONDS.

Usage:
  python -m live.run_live            # one scan
  python -m live.run_live --loop 900 # scan every 15 min
  python -m live.run_live --startup  # also send a heartbeat
"""
from __future__ import annotations
import sys, os, json, time, urllib.request, urllib.parse, pathlib, csv, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from swingbot.search import build_features_rich
from swingbot.backtest import _recent_pivots
from live import feeds

ENV = {}
for _l in pathlib.Path(".env").read_text().splitlines():
    _l = _l.strip()
    if _l and not _l.startswith("#") and "=" in _l:
        _k, _v = _l.split("=", 1); ENV[_k.strip()] = _v.split("#")[0].strip()
TOK, CHAT = ENV.get("TELEGRAM_BOT_TOKEN", ""), ENV.get("TELEGRAM_CHAT_ID", "")
RISK_PCT = ENV.get("RISK_PCT", "0.5")

STATE = pathlib.Path("live/state.json")
JOURNAL = pathlib.Path("live/journal.csv")

# 3 locked strategies. exit: ("fixed", rr) or ("partial", t1, frac, runner_rr)
STRATS = [
    dict(key="SPX500", arch="mean_reversion", variant="mr_adx18_rsi30_sm15", exit=("fixed", 3.0)),
    dict(key="ETHUSD", arch="trend_pullback_plus", variant="tpp_adx18_rsi45_relaxed", exit=("partial", 1.0, 0.5, 3.0)),
    dict(key="EURUSD", arch="trend_pullback_plus", variant="tpp_adx18_rsi48", exit=("fixed", 2.0)),
]


def tg(text):
    if not TOK or not CHAT:
        print("[tg skipped — no token/chat]\n" + text); return
    url = f"https://api.telegram.org/bot{TOK}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except Exception as e:
        print("tg fail:", str(e)[:80])


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(s):
    STATE.write_text(json.dumps(s, indent=2, default=str))


def journal(row):
    new = not JOURNAL.exists()
    with open(JOURNAL, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts", "strategy", "event", "side", "entry", "stop", "tp", "outcome_r", "note"])
        w.writerow(row)


def sig_fn(arch, variant):
    mod = importlib.import_module(f"swingbot.archetypes.{arch}")
    v = mod.variants(); items = v.items() if isinstance(v, dict) else v
    fn = next(fn for lbl, fn in items if lbl == variant)
    return fn, list(getattr(mod, "REQUIRED_COLS", []))


def features(instr):
    m15 = feeds.fetch(instr, "m15", 400)
    h1 = feeds.fetch(instr, "h1", 400)
    d1 = feeds.fetch(instr, "d1", 250)
    return build_features_rich(m15, h1, d1)


def check_entry(st, feats, cols):
    f = feats.dropna(subset=cols) if cols else feats.dropna()
    if len(f) < 50:
        return None
    i = len(f) - 1
    row = f.iloc[i].to_dict()
    highs, lows = f["high"].to_numpy(), f["low"].to_numpy()
    piv = _recent_pivots(highs, lows, i, 40)
    fn, _ = sig_fn(st["arch"], st["variant"])
    return fn(row, piv, f.index[i])


def manage(pos, instr):
    """Walk bars since entry; return (closed, alerts, updated_pos)."""
    f = feeds.fetch(instr, "m15", 300)
    after = f[f.index > pd.Timestamp(pos["entry_ts"])]
    side, entry, risk = pos["side"], pos["entry"], pos["risk"]
    stop, tp = pos["stop"], pos["tp"]
    t1 = pos.get("t1"); frac = pos.get("frac", 0.0); partial_done = pos.get("partial_done", False)
    banked = pos.get("banked", 0.0)
    alerts = []
    for ts, b in after.iterrows():
        hi, lo = b["high"], b["low"]
        # stop first (conservative)
        hit_stop = (lo <= stop) if side == 1 else (hi >= stop)
        if hit_stop:
            leg_r = side * (stop - entry) / risk
            total = banked + (1 - frac if partial_done else 1.0) * leg_r if t1 else leg_r
            tag = "runner stopped@BE" if partial_done else "STOP"
            alerts.append(("close", f"{'🟦' if total>=0 else '🟥'} {pos['key']} {tag} → {total:+.2f}R (paper)", total))
            return True, alerts, pos
        # partial milestone (ETH)
        if t1 and not partial_done:
            hit_t1 = (hi >= entry + side * t1 * risk) if side == 1 else (lo <= entry - side * t1 * risk)
            if hit_t1:
                banked = frac * t1
                partial_done = True; stop = entry
                pos.update(partial_done=True, stop=entry, banked=banked)
                alerts.append(("info", f"🟨 {pos['key']} +{t1:.0f}R — take {int(frac*100)}% partial, move stop to BREAKEVEN. Runner targets {pos['runner_rr']:.0f}R.", None))
        # target
        hit_tp = (hi >= tp) if side == 1 else (lo <= tp)
        if hit_tp:
            leg_r = side * (tp - entry) / risk
            total = banked + (1 - frac) * leg_r if (t1 and partial_done) else leg_r
            alerts.append(("close", f"🟩 {pos['key']} TARGET hit → {total:+.2f}R (paper)", total))
            return True, alerts, pos
    return False, alerts, pos


def scan(startup=False):
    if startup:
        tg("📡 Edgewise scan online (paper). Watching SPX500 · ETHUSD · EURUSD.")
    state = load_state()
    now = pd.Timestamp.now("UTC")
    for st in STRATS:
        key = st["key"]
        try:
            feats = features(key)
        except Exception as e:
            print(f"{key}: data error {str(e)[:80]}"); continue
        pos = state.get(key)
        if pos:  # manage open
            closed, alerts, pos = manage(pos, key)
            for kind, msg, r in alerts:
                tg(msg)
                if kind == "close":
                    journal([now, key, "close", pos["side"], pos["entry"], pos["stop"], pos["tp"], f"{r:.3f}", ""])
            state[key] = None if closed else pos
            print(f"{key}: {'closed' if closed else 'open'}{' '+str(len(alerts))+' alert(s)' if alerts else ''}")
        else:    # look for entry
            cols = sig_fn(st["arch"], st["variant"])[1]
            sig = check_entry(st, feats, cols)
            if sig is None:
                print(f"{key}: no signal"); continue
            entry, stop, side = sig.entry, sig.stop, sig.side
            risk = abs(entry - stop)
            etyp = st["exit"]
            if etyp[0] == "fixed":
                rr = etyp[1]; tp = entry + side * rr * risk; t1 = None; frac = 0.0; runner = rr
            else:
                _, t1, frac, runner = etyp; tp = entry + side * runner * risk
            pos = dict(key=key, arch=st["arch"], variant=st["variant"], side=side,
                       entry=entry, stop=stop, risk=risk, tp=tp, t1=t1, frac=frac,
                       runner_rr=runner, partial_done=False, banked=0.0,
                       entry_ts=str(sig.ts))
            d = "LONG" if side == 1 else "SHORT"
            plan = (f"🟢 NEW SIGNAL — {key} ({st['arch'].replace('_',' ')})\n"
                    f"{d}  |  risk {RISK_PCT}%\n"
                    f"Entry ~{entry:.4f} (market)\n"
                    f"Stop {stop:.4f}   (1R = {risk:.4f})\n"
                    f"Target {tp:.4f}  ({runner:.0f}R)\n"
                    + (f"Plan: take {int(frac*100)}% at +{t1:.0f}R → stop to breakeven → runner to {runner:.0f}R\n" if t1 else "")
                    + f"Bar {sig.ts} UTC · paper")
            tg(plan)
            journal([now, key, "open", side, f"{entry:.4f}", f"{stop:.4f}", f"{tp:.4f}", "", st["variant"]])
            state[key] = pos
            print(f"{key}: NEW SIGNAL {d}")
    save_state(state)


if __name__ == "__main__":
    args = sys.argv[1:]
    startup = "--startup" in args
    loop = None
    if "--loop" in args:
        loop = int(args[args.index("--loop") + 1])
    if loop:
        scan(startup=True)
        while True:
            time.sleep(loop)
            try:
                scan()
            except Exception as e:
                print("scan error:", str(e)[:100])
    else:
        scan(startup=startup)
