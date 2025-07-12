import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Telegram Configuration ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Daftar Saham IHSG (Hardcoded - 100 besar saham aktif, bisa diperbarui manual) ===
daftar_saham = [
    'ACES', 'ADRO', 'AKRA', 'ANTM', 'ASII', 'BBCA', 'BBNI', 'BBRI', 'BBTN', 'BMRI',
    'BRIS', 'BRPT', 'BSDE', 'CPIN', 'ELSA', 'EMTK', 'ERA', 'ERAA', 'EXCL', 'GGRM',
    'HRUM', 'ICBP', 'INCO', 'INDF', 'INDY', 'INKP', 'INTP', 'ITMG', 'JPFA', 'JSMR',
    'KLBF', 'MDKA', 'MEDC', 'MIKA', 'MPPA', 'PGAS', 'PTBA', 'PTPP', 'PWON', 'RAJA',
    'SCMA', 'SIDO', 'SMGR', 'SMRA', 'TBIG', 'TCPI', 'TINS', 'TKIM', 'TLKM', 'TOWR',
    'TPIA', 'UNTR', 'UNVR', 'WIKA', 'WSKT', 'WTON'
]

# === Analisis Sinyal ===
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

        # Deteksi sinyal teknikal
        macd_cross_buy = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        macd_cross_sell = prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']

        buy_signal = (
            (last['RSI'] < 30) or
            macd_cross_buy or
            (last['Close'] > last['MA5'] and last['Close'] > last['MA20'])
        )
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
    data={'chat_id': CHAT_ID, 'text': pesan}
)
