# ===========================================
# ✅ BOT SAHAM IHSG - FINAL GABUNG SEMUA FITUR
# ===========================================
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# ========== KONFIG TELEGRAM ==========
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# ========== FUNGSI MENGAMBIL DAFTAR SAHAM IHSG ==========
def ambil_saham_ihsg():
    url = "https://raw.githubusercontent.com/dhinosaurus/daftar-saham-ihsg/main/ihsg.csv"
    try:
        df = pd.read_csv(url)
        return df['Kode'].dropna().astype(str).tolist()
    except:
        return []

# ========== PROSES UTAMA ==========
result_sinyal = []
result_hampir = []
result_pantau = []
ringkasan_10 = []
saham_list = ambil_saham_ihsg()

for kode in saham_list:
    ticker = kode + ".JK"
    try:
        df = yf.download(ticker, period='3mo', interval='1d', progress=False)
        if df.empty or len(df) < 20:
            continue

        close_series = df['Close'].squeeze()
        df['MA5'] = SMAIndicator(close_series, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close_series, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close_series, window=14).rsi()
        macd = MACD(close_series)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
            continue

        macd_cross_buy = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        macd_cross_sell = prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']

        buy = (
            last['RSI'] < 30 or
            macd_cross_buy or
            (last['Close'] > last['MA5'] > last['MA20'])
        )
        sell = (
            last['RSI'] > 70 or
            macd_cross_sell or
            (last['Close'] < last['MA5'] < last['MA20'])
        )

        if buy and not sell:
            result_sinyal.append(f"{kode} → ✅ BUY")
        elif sell and not buy:
            result_sinyal.append(f"{kode} → 🚨 SELL")
        elif (last['Close'] > last['MA5']) and (last['RSI'] < 50):
            result_hampir.append(f"{kode} → 🔍 Hampir sinyal BUY")
        elif last['RSI'] < 60 and macd_cross_buy:
            result_pantau.append(f"{kode} → 👀 MACD & RSI menarik")

        # Tambahkan ringkasan 10 saham pertama
        if len(ringkasan_10) < 10:
            ringkasan_10.append(
                f"{kode}: Close={last['Close']:.0f}, MA5={last['MA5']:.0f}, RSI={last['RSI']:.1f}, MACD={last['MACD']:.2f}"
            )

    except:
        continue

# ========== FORMAT PESAN TELEGRAM ==========
message = ""
if result_sinyal:
    message += "\n\n📈 Sinyal Kuat Saham IHSG Hari Ini:\n" + "\n".join(result_sinyal[:10])
else:
    message += "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

if result_hampir:
    message += "\n\n📊 Hampir Sinyal BUY:\n" + "\n".join(result_hampir[:3])

if result_pantau:
    message += "\n\n👀 Saham Potensi Menarik:\n" + "\n".join(result_pantau[:5])

if ringkasan_10:
    message += "\n\n📋 Ringkasan 10 Saham:\n" + "\n".join(ringkasan_10)

# ========== KIRIM TELEGRAM ==========
requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)
