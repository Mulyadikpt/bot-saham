import pandas as pd
import yfinance as yf
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil daftar saham IHSG dari file XLSX IDX ===
url_excel = "https://www.idx.co.id/media/daftar-saham.xlsx"
try:
    df_saham = pd.read_excel(url_excel)
    kode_saham = df_saham['Kode Saham'].dropna().astype(str).tolist()
except Exception as e:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"❌ Gagal ambil daftar saham dari IDX: {e}"}
    )
    exit()

# === Fungsi analisis satu saham ===
def analisa_saham(kode):
    ticker = kode + '.JK'
    try:
        data = yf.download(ticker, period='3mo', interval='1d', progress=False)
        if data.empty or len(data) < 21:
            return None

        close = data['Close']
        data['MA5'] = SMAIndicator(close, window=5).sma_indicator()
        data['MA20'] = SMAIndicator(close, window=20).sma_indicator()
        data['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()

        last = data.iloc[-1]
        prev = data.iloc[-2]

        if last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
            return None

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
            return f"{kode} → ✅ BUY"
        elif sell_signal and not buy_signal:
            return f"{kode} → 🚨 SELL"
        else:
            return None

    except Exception:
        return None

# === Proses semua saham IHSG ===
hasil_sinyal = []
for kode in kode_saham:
    hasil = analisa_saham(kode)
    if hasil:
        hasil_sinyal.append(hasil)

# === Format pesan Telegram ===
if hasil_sinyal:
    pesan = "📊 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

# === Kirim ke Telegram ===
requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan}
)
