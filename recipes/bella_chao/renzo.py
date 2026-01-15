#!/usr/bin/env python3
# renzo.py — Continuous trading signal simulator with risk management (profit-tilted)

import os
import sys
import time
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

from bella_chao import PriceFetcher
from atr_predictor import TargetPredictor
from identity_service import IdentifierService
from inference import InferenceOrchestrator, build_decide_prompt

load_dotenv()

# ────────── Data / Timing Config ──────────
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
LOOKBACK = os.getenv("LOOKBACK", "30m")  # explicit lookback overrides auto-scaling
HORIZON_BARS = int(os.getenv("HORIZON_BARS", "5"))  # default 5 → more follow-through

# ────────── Data / ID Config ──────────
POSITION_ID = IdentifierService.generate_position_id()

# Timeframe mapping for horizon-aware cadence
_TF_SEC = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400}
if TIMEFRAME not in _TF_SEC:
    raise ValueError(f"Unsupported TIMEFRAME={TIMEFRAME}")

# Loop cadence defaults to the evaluation horizon (can still override via env)
INTERVAL_SEC = int(os.getenv("INTERVAL_SEC", str(HORIZON_BARS * _TF_SEC[TIMEFRAME])))

# ────────── Cost Model (bps) ──────────
# If you can post-only, set USE_MAKER=true in .env; otherwise taker fees are assumed.
TAKER_FEE_BPS    = float(os.getenv("TAKER_FEE_BPS", "6"))   # 0.06% taker (example)
MAKER_FEE_BPS    = float(os.getenv("MAKER_FEE_BPS", "2"))   # 0.02% maker (example)
SLIPPAGE_BPS     = float(os.getenv("SLIPPAGE_BPS",  "2"))   # 0.02% slippage
SPREAD_BPS       = float(os.getenv("SPREAD_BPS",    "2"))   # 0.02% spread
COST_BUFFER_BPS  = float(os.getenv("COST_BUFFER_BPS", "2")) # safety margin
USE_MAKER        = os.getenv("USE_MAKER", "false").lower() == "true"

FEE_BPS   = MAKER_FEE_BPS if USE_MAKER else TAKER_FEE_BPS
COST_BPS  = FEE_BPS + SLIPPAGE_BPS + SPREAD_BPS + COST_BUFFER_BPS  # effective round-trip cost floor

# ────────── Risk & Filters ──────────
TAKE_PROFIT_ATR_MULTIPLIER = float(os.getenv("TAKE_PROFIT_ATR_MULTIPLIER", "2.5"))
STOP_LOSS_ATR_MULTIPLIER   = float(os.getenv("STOP_LOSS_ATR_MULTIPLIER", "1.5"))
MIN_RISK_REWARD_RATIO      = float(os.getenv("MIN_RISK_REWARD_RATIO", "1.6"))

# Skip dead markets and weak momentum
MIN_ATR_BPS   = float(os.getenv("MIN_ATR_BPS", "2.0"))   # per-bar ATR threshold (bps)
MIN_SLOPE_BPS = float(os.getenv("MIN_SLOPE_BPS", "1.0")) # min |slope| in bps/bar aligned with decision

# Anti-whipsaw cooldown (bars)
COOLDOWN_BARS = int(os.getenv("COOLDOWN_BARS", "3"))

# ────────── Logging / Infra ──────────
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
LOG_PATH     = os.getenv("SIGNAL_LOG", "signals_log.csv")

# ────────── Helpers ──────────
def now_utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def append_log(record: dict):
    """Append or create signals_log.csv with new record."""
    df_new = pd.DataFrame([record])
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(LOG_PATH, index=False)
    print(f"[📊] Log updated → {LOG_PATH} ({len(df)} total rows)")

def pct_to_bps(x: float) -> float:
    return x * 1e4

# ────────── Main trading loop ──────────
def main():
    if not ASSISTANT_ID:
        sys.exit("Missing ASSISTANT_ID in environment.")

    orchestrator = InferenceOrchestrator(assistant_id=ASSISTANT_ID)
    fetcher      = PriceFetcher(symbol=SYMBOL, timeframe=TIMEFRAME, lookback=LOOKBACK)
    predictor    = TargetPredictor(price_fetcher=fetcher)

    print(
        f"[TARS] Engine online → {SYMBOL} | TF={TIMEFRAME} | LOOKBACK={LOOKBACK} | "
        f"HORIZON_BARS={HORIZON_BARS} | INTERVAL={INTERVAL_SEC}s | "
        f"COST_BPS={COST_BPS:.2f} (USE_MAKER={USE_MAKER})\n"
    )

    # Cooldown state
    last_action = None            # 'buy' | 'sell' | None
    last_action_bar_index = -10   # index of last trade bar
    bar_counter = 0

    while True:
        cycle_started = datetime.utcnow()
        try:
            # 1) Fetch latest closed bars
            df = fetcher.fetch()
            current_price = float(df.iloc[-1]["close"])
            lookback_bars = len(df)

            # 2) Build strict DECIDE prompt
            prompt = build_decide_prompt(
                symbol=SYMBOL,
                timeframe=TIMEFRAME,
                lookback_bars=lookback_bars,
                horizon_bars=HORIZON_BARS,
                df=df,
                cost_bps=COST_BPS,
            )

            # 3) LLM decision
            print(f"[{datetime.utcnow().isoformat()}] Fetching decision…")
            llm_decision = orchestrator.run_once(prompt).strip().lower()
            if llm_decision not in ("buy", "sell", "hold"):
                print(f"[⚠️] Unexpected decision output: {llm_decision!r} → coercing to 'hold'")
                llm_decision = "hold"

            # 4) Volatility & momentum regime checks (before risk blocks)
            #    ATR from predictor (price units) → convert to bps at current_price
            _, atr_price = predictor.get_atr_and_target(current_price, COST_BPS, TAKE_PROFIT_ATR_MULTIPLIER)
            atr_bps = (atr_price / current_price) * 1e4 if atr_price > 0 else 0.0

            # Simple 5-bar slope in bps/bar
            if len(df) >= 6:
                slope_bps_per_bar = pct_to_bps((df["close"].iloc[-1] - df["close"].iloc[-6]) / df["close"].iloc[-6]) / 5.0
            else:
                slope_bps_per_bar = 0.0

            # Gate 1: ATR must exceed threshold
            if atr_bps < MIN_ATR_BPS and llm_decision in ("buy", "sell"):
                print(f"[⛔] ATR too low ({atr_bps:.2f} bps < {MIN_ATR_BPS} bps). → HOLD")
                llm_decision = "hold"

            # Gate 2: Momentum slope must align with the signal
            if llm_decision == "buy" and slope_bps_per_bar < MIN_SLOPE_BPS:
                print(f"[⛔] Slope {slope_bps_per_bar:.2f} bps/bar < {MIN_SLOPE_BPS}. BUY → HOLD")
                llm_decision = "hold"
            if llm_decision == "sell" and slope_bps_per_bar > -MIN_SLOPE_BPS:
                print(f"[⛔] Slope {slope_bps_per_bar:.2f} bps/bar > -{MIN_SLOPE_BPS}. SELL → HOLD")
                llm_decision = "hold"

            # Gate 3: Cooldown to avoid whipsaw flips (only block trade actions, not hold)
            if last_action in ("buy", "sell") and llm_decision in ("buy", "sell"):
                if (bar_counter - (last_action_bar_index or -10)) < COOLDOWN_BARS:
                    print(f"[🧊] Cooldown active ({COOLDOWN_BARS} bars). Ignoring trade → HOLD")
                    llm_decision = "hold"

            # 5) Initialize risk vars & final decision
            take_profit_price = 0.0
            stop_loss_price   = 0.0
            risk_reward_ratio = 0.0
            final_decision    = llm_decision

            # Expected TP distance (in bps) using ATR * TP multiple (used for cost-vs-edge gate)
            tp_distance_price = atr_price * TAKE_PROFIT_ATR_MULTIPLIER if atr_price > 0 else 0.0
            tp_distance_bps   = (tp_distance_price / current_price) * 1e4 if tp_distance_price > 0 else 0.0

            # Gate 4: Only trade if expected TP distance clears the cost floor
            if final_decision in ("buy", "sell"):
                if tp_distance_bps <= COST_BPS:
                    print(f"[⛔] Edge too small: TP {tp_distance_bps:.2f} bps ≤ COST {COST_BPS:.2f} bps. → HOLD")
                    final_decision = "hold"

            # 6) Symmetric risk filter (BUY & SELL) with ATR-derived TP/SL + R/R
            if final_decision == "buy":
                if atr_price > 0:
                    potential_reward = atr_price * TAKE_PROFIT_ATR_MULTIPLIER
                    potential_risk   = atr_price * STOP_LOSS_ATR_MULTIPLIER
                    risk_reward_ratio = (potential_reward / potential_risk) if potential_risk > 0 else 0.0

                    if risk_reward_ratio >= MIN_RISK_REWARD_RATIO:
                        take_profit_price = current_price + potential_reward
                        stop_loss_price   = current_price - potential_risk
                        print(f"[✅] BUY Validated. R/R {risk_reward_ratio:.2f} | "
                              f"TP={take_profit_price:.2f} SL={stop_loss_price:.2f} ATR={atr_price:.2f}")
                    else:
                        final_decision = "hold"
                        print(f"[❌] BUY Invalidated (R/R {risk_reward_ratio:.2f} < {MIN_RISK_REWARD_RATIO}). → HOLD")
                else:
                    final_decision = "hold"
                    print("[⚠️] ATR=0 for BUY. → HOLD")

            elif final_decision == "sell":
                if atr_price > 0:
                    potential_reward = atr_price * TAKE_PROFIT_ATR_MULTIPLIER
                    potential_risk   = atr_price * STOP_LOSS_ATR_MULTIPLIER
                    risk_reward_ratio = (potential_reward / potential_risk) if potential_risk > 0 else 0.0

                    if risk_reward_ratio >= MIN_RISK_REWARD_RATIO:
                        take_profit_price = current_price - potential_reward
                        stop_loss_price   = current_price + potential_risk
                        print(f"[✅] SELL Validated. R/R {risk_reward_ratio:.2f} | "
                              f"TP={take_profit_price:.2f} SL={stop_loss_price:.2f} ATR={atr_price:.2f}")
                    else:
                        final_decision = "hold"
                        print(f"[❌] SELL Invalidated (R/R {risk_reward_ratio:.2f} < {MIN_RISK_REWARD_RATIO}). → HOLD")
                else:
                    final_decision = "hold"
                    print("[⚠️] ATR=0 for SELL. → HOLD")

            # If we accepted a trade, update cooldown anchors
            if final_decision in ("buy", "sell"):
                last_action = final_decision
                last_action_bar_index = bar_counter

            # 7) Log record (with eval schedule)
            decision_epoch = int(datetime.utcnow().timestamp())
            eval_due_epoch = decision_epoch + HORIZON_BARS * _TF_SEC[TIMEFRAME]

            record = {
                "timestamp": now_utc_naive().isoformat(),
                "position_id": IdentifierService.generate_position_id(),
                "decision_epoch": decision_epoch,
                "eval_due_epoch": eval_due_epoch,
                "symbol": SYMBOL,
                "timeframe": TIMEFRAME,
                "llm_decision": llm_decision,
                "final_decision": final_decision,
                "price_close": current_price,
                "take_profit_price": take_profit_price,
                "stop_loss_price": stop_loss_price,
                "atr_price": atr_price,
                "atr_bps": round((atr_price / current_price) * 1e4, 4) if atr_price > 0 else 0.0,
                "slope_bps_per_bar": round(slope_bps_per_bar, 4),
                "tp_distance_bps": round(tp_distance_bps, 4),
                "risk_reward_ratio": round(risk_reward_ratio, 4),
                "cost_bps_effective": round(COST_BPS, 4),
                "spread_bps": SPREAD_BPS,
                "slippage_bps": SLIPPAGE_BPS,
                "fee_bps": FEE_BPS,
                "use_maker": USE_MAKER,
                "lookback_bars": lookback_bars,
                "horizon_bars": HORIZON_BARS,
                "cooldown_bars": COOLDOWN_BARS,
                "evaluated": False,
                "result": "",        # "vindicated" | "invalidated" (to be filled by evaluator)
                "notes": "",
            }


            append_log(record)

        except Exception as e:
            print(f"[❌] Error in loop: {e}")

        # 8) Horizon-aligned sleep
        elapsed = (datetime.utcnow() - cycle_started).total_seconds()
        sleep_s = max(0.0, INTERVAL_SEC - elapsed)
        print(f"[TARS] Sleeping {sleep_s/60.0:.2f} minutes…\n")
        time.sleep(sleep_s)

        # Tick bar counter
        bar_counter += 1

if __name__ == "__main__":
    main()
