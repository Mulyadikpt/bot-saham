import yfinance as yf
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
import requests

# TOKEN & CHAT_ID Telegram (ganti dengan milikmu)
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# Daftar saham (LQ45 + contoh IHSG)
saham_list = ['BBRI.JK', 'TLKM.JK', 'ANTM.JK', 'RAJA.JK']

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': pesan}
    requests.post(url, data=data)

sinyal_kuat = []

for kode in saham_list:
    df = yf.download(kode, period='3mo', interval='1d', progress=False)
    if df.empty or len(df) < 20: continue
    df['MA5'] = SMAIndicator(df['Close'], 5).sma_indicator()
    df['MA20'] = SMAIndicator(df['Close'], 20).sma_indicator()
    df['RSI'] = RSIIndicator(df['Close'], 14).rsi()
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()

    last = df.iloc[-1]
    buy = (last['RSI'] < 30) or           (df['MACD'].iloc[-2] < df['Signal'].iloc[-2] and df['MACD'].iloc[-1] > df['Signal'].iloc[-1]) or           ((last['Close'] > last['MA5']) and (last['Close'] > last['MA20']))
    if buy:
        sinyal_kuat.append(f"{kode.replace('.JK','')} → ✅ BUY")

if sinyal_kuat:
    pesan = "📊 Sinyal Kuat Saham Hari Ini:\n\n" + "\n".join(sinyal_kuat)
else:
    pesan = "🔍 Tidak ada sinyal kuat hari ini."

kirim_telegram(pesan)
