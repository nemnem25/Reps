import streamlit as st
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ----------------------------
# Fungsi untuk mendapatkan data historis dari CoinGecko
# ----------------------------
def fetch_historical_data(coin_id, currency="usd", days=365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency, "days": days}
    response = requests.get(url, params=params)
    response.raise_for_status()
    prices = response.json()["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
    df.set_index("date", inplace=True)
    df.drop(columns="timestamp", inplace=True)
    return df

# ----------------------------
# Analisis Fibonacci Retracement
# ----------------------------
def calculate_fibonacci(df):
    high = df["close"].max()
    low = df["close"].min()
    diff = high - low
    levels = {
        "0%": high,
        "23.6%": high - 0.236 * diff,
        "38.2%": high - 0.382 * diff,
        "50%": high - 0.5 * diff,
        "61.8%": high - 0.618 * diff,
        "100%": low
    }
    return levels

# ----------------------------
# Hitung RSI
# ----------------------------
def calculate_rsi(df, period=14):
    delta = df["close"].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ----------------------------
# Buat Grafik
# ----------------------------
def plot_analysis(df, fib_levels):
    plt.figure(figsize=(12, 6))

    # Plot harga penutupan
    plt.plot(df.index, df["close"], label="Close Price", color="blue")

    # Plot level Fibonacci
    for level_name, level_value in fib_levels.items():
        plt.axhline(level_value, linestyle="--", label=f"Fib {level_name}: {level_value:.2f}", alpha=0.7)

    plt.title("Fibonacci Retracement & Close Price")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid()
    st.pyplot(plt)

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("📊 Cryptocurrency Technical Analysis App")
st.markdown("Analyze cryptocurrency price trends with technical indicators like **Fibonacci Retracement** and **RSI**.")

# Input untuk memilih cryptocurrency
coin_id = st.selectbox(
    "Select Cryptocurrency:",
    options=["bitcoin", "ethereum", "dogecoin"],
    index=0
)

# Ambil data historis
st.write("Fetching historical data...")
try:
    df = fetch_historical_data(coin_id)
    st.success(f"Fetched {len(df)} days of historical data for {coin_id.capitalize()}!")
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

# Hitung Fibonacci Retracement
st.write("Calculating Fibonacci Retracement levels...")
fib_levels = calculate_fibonacci(df)

# Hitung RSI
st.write("Calculating RSI...")
df["RSI"] = calculate_rsi(df)

# Tampilkan data dan grafik
st.subheader("📈 Close Price Chart with Fibonacci Levels")
plot_analysis(df, fib_levels)

st.subheader("📊 RSI Indicator")
st.line_chart(df["RSI"])

# Tampilkan analisis dalam teks
st.subheader("📃 Analysis Report")
last_price = df["close"].iloc[-1]
last_rsi = df["RSI"].iloc[-1]
analysis = f"""
- **Last Close Price:** ${last_price:.2f}
- **RSI:** {last_rsi:.2f} ({'Overbought' if last_rsi > 70 else 'Oversold' if last_rsi < 30 else 'Neutral'})
"""
for level_name, level_value in fib_levels.items():
    analysis += f"\n- Fibonacci {level_name}: ${level_value:.2f}"
st.markdown(analysis)
