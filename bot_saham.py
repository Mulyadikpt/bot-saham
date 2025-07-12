import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Load daftar saham IHSG dari file lokal ===
try:
    df_saham = pd.read_csv('data/daftar_ihsg.csv')
    daftar_saham = df_saham['Kode'].tolist()
except Exception as e:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"❌ Gagal load daftar saham: {e}"}
    )
    exit()

hasil_sinyal = []

for kode in daftar_saham:
    try:
        ticker = kode + '.JK'
        df = yf.download(ticker, period='3mo', interval='1d')
        if df.empty or len(df) < 30:
            continue

        close = df['Close'].dropna()
        df['MA5'] = SMAIndicator(close, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        macd_buy = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        rsi_buy = last['RSI'] < 30
        ma_buy = last['Close'] > last['MA5'] and last['Close'] > last['MA20']

        buy_signal = (macd_buy or rsi_buy or ma_buy)

        if buy_signal:
            pesan = f"{kode} → ✅ BUY\nClose: {last['Close']:.2f}\nMA5: {last['MA5']:.2f} | MA20: {last['MA20']:.2f}\nRSI: {last['RSI']:.2f}\nMACD: {last['MACD']:.2f} | Signal: {last['Signal']:.2f}"
            hasil_sinyal.append(pesan)

    except Exception as err:
        print(f"Gagal memproses {kode}: {err}")
        continue

# === Kirim hasil ke Telegram ===
if hasil_sinyal:
    final = "📊 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n\n".join(hasil_sinyal)
else:
    final = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': final}
)
