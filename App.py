import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ----------------------------
# Fungsi untuk mendapatkan data historis dari CoinGecko
# ----------------------------
def fetch_historical_data(coin_id, currency="usd", days=365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency, "days": days}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        prices = data["prices"]
        volumes = data["total_volumes"]

        df = pd.DataFrame(prices, columns=["timestamp", "close"])
        df["volume"] = pd.DataFrame(volumes)[1]
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
        df.set_index("date", inplace=True)
        df.drop(columns="timestamp", inplace=True)
        return df
    else:
        st.error("Failed to fetch data from CoinGecko API.")
        return None

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
# Hitung MACD
# ----------------------------
def calculate_macd(df):
    short_ema = df["close"].ewm(span=12, adjust=False).mean()
    long_ema = df["close"].ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# ----------------------------
# Hitung Bollinger Bands
# ----------------------------
def calculate_bollinger_bands(df, period=20):
    sma = df["close"].rolling(window=period).mean()
    std_dev = df["close"].rolling(window=period).std()
    upper_band = sma + (std_dev * 2)
    lower_band = sma - (std_dev * 2)
    return upper_band, sma, lower_band

# ----------------------------
# Buat Grafik dengan Semua Indikator
# ----------------------------
def plot_analysis(df, fib_levels, macd, macd_signal, bb_upper, bb_middle, bb_lower, ema_50, ema_100, ema_200):
    plt.figure(figsize=(14, 8))

    # Plot harga penutupan
    plt.plot(df.index, df["close"], label="Harga Penutupan", color="blue")

    # Plot level Fibonacci
    for level_name, level_value in fib_levels.items():
        plt.axhline(level_value, linestyle="--", label=f"Fib {level_name}: {level_value:.2f}", alpha=0.7)

    # Plot Bollinger Bands
    plt.plot(df.index, bb_upper, label="Bollinger Upper", color="orange", linestyle="--")
    plt.plot(df.index, bb_middle, label="Bollinger Middle", color="green", linestyle="--")
    plt.plot(df.index, bb_lower, label="Bollinger Lower", color="orange", linestyle="--")

    # Plot EMA
    plt.plot(df.index, ema_50, label="EMA 50", color="purple", linestyle="-")
    plt.plot(df.index, ema_100, label="EMA 100", color="brown", linestyle="-")
    plt.plot(df.index, ema_200, label="EMA 200", color="pink", linestyle="-")

    plt.title("Grafik Analisis Teknikal dengan Indikator")
    plt.xlabel("Tanggal")
    plt.ylabel("Harga (USD)")
    plt.legend()
    plt.grid()
    st.pyplot(plt)

    # Plot MACD
    plt.figure(figsize=(14, 4))
    plt.plot(df.index, macd, label="MACD", color="blue")
    plt.plot(df.index, macd_signal, label="MACD Signal", color="red")
    plt.axhline(0, color="black", linestyle="--", linewidth=0.5)
    plt.title("Indikator MACD")
    plt.legend()
    st.pyplot(plt)

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("📊 Aplikasi Analisis Teknikal Cryptocurrency")
st.markdown(
    "Analisis harga cryptocurrency menggunakan indikator teknikal seperti **Fibonacci Retracement**, **RSI**, **MACD**, **Bollinger Bands**, **EMA**, dan **Volume**."
)

# Input untuk memilih cryptocurrency
coin_id = st.selectbox(
    "Pilih Cryptocurrency:",
    options=["bitcoin", "ethereum", "dogecoin"],
    index=0
)

# Ambil data historis
st.write("Mengambil data historis...")
df = fetch_historical_data(coin_id)

if df is not None:
    st.success(f"Berhasil mengambil {len(df)} hari data historis untuk {coin_id.capitalize()}!")

    # Hitung semua indikator
    st.write("Menghitung indikator teknikal...")
    fib_levels = calculate_fibonacci(df)
    df["RSI"] = calculate_rsi(df)
    macd, macd_signal = calculate_macd(df)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df)
    ema_50 = df["close"].ewm(span=50, adjust=False).mean()
    ema_100 = df["close"].ewm(span=100, adjust=False).mean()
    ema_200 = df["close"].ewm(span=200, adjust=False).mean()

    # Tampilkan grafik
    st.subheader("📈 Grafik Harga dengan Indikator")
    plot_analysis(df, fib_levels, macd, macd_signal, bb_upper, bb_middle, bb_lower, ema_50, ema_100, ema_200)

    # Tampilkan analisis dalam teks
    st.subheader("📃 Laporan Analisis")
    last_price = df["close"].iloc[-1]
    last_volume = df["volume"].iloc[-1]
    last_rsi = df["RSI"].iloc[-1]
    last_macd = macd.iloc[-1]
    last_macd_signal = macd_signal.iloc[-1]

    analysis = f"""
    - **Harga Penutupan Terakhir:** ${last_price:.2f}
    - **Volume Terakhir:** {last_volume:,.0f}
    - **RSI:** {last_rsi:.2f} ({'Overbought' if last_rsi > 70 else 'Oversold' if last_rsi < 30 else 'Netral'})
    - **MACD:** {last_macd:.2f}
    - **MACD Signal:** {last_macd_signal:.2f}
    - **Bollinger Bands:** 
        - Upper: ${bb_upper.iloc[-1]:.2f}
        - Middle: ${bb_middle.iloc[-1]:.2f}
        - Lower: ${bb_lower.iloc[-1]:.2f}
    - **EMA 50:** ${ema_50.iloc[-1]:.2f}
    - **EMA 100:** ${ema_100.iloc[-1]:.2f}
    - **EMA 200:** ${ema_200.iloc[-1]:.2f}
    """
    st.markdown(analysis)

    # Narasi berbentuk berita
    st.subheader("📰 Narasi Analisis Teknikal")
    news = f"""
    Pada penutupan terakhir, harga {coin_id.capitalize()} berada di ${last_price:.2f} dengan volume perdagangan sebesar {last_volume:,.0f}. 
    Indikator RSI menunjukkan kondisi {'overbought' if last_rsi > 70 else 'oversold' if last_rsi < 30 else 'netral'}, sementara MACD berada pada level {last_macd:.2f} dengan sinyal di {last_macd_signal:.2f}, mengindikasikan {'tren bullish' if last_macd > last_macd_signal else 'tren bearish'}. 
    Bollinger Bands menunjukkan harga berada di {'atas' if last_price > bb_middle.iloc[-1] else 'bawah'} pita tengah, yang mencerminkan {'tekanan beli' if last_price > bb_middle.iloc[-1] else 'tekanan jual'}. 
    EMA 50 saat ini berada di ${ema_50.iloc[-1]:.2f}, sementara EMA 200 berada di ${ema_200.iloc[-1]:.2f}, mengindikasikan {'momentum positif' if ema_50.iloc[-1] > ema_200.iloc[-1] else 'momentum negatif'}. 
    Dengan volume yang {'meningkat' if last_volume > df['volume'].mean() else 'menurun'}, pasar menunjukkan {'potensi pergerakan signifikan' if last_volume > df['volume'].mean() else 'stabilitas relatif'}.
    """
    st.markdown(f"<div style='text-align: justify;'>{news}</div>", unsafe_allow_html=True)
