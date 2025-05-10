import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
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

# ————————————————————
# Daftar ticker dan mapping ke CoinGecko
# ————————————————————

ticker_options = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"]
coingecko_map = {
    "BTC-USD": "bitcoin", "ETH-USD": "ethereum", "BNB-USD": "binancecoin",
    "SOL-USD": "solana", "XRP-USD": "ripple"
}

# ————————————————————
# Input pengguna
# ————————————————————

ticker_input = st.selectbox("Pilih simbol kripto:", ticker_options)
if not ticker_input:
    st.stop()

# ————————————————————
# Logika simulasi Monte Carlo
# ————————————————————

try:
    coin_id = coingecko_map[ticker_input]
    resp = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                        params={"vs_currency": "usd", "days": "365"})
    resp.raise_for_status()
    prices = resp.json()["prices"]
    dates = [datetime.fromtimestamp(p[0]/1000).date() for p in prices]
    closes = [p[1] for p in prices]

    df = pd.DataFrame({"Date": dates, "Close": closes}).set_index("Date")
    if len(df) < 2:
        st.warning("Data historis tidak mencukupi untuk simulasi.")
        st.stop()

    log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    mu, sigma = log_ret.mean(), log_ret.std()
    current_price = df["Close"].iloc[-2]
    harga_penutupan = format_angka_indonesia(current_price)
    st.write(f"**Harga penutupan {ticker_input} sehari sebelumnya: US${harga_penutupan}**")

    np.random.seed(42)

    for days in [3, 7, 30]:
        st.subheader(f"Proyeksi Harga Kripto {ticker_input} untuk {days} Hari ke Depan")
        sims = np.zeros((days, 100000))
        for i in range(100000):
            rw = np.random.normal(mu, sigma, days)
            sims[:, i] = current_price * np.exp(np.cumsum(rw))
        finals = sims[-1, :]

        bins = np.linspace(finals.min(), finals.max(), 10)
        counts, _ = np.histogram(finals, bins=bins)
        probs = counts / len(finals) * 100
        idx_sorted = np.argsort(probs)[::-1]

        table_html = "<table><thead><tr><th>Peluang</th><th>Rentang Harga (US$)</th></tr></thead><tbody>"
        for id_sort in idx_sorted[:3]:
            low = bins[id_sort]
            high = bins[id_sort+1] if id_sort+1 < len(bins) else bins[-1]
            table_html += f"<tr><td>{format_persen_indonesia(probs[id_sort])}</td><td>{format_angka_indonesia(low)} - {format_angka_indonesia(high)}</td></tr>"
        table_html += "</tbody></table>"

        st.markdown(table_html, unsafe_allow_html=True)

        # Grafik Scatter Plot (Sebaran Simulasi)
        scatter_fig = go.Figure()
        for i in range(100):
            scatter_fig.add_trace(go.Scatter(
                x=list(range(1, days + 1)),
                y=sims[:, i],
                mode="lines",
                line=dict(width=0.5, color="white"),
                showlegend=False
            ))

        scatter_fig.update_layout(
            title=f"Sebaran Simulasi Harga Kripto {ticker_input}",
            xaxis_title="Hari ke-",
            yaxis_title="Harga (US$)",
            template="plotly_dark",
            height=500,
            width=800
        )

        st.plotly_chart(scatter_fig)

        # Grafik Histogram Probabilitas
        hist_fig = go.Figure()
        hist_fig.add_trace(go.Bar(
            x=[f"{format_angka_indonesia(bins[i])} - {format_angka_indonesia(bins[i+1])}" for i in range(len(bins) - 1)],
            y=probs,
            marker=dict(color="white", line=dict(color="white", width=1)),
            hoverinfo="x+y"
        ))

        hist_fig.update_layout(
            title=f"Histogram Probabilitas Harga Kripto {ticker_input}",
            xaxis_title="Rentang Harga (US$)",
            yaxis_title="Peluang (%)",
            template="plotly_dark",
            height=500,
            width=800
        )

        st.plotly_chart(hist_fig)

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
