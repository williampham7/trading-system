import ta
import numpy as np
from collections import deque
import numpy as np
import pandas as pd

def rsi(trade_prices, period = 14):
    if len(trade_prices) < period + 1:
        return None
    
    # Compute price changes
    deltas = np.diff(trade_prices)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Compute average gain and average loss using Wilder's smoothing
    avg_gain = np.mean(gains[:period])  # First average gain
    avg_loss = np.mean(losses[:period])  # First average loss

    # Apply smoothing for the rest
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    # Avoid division by zero
    if avg_loss == 0:
        return 100  # RSI = 100 if no losses

    # Compute RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def di_plus(trade_prices):
    if len(trade_prices) < 3:
        return -1 # need at least two prices
    
    # Compute price differences
    high_diff = trade_prices[1:] - trade_prices[:-1]
    low_diff = trade_prices[:-1] - trade_prices[1:]

    # Calculate +DM
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)

    # Compute True Range (TR)
    tr = np.abs(trade_prices[1:] - trade_prices[:-1])  # Simple TR for close-close method

    # Avoid division by zero
    tr_sum = np.sum(tr)
    if tr_sum == 0:
        return 0  # No movement

    # Compute DI+
    di_plus = (np.sum(plus_dm) / tr_sum) * 100
    return di_plus

def di_minus(trade_prices):
    if len(trade_prices) < 3:
        return -1 # need at least two prices
    
    # Compute price differences
    high_diff = trade_prices[1:] - trade_prices[:-1]
    low_diff = trade_prices[:-1] - trade_prices[1:]

    # Calculate -DM
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

    # Compute True Range (TR)
    tr = np.abs(trade_prices[1:] - trade_prices[:-1])  # Simple TR for close-close method

    # Avoid division by zero
    tr_sum = np.sum(tr)
    if tr_sum == 0:
        return 0  # No movement

    # Compute DI-
    di_minus = (np.sum(minus_dm) / tr_sum) * 100
    return di_minus

def macd(prices, macd_period):
    """
    Calculate and return the latest MACD value from a NumPy array of prices.

    :param prices: np.ndarray of closing prices.
    :return: Most recent MACD value or None if not enough data.
    """

    if prices.size < macd_period:  # Ensure enough data for MACD calculation
        return None 

    # Calculate MACD difference directly
    macd_values = ta.trend.macd_diff(pd.Series(prices))

    return macd_values.iloc[-1] if not np.isnan(macd_values.iloc[-1]) else None

