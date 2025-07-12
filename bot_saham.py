import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Daftar Saham IHSG Manual (Bisa ditambah) ===
tickers = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'TLKM.JK', 'ASII.JK', 'UNVR.JK', 'RAJA.JK',
    'ANTM.JK', 'ADRO.JK', 'ICBP.JK', 'INDF.JK', 'PGAS.JK', 'MDKA.JK', 'PTBA.JK'
]

# === Fungsi Kirim Telegram ===
def send_telegram(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

# === Mulai Analisis ===
hasil = []
for kode in tickers:
    try:
        df = yf.download(kode, period='3mo', interval='1d', progress=False)
        if df.empty or len(df) < 20:
            continue

        close = df['Close'].squeeze()
        df['MA5'] = SMAIndicator(close, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Validasi data
        if last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
            continue

        # Deteksi sinyal
        macd_cross_up = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        macd_cross_down = prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']

        is_buy = (
            (last['RSI'] < 30) or
            macd_cross_up or
            (last['Close'] > last['MA5'] and last['Close'] > last['MA20'])
        )
        is_sell = (
            (last['RSI'] > 70) or
            macd_cross_down or
            (last['Close'] < last['MA5'] and last['Close'] < last['MA20'])
        )

        if is_buy and not is_sell:
            remark = f"{kode.replace('.JK','')} → ✅ BUY"
        elif is_sell and not is_buy:
            remark = f"{kode.replace('.JK','')} → 🚨 SELL"
        elif is_buy and is_sell:
            remark = f"{kode.replace('.JK','')} → ⚠️ Mixed Signal"
        else:
            continue  # tidak ada sinyal kuat

        hasil.append(remark)

    except Exception as e:
        print(f"{kode} error: {e}")
        continue

# === Kirim ke Telegram ===
if hasil:
    pesan = "📊 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil)
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

send_telegram(pesan)
