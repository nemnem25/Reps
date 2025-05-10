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
st.markdown(
    "_Simulasi berbasis data historis untuk memproyeksikan harga kripto selama beberapa hari ke depan, menggunakan metode Monte Carlo. Harga yang digunakan adalah harga penutupan selama 365 hari terakhir._",
    unsafe_allow_html=True
)

# —————————————————————————
# Daftar ticker dan mapping ke CoinGecko
# —————————————————————————

ticker_options = [
    "BTC-USD", "ETH-USD", "BNB-USD", "USDT-USD", "SOL-USD", "XRP-USD", "TON-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "SHIB-USD", "WETH-USD", "DOT-USD", "TRX-USD", "WBTC-USD", "LINK-USD",
    "MATIC-USD", "ICP-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "UNI-USD", "PEPE-USD", "LEO-USD",
    "DAI-USD", "APT-USD", "STETH-USD", "XLM-USD", "OKB-USD", "ETC-USD", "CRO-USD", "FIL-USD",
    "RNDR-USD", "ATOM-USD", "HBAR-USD", "KAS-USD", "IMX-USD", "TAO-USD", "VET-USD", "MNT-USD",
    "FET-USD", "LDO-USD", "TONCOIN-USD", "AR-USD", "INJ-USD", "GRT-USD", "BTCB-USD", "USDC-USD",
    "SUI-USD", "BGB-USD", "XTZ-USD", "MUBARAK-USD"
]

coingecko_map = {
    "BTC-USD":"bitcoin", "ETH-USD":"ethereum", "BNB-USD":"binancecoin", "USDT-USD":"tether", "SOL-USD":"solana",
    "XRP-USD":"ripple", "TON-USD":"toncoin", "DOGE-USD":"dogecoin", "ADA-USD":"cardano", "AVAX-USD":"avalanche-2",
    "SHIB-USD":"shiba-inu", "WETH-USD":"weth", "DOT-USD":"polkadot", "TRX-USD":"tron", "WBTC-USD":"wrapped-bitcoin",
    "LINK-USD":"chainlink", "MATIC-USD":"matic-network", "ICP-USD":"internet-computer", "LTC-USD":"litecoin",
    "BCH-USD":"bitcoin-cash", "NEAR-USD":"near", "UNI-USD":"uniswap", "PEPE-USD":"pepe", "LEO-USD":"leo-token",
    "DAI-USD":"dai", "APT-USD":"aptos", "STETH-USD":"staked-ether", "XLM-USD":"stellar", "OKB-USD":"okb",
    "ETC-USD":"ethereum-classic", "CRO-USD":"crypto-com-chain", "FIL-USD":"filecoin", "RNDR-USD":"render-token",
    "ATOM-USD":"cosmos", "HBAR-USD":"hedera-hashgraph", "KAS-USD":"kaspa", "IMX-USD":"immutable-x",
    "TAO-USD":"bittensor", "VET-USD":"vechain", "MNT-USD":"mantle", "FET-USD":"fetch-ai", "LDO-USD":"lido-dao",
    "TONCOIN-USD":"toncoin", "AR-USD":"arweave", "INJ-USD":"injective-protocol", "GRT-USD":"the-graph",
    "BTCB-USD":"bitcoin-bep2", "USDC-USD":"usd-coin", "SUI-USD":"sui", "BGB-USD":"bitget-token", "XTZ-USD":"tezos", "MUBARAK-USD":"mubarakcoin"
}

# ————————————————————
# Input pengguna
# ————————————————————

ticker_input = st.selectbox("Pilih simbol kripto:", ticker_options)
if not ticker_input:
    st.stop()

# ————————————————————
# Tampilkan Tabel Data Historis Kripto
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
    dates = [datetime.fromtimestamp(p[0] / 1000).strftime("%Y-%m-%d") for p in prices]
    closes = [p[1] for p in prices]

    df = pd.DataFrame({
        "Tanggal": dates,
        "Harga Penutupan": closes
    })

    st.subheader(f"Data Historis {ticker_input} (365 Hari Terakhir)")
    st.dataframe(df)

except Exception as e:
    st.error(f"Gagal memuat data historis: {e}")

# ————————————————————
# Logika Simulasi
# ————————————————————

try:
    # Logika simulasi menggunakan data historis
    log_ret = np.log(df["Harga Penutupan"] / df["Harga Penutupan"].shift(1)).dropna()
    mu, sigma = log_ret.mean(), log_ret.std()

    # Harga penutupan terakhir
    current_price = df["Harga Penutupan"].iloc[-1]

    # Kombinasi simbol kripto, tanggal, dan harga penutupan untuk random seed
    today = datetime.now().strftime("%Y-%m-%d")
    seed = hash((ticker_input, today, current_price)) % 2**32
    np.random.seed(seed)

    for days in [3, 7, 30, 90, 365]:
        st.subheader(f"Proyeksi Harga Kripto {ticker_input} untuk {days} Hari ke Depan")
        sims = np.zeros((days, 100000))
        for i in range(100000):
            rw = np.random.normal(mu, sigma, days)
            sims[:, i] = current_price * np.exp(np.cumsum(rw))

        final_prices = sims[-1, :]
        st.write(f"Rata-rata harga setelah {days} hari: ${format_angka_indonesia(np.mean(final_prices))}")

except Exception as e:
    st.error(f"Terjadi kesalahan dalam simulasi: {e}")
