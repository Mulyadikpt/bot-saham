import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil Data Saham ===
ticker = 'RAJA.JK'
df = yf.download(ticker, period='3mo', interval='1d')

# Pastikan data tidak kosong
if df.empty:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"⚠️ Data saham {ticker} tidak tersedia."}
    )
    exit()

# Hitung indikator teknikal
close_series = df['Close'].squeeze()
df['MA5'] = SMAIndicator(close_series, window=5).sma_indicator()
df['MA20'] = SMAIndicator(close_series, window=20).sma_indicator()
df['RSI'] = RSIIndicator(close_series, window=14).rsi()
macd = MACD(close_series)
df['MACD'] = macd.macd()
df['Signal'] = macd.macd_signal()

# Ambil data terakhir
last_row = df.iloc[-1]

# Cek validitas data
if last_row[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
    remark = "🔍 Tidak ada sinyal kuat (Netral) – Data belum cukup."
else:
    # Cek sinyal
    macd_cross_buy = df['MACD'].iloc[-2] < df['Signal'].iloc[-2] and df['MACD'].iloc[-1] > df['Signal'].iloc[-1]
    macd_cross_sell = df['MACD'].iloc[-2] > df['Signal'].iloc[-2] and df['MACD'].iloc[-1] < df['Signal'].iloc[-1]

    buy_signal = (
        (last_row['RSI'] < 30) or
        macd_cross_buy or
        (last_row['Close'] > last_row['MA5'] and last_row['Close'] > last_row['MA20'])
    )

    sell_signal = (
        (last_row['RSI'] > 70) or
        macd_cross_sell or
        (last_row['Close'] < last_row['MA5'] and last_row['Close'] < last_row['MA20'])
    )

    if buy_signal and not sell_signal:
        remark = "✅ Sinyal BUY terdeteksi untuk RAJA hari ini."
    elif sell_signal and not buy_signal:
        remark = "🚨 Sinyal SELL terdeteksi untuk RAJA hari ini."
    elif buy_signal and sell_signal:
        remark = "⚠️ Sinyal campuran (Buy & Sell bersamaan)"
    else:
        remark = "🔍 Tidak ada sinyal kuat (Netral)"

# Format pesan
message = f"""📊 Sinyal Otomatis RAJA

Close: {last_row['Close']:.2f}
MA5: {last_row['MA5']:.2f} | MA20: {last_row['MA20']:.2f}
RSI: {last_row['RSI']:.2f}
MACD: {last_row['MACD']:.2f} | Signal Line: {last_row['Signal']:.2f}

Sinyal:
{remark}
"""

# Kirim ke Telegram
requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': message}
)
