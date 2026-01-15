#!/usr/bin/env python3
# bella_chao.py — Fetch → Prompt → Inference (existing assistant)

import os
import sys
from io import StringIO
from typing import Optional, Iterable

import pandas as pd
from dotenv import load_dotenv
from projectdavid import Entity

# ---- bring your fetcher ----
# Make sure tars_price_fetcher.py (with class PriceFetcher) is on PYTHONPATH / same folder.
from bella_chao import PriceFetcher   # <-- your class as posted

# ---------------- Env & client ----------------
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:9000")
ENTITIES_API_KEY = os.getenv("ENTITIES_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")            # existing assistant id
ENTITIES_USER_ID = os.getenv("ENTITIES_USER_ID")    # optional
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
PROVIDER = os.getenv("PROVIDER", "Hyperbolic")
MODEL = os.getenv("MODEL", "hyperbolic/deepseek-ai/DeepSeek-V3-0324")

if not ENTITIES_API_KEY:
    sys.exit("Missing ENTITIES_API_KEY.")
if not ASSISTANT_ID:
    sys.exit("Missing ASSISTANT_ID (existing assistant id required).")

client = Entity(base_url=BASE_URL, api_key=ENTITIES_API_KEY)

# ------------- Orchestrator (existing assistant) -------------
class InferenceOrchestrator:
    def __init__(
        self,
        assistant_id: str,
        provider: str = PROVIDER,
        model: str = MODEL,
        hyperbolic_api_key: Optional[str] = HYPERBOLIC_API_KEY,
        user_id: Optional[str] = ENTITIES_USER_ID,
    ):
        self.assistant_id = assistant_id
        self.provider = provider
        self.model = model
        self.hyperbolic_api_key = hyperbolic_api_key
        self.user_id = user_id

        self.thread_id: Optional[str] = None
        self.message_id: Optional[str] = None
        self.run_id: Optional[str] = None

    def create_thread(self) -> str:
        kwargs = {}
        if self.user_id:
            kwargs["participant_ids"] = [self.user_id]
        thread = client.threads.create_thread(**kwargs)
        self.thread_id = thread.id
        return self.thread_id

    def create_message(self, content: str) -> str:
        if not self.thread_id:
            raise RuntimeError("Thread not created yet.")
        msg = client.messages.create_message(
            thread_id=self.thread_id,
            role="user",
            content=content,
            assistant_id=self.assistant_id,
        )
        self.message_id = msg.id
        return self.message_id

    def create_run(self) -> str:
        if not self.thread_id:
            raise RuntimeError("Thread not created yet.")
        run = client.runs.create_run(
            assistant_id=self.assistant_id,
            thread_id=self.thread_id,
            truncation_strategy="auto",
        )
        self.run_id = run.id
        return self.run_id

    def setup_stream(self) -> None:
        if not all([self.user_id, self.thread_id, self.assistant_id, self.message_id, self.run_id]):
            raise RuntimeError("user_id, thread_id, assistant_id, message_id, and run_id required for streaming.")
        stream = client.synchronous_inference_stream
        stream.setup(
            user_id=self.user_id,
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            message_id=self.message_id,
            run_id=self.run_id,
            api_key=self.hyperbolic_api_key,
        )

    def stream(self, timeout_per_chunk: float = 180.0) -> Iterable[str]:
        for chunk in client.synchronous_inference_stream.stream_chunks(
            provider=self.provider,
            model=self.model,
            timeout_per_chunk=timeout_per_chunk,
        ):
            content = chunk.get("content", "")
            if content:
                yield content

    def run_once(self, content: str) -> str:

        self.create_thread()
        self.create_message(content)
        self.create_run()
        self.setup_stream()

        out = []
        for token in self.stream():
            print(token, end="", flush=True)   # live echo
            out.append(token)
        print("\n--- End of Stream ---")
        return "".join(out)

# ------------- Prompt builder (DECIDE) -------------
def df_to_price_csv(df: pd.DataFrame) -> str:
    """
    Convert OHLCV DF to compact CSV: t,o,h,l,c,v with ISO8601 UTC timestamp.
    Assumes df has columns: ts, open, high, low, close, volume, t(utc)
    """
    cols = ["t","o","h","l","c","v"]
    out = [",".join(cols)]
    for _, r in df.iterrows():
        out.append(
            f"{pd.to_datetime(r['t']).strftime('%Y-%m-%dT%H:%M:%SZ')},"
            f"{round(float(r['open']), 2)},"
            f"{round(float(r['high']), 2)},"
            f"{round(float(r['low']),  2)},"
            f"{round(float(r['close']),2)},"
            f"{round(float(r['volume']),3)}"
        )
    return "\n".join(out)

def build_decide_prompt(
    symbol: str,
    timeframe: str,
    lookback_bars: int,
    horizon_bars: int = 3,
    df: Optional[pd.DataFrame] = None,
    cost_bps: Optional[float] = None,
) -> str:
    """
    Constructs the strict one-shot DECIDE prompt per your SYSTEM contract.
    Only includes the fields the agent expects, in plain text.
    """
    if df is None or len(df) < lookback_bars:
        raise ValueError("Insufficient data for the requested lookback_bars.")
    csv_text = df_to_price_csv(df.tail(lookback_bars))

    header_lines = [
        "MODE: DECIDE",
        f"SYMBOL: {symbol.replace('/', '')}",
        f"TIMEFRAME: {timeframe}",
        f"LOOKBACK_BARS: {lookback_bars}",
        f"HORIZON_BARS: {horizon_bars}",
    ]
    if cost_bps is not None:
        header_lines.append(f"COST_BPS: {cost_bps:.2f}")

    # Important: blank line before PRICE_CSV for readability; the agent uses only the content.
    prompt = "\n".join(header_lines) + "\nPRICE_CSV:\n" + csv_text
    return prompt

# ------------- Main entry: fetch → decide -------------
def main():
    # ---- fetch the last N closed minutes (default 10m) ----
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1m")
    lookback = os.getenv("LOOKBACK", "10m")   # can be "10m" or integer bars via your fetcher
    horizon_bars = int(os.getenv("HORIZON_BARS", "3"))
    cost_bps = os.getenv("COST_BPS")          # optional

    # instantiate your fetcher
    pf = PriceFetcher(symbol=symbol, timeframe=timeframe, lookback=lookback)
    df = pf.fetch()

    # resolve effective lookback bars (so prompt & data match exactly)
    # If LOOKBACK was a string like "10m", PriceFetcher already converted; we recompute here
    if isinstance(lookback, str):
        # reuse fetcher internals by asking for the final window length:
        lookback_bars = len(df)
    else:
        lookback_bars = int(lookback)

    # build DECIDE prompt
    prompt = build_decide_prompt(
        symbol=symbol,
        timeframe=timeframe,
        lookback_bars=lookback_bars,
        horizon_bars=horizon_bars,
        df=df,
        cost_bps=float(cost_bps) if cost_bps is not None else None,
    )

    # ---- run inference with existing assistant ----
    orchestrator = InferenceOrchestrator(assistant_id=ASSISTANT_ID)
    orchestrator.run_once(prompt)

if __name__ == "__main__":
    main()
