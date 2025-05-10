import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import pytz
import requests

# ————————————————————
# Utility formatting angka Indonesia 
# ————————————————————

def format_angka_indonesia(val) -> str:
    try:
        val = float(val)
    except (TypeError, ValueError):
        return str(val)
    if abs(val) < 1:
        s = f"{val:,.8f}"
    else:
        s = f"{val:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def format_persen_indonesia(val) -> str:
    try:
        val = float(val)
    except (TypeError, ValueError):
        return str(val)
    s = f"{val:.1f}"
    return s.replace(".", ",") + "%"

# ————————————————————
# Konfigurasi halaman Streamlit
# ————————————————————

st.set_page_config(page_title="Proyeksi Harga Kripto Metode Monte Carlo", layout="centered")

# Tampilkan waktu realtime di atas
wib = pytz.timezone("Asia/Jakarta")
waktu_sekarang = datetime.now(wib).strftime("%A, %d %B %Y")
st.markdown(f"""
<div style='background-color: #5B5B5B; padding: 8px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 16px;'>
⏰ {waktu_sekarang}
</div>
""", unsafe_allow_html=True)

st.title("Proyeksi Harga Kripto Metode Monte Carlo")

# —————————————————————————
# Daftar ticker dan mapping ke CoinGecko
# —————————————————————————

ticker_options = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "DOGE-USD"
]

coingecko_map = {
    "BTC-USD": "bitcoin", "ETH-USD": "ethereum", "BNB-USD": "binancecoin",
    "SOL-USD": "solana", "DOGE-USD": "dogecoin"
}

# ————————————————————
# Input pengguna
# ————————————————————

ticker_input = st.selectbox("Pilih simbol kripto:", ticker_options)
if not ticker_input:
    st.stop()

# ————————————————————
# Logika simulasi
# ————————————————————

try:
    # Ambil data historis dari CoinGecko
    coin_id = coingecko_map[ticker_input]
    resp = requests.get(
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": "365"}
    )
    resp.raise_for_status()
    prices = resp.json()["prices"]
    dates = [datetime.fromtimestamp(p[0] / 1000).date() for p in prices]
    closes = [p[1] for p in prices]

    df = pd.DataFrame({"Date": dates, "Close": closes}).set_index("Date")
    if len(df) < 2:
        st.warning("Data historis tidak mencukupi untuk simulasi.")
        st.stop()

    log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    mu, sigma = log_ret.mean(), log_ret.std()

    # Harga penutupan terakhir (dari hari sebelumnya, sesuai historis)
    current_price = df["Close"].iloc[-2]

    harga_penutupan = format_angka_indonesia(current_price)
    st.write(f"**Harga penutupan {ticker_input} sehari sebelumnya: US${harga_penutupan}**")

    # **Gunakan seed yang dinamis berdasarkan tanggal dan harga penutupan**
    today = datetime.now().strftime("%Y-%m-%d")
    seed = hash((today, current_price)) % 2**32  # Kombinasi tanggal dan harga penutupan
    np.random.seed(seed)

    # Simulasi Monte Carlo
    for days in [3, 7, 30, 90, 365]:
        st.subheader(f"Proyeksi Harga Kripto {ticker_input} untuk {days} Hari ke Depan")
        sims = np.zeros((days, 100000))
        for i in range(100000):
            rw = np.random.normal(mu, sigma, days)
            sims[:, i] = current_price * np.exp(np.cumsum(rw))
        finals = sims[-1, :]

        # Tampilkan hasil simulasi
        st.write(f"Hasil simulasi untuk {days} hari ke depan:")
        st.write(f"Rata-rata harga: US${format_angka_indonesia(np.mean(finals))}")
        st.write(f"Standar deviasi: US${format_angka_indonesia(np.std(finals))}")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
