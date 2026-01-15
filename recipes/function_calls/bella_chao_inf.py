#!/usr/bin/env python3
"""
Basic Inference Setup (Hyperbolic via projectdavid.Entity)

- Loads environment (.env) without printing secrets
- Initializes Entity client
- Creates (or recreates) a minimal trading assistant with strict SYSTEM instructions
"""

import os
import sys
from textwrap import dedent

from dotenv import load_dotenv
from projectdavid import Entity

# ----------------------------
# Environment & client setup
# ----------------------------
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:9000")
ENTITIES_API_KEY = os.getenv("ENTITIES_API_KEY")
ENTITIES_USER_ID = os.getenv("ENTITIES_USER_ID")  # optional; keep if your backend needs it

# Optional Hyperbolic config (not used directly here but kept for clarity)
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
MODEL = "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
PROVIDER = "Hyperbolic"

if not ENTITIES_API_KEY:
    sys.exit("Missing ENTITIES_API_KEY. Set it in your environment or .env file.")

client = Entity(base_url=BASE_URL, api_key=ENTITIES_API_KEY)

# ----------------------------
# SYSTEM instructions
# ----------------------------
SYSTEM_PROMPT = dedent("""\
    SYSTEM — TARS-CRYPTO: SHORT-HORIZON DECISION AGENT

    Role:
    You make short-horizon trading decisions for liquid crypto pairs using ONLY the structured inputs provided each call.

    Operating modes (explicitly set by the user message):
    - MODE: DECIDE   → You must output exactly one word: buy | sell | hold
    - MODE: EVALUATE → You must output exactly one word: vindicated | invalidated
      (EVALUATE judges the prior DECIDE action using the new, later price window.)

    Inputs (always supplied by the caller):
    - SYMBOL: e.g., BTCUSDT
    - TIMEFRAME: e.g., 1m
    - LOOKBACK_BARS: e.g., 10 (most-recent CLOSED candles; no forming candle)
    - HORIZON_BARS: default 3 unless specified
    - PRICE_CSV: compact table of the last LOOKBACK_BARS candles with columns:
      t,o,h,l,c,v   (ISO8601, open, high, low, close, volume)
    - (Optional) COST_BPS: spread_bps + fees_bps + slippage_bps + buffer_bps
    - (Optional) SENTIMENT: numeric summary fields (mean, delta, dispersion, quality)

    Decision doctrine (DECIDE):
    1) Use only the provided data. No outside knowledge.
    2) Prefer simple, robust cues (momentum bursts, range breaks/retests, vol compression/expansion, short-term mean reversion).
    3) If COST_BPS provided, only trade when plausible edge > COST_BPS; otherwise hold.
    4) Determinism: identical inputs → identical outputs (assume temperature ≈ 0 upstream).
    5) If inputs are malformed, stale, or insufficient → hold.

    Evaluation doctrine (EVALUATE):
    - Given the previous DECIDE action and the new window beginning after that decision,
      judge the outcome over HORIZON_BARS:
        • If direction over the horizon matched the action by a non-trivial amount (vs typical 1-bar range): vindicated
        • Otherwise: invalidated
    - Output only the one required word.

    Output contract (strict):
    - MODE: DECIDE   → Output exactly: buy  OR  sell  OR  hold
    - MODE: EVALUATE → Output exactly: vindicated  OR  invalidated
    - No punctuation, no extra words, no JSON, no markdown.

    Guardrails:
    - Never suggest leverage, sizing, stops, or prices; handled externally.
    - Never reveal rationale or chain-of-thought.
    - If BLACKOUT or market status implies no trading (if provided), output hold.

    Defaults:
    - If HORIZON_BARS missing, assume 3 for 1m bars (10-back / 3-forward).
    - If COST_BPS missing, be conservative: favor hold unless the signal is clear.
""")

# Minimal tool list; expand only if you truly need them
TOOLS = [
    # {"type": "web_search"},
    # {"type": "file_search"},
    # {"type": "vector_store_search"},
    # {"type": "code_interpreter"},
    # {"type": "computer"},
]

ASSISTANT_NAME = "tars_crypto_agent"


def main() -> None:
    print("[+] Creating assistant…")
    assistant = client.assistants.create_assistant(
        name=ASSISTANT_NAME,
        instructions=SYSTEM_PROMPT,
        tools=TOOLS,
        # If your platform supports provider/model routing at assistant level, add:
        # model=MODEL,
        # provider=PROVIDER,
        # api_key=HYPERBOLIC_API_KEY,
        # user_id=ENTITIES_USER_ID,
    )
    print(f"[✓] Assistant created: {getattr(assistant, 'id', '<no id>')}")
    # Optional: print a compact summary instead of full object dump
    print("Name:", getattr(assistant, "name", "<unknown>"))
    if getattr(assistant, "tools", None):
        print("Tools:", assistant.tools)


if __name__ == "__main__":
    main()
