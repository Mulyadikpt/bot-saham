import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Telegram Configuration ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Get IHSG Stock List ===
url = "https://raw.githubusercontent.com/mrfdn/daftar-saham-ihsg/main/daftar_saham_ihsg.csv"
try:
    df_saham = pd.read_csv(url)
    daftar_saham = df_saham['Kode'].tolist()
except Exception as e:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"❌ Gagal mengambil daftar saham IHSG: {e}"}
    )
    exit()

# === Analyze All Stocks ===
hasil_sinyal = []

for kode in daftar_saham:
    ticker = kode + ".JK"
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 25:
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

        # === Sinyal BUY ===
        macd_cross_buy = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        buy_signal = (
            (last['RSI'] < 30) or
            macd_cross_buy or
            (last['Close'] > last['MA5'] and last['Close'] > last['MA20'])
        )

        # === Sinyal SELL ===
        macd_cross_sell = prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']
        sell_signal = (
            (last['RSI'] > 70) or
            macd_cross_sell or
            (last['Close'] < last['MA5'] and last['Close'] < last['MA20'])
        )

        if buy_signal and not sell_signal:
            hasil_sinyal.append(f"✅ BUY — {kode}")
        elif sell_signal and not buy_signal:
            hasil_sinyal.append(f"🚨 SELL — {kode}")

    except Exception as e:
        print(f"[ERROR] {kode}: {e}")
        continue

# === Kirim ke Telegram ===
if hasil_sinyal:
    pesan = "📈 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan}
)
