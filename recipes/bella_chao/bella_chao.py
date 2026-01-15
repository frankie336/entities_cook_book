#!/usr/bin/env python3
# bella_chao.py
"""
tars_price_fetcher.py — Class-based OHLCV fetcher (Binance via CCXT)

- Default look-back = 10 minutes on the chosen timeframe (e.g., 1m → 10 bars).
- Always excludes the currently forming candle (aligns to "now").
- Paginates until it has the required number of CLOSED bars.
- Simple CLI retained for convenience; you can also import and use the class directly.

Usage (CLI):
  pip install ccxt pandas
  python tars_price_fetcher.py --symbol BTC/USDT --timeframe 1m
  python tars_price_fetcher.py --symbol ETH/USDT --timeframe 5m --lookback 60m --out eth_5m.csv

Usage (import):
  from tars_price_fetcher import PriceFetcher
  pf = PriceFetcher(symbol="BTC/USDT", timeframe="1m", lookback="10m")
  df = pf.fetch()
  print(df.tail())
"""
import argparse
import math
from typing import List, Optional, Union
import pandas as pd
import ccxt

SUPPORTED_TF = ["1m","3m","5m","15m","30m","1h","2h","4h","1d"]

class PriceFetcher:
    def __init__(self,
                 symbol: str = "BTC/USDT",
                 timeframe: str = "1m",
                 lookback: Union[str, int] = "10m"  # "10m", "2h", "1d" or integer bars
                 ):
        """
        lookback:
          - str like "10m","90m","6h","2d"  → converted to bars for the given timeframe
          - int (bars) → use as-is
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.lookback = lookback
        self.ex = ccxt.binance({
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
            },
        })

    # ---------- public API ----------
    def fetch(self) -> pd.DataFrame:
        """Fetch the last N CLOSED candles aligned to 'now' based on the current lookback."""
        limit = self._resolve_limit(self.lookback, self.timeframe)
        return self._fetch_last_n(self.symbol, self.timeframe, limit)

    def set_lookback(self, lookback: Union[str, int]) -> None:
        self.lookback = lookback

    # ---------- internals ----------
    @staticmethod
    def _timeframe_to_ms(tf: str) -> int:
        m = {"1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
             "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000,
             "1d": 86_400_000}
        if tf not in m:
            raise ValueError(f"Unsupported timeframe: {tf}")
        return m[tf]

    @staticmethod
    def _parse_lookback_str(s: str) -> int:
        """Return milliseconds for strings like '90m','6h','2d'."""
        unit = s[-1].lower()
        val = float(s[:-1])
        if unit == "m":
            return int(val * 60_000)
        if unit == "h":
            return int(val * 3_600_000)
        if unit == "d":
            return int(val * 86_400_000)
        raise ValueError("lookback must end with m/h/d, e.g., 10m, 90m, 6h, 2d")

    def _resolve_limit(self, lookback: Union[str, int], timeframe: str) -> int:
        """Convert lookback to bar count (limit). Defaults to 10 bars for 1m if lookback is '10m'."""
        if isinstance(lookback, int):
            return max(1, lookback)
        if isinstance(lookback, str):
            lb_ms = self._parse_lookback_str(lookback)
            ms_per_bar = self._timeframe_to_ms(timeframe)
            return max(1, math.ceil(lb_ms / ms_per_bar))
        raise TypeError("lookback must be int (bars) or str like '10m','6h','2d'.")

    def _fetch_last_n(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        ms_per_bar = self._timeframe_to_ms(timeframe)
        now_ms = self.ex.milliseconds()
        now_floor = (now_ms // ms_per_bar) * ms_per_bar  # open time of current forming bar

        rows: List[list] = []
        # Start sufficiently back; page forward until we cover limit
        since = now_ms - (limit + 1000) * ms_per_bar
        while len(rows) < limit + 5:  # small buffer
            chunk = self.ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            if not chunk:
                break
            rows.extend(chunk)
            last_ts = chunk[-1][0]
            since = last_ts + ms_per_bar
            if since >= now_floor + ms_per_bar:
                break

        if not rows:
            raise RuntimeError("No OHLCV returned from exchange.")

        df = pd.DataFrame(rows, columns=["ts","open","high","low","close","volume"])
        df = df.drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)
        # Keep only CLOSED bars before the current forming candle
        df = df[df["ts"] < now_floor].tail(limit).reset_index(drop=True)
        df["t"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        return df

# -------------- CLI --------------
def _build_cli():
    ap = argparse.ArgumentParser(description="Fetch last N closed OHLCV candles aligned to now (Binance spot).")
    # FIX: Corrected ap.add.argument to ap.add_argument
    ap.add_argument("--symbol", default="BTC/USDT", help="e.g., BTC/USDT (default: BTC/USDT)")
    ap.add_argument("--timeframe", default="1m", choices=SUPPORTED_TF, help="default: 1m")
    ap.add_argument("--lookback", default="10m",
                    help="Look-back window, e.g., 10m, 90m, 6h, 2d OR integer bars (default: 10m)")
    ap.add_argument("--out", help="Optional CSV output path")
    return ap

def main():
    ap = _build_cli()
    args = ap.parse_args()

    # allow integer bars via CLI too
    try:
        lookback: Union[str, int] = int(args.lookback)
    except ValueError:
        lookback = args.lookback  # keep as string like "10m"

    pf = PriceFetcher(symbol=args.symbol, timeframe=args.timeframe, lookback=lookback)
    df = pf.fetch()

    print(df.tail(10).to_string(index=False))
    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nSaved {len(df)} rows → {args.out}")

if __name__ == "__main__":
    main()