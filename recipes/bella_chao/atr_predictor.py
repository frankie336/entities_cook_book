# predictor.py
"""
A class to predict a minimal profitable price target based on market volatility.
"""
import pandas as pd
from bella_chao import PriceFetcher

class TargetPredictor:
    """
    Calculates volatility-based price targets.
    """
    def __init__(self, price_fetcher: PriceFetcher, atr_period: int = 14):
        """
        Initializes the TargetPredictor.

        Args:
            price_fetcher: An instance of the PriceFetcher class.
            atr_period: The period over which to calculate the Average True Range (ATR).
        """
        self.price_fetcher = price_fetcher
        self.atr_period = atr_period

    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """
        Calculates the Average True Range (ATR) for the given data.

        Args:
            df: A pandas DataFrame with 'high', 'low', and 'close' columns.

        Returns:
            The latest ATR value.
        """
        if df.empty or len(df) < self.atr_period:
            return 0.0

        high_low = df['high'] - df['low']
        high_prev_close = (df['high'] - df['close'].shift(1)).abs()
        low_prev_close = (df['low'] - df['close'].shift(1)).abs()

        true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        # Calculate Exponential Moving Average of True Range
        atr = true_range.ewm(alpha=1/self.atr_period, adjust=False).mean()

        return atr.iloc[-1]

    def get_atr_and_target(self, current_price: float, cost_bps: float, atr_multiplier: float) -> tuple[float, float]:
        """
        Calculates the latest ATR and a corresponding price target.

        Args:
            current_price: The current price of the asset.
            cost_bps: The trading cost in basis points, used for break-even calculation.
            atr_multiplier: The factor to multiply the ATR by for the target.

        Returns:
            A tuple containing (price_target, atr_value).
        """
        df = self.price_fetcher.fetch()
        atr = self._calculate_atr(df)

        # Calculate the price displacement needed to cover costs
        cost_factor = cost_bps / 10000
        break_even_price = current_price * (1 + cost_factor)

        # The target is the break-even price plus a factor of the ATR
        price_target = break_even_price + (atr * atr_multiplier)

        # --- FIX: Corrected the return statement to include 'atr' ---
        return price_target, atr