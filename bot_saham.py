import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil daftar saham IHSG dari Wikipedia ===
daftar_saham = pd.read_html("https://id.wikipedia.org/wiki/Daftar_saham_IHSG")[0]
kode_saham = daftar_saham['Kode'].dropna().tolist()
kode_saham = [kode.strip().upper() + ".JK" for kode in kode_saham if isinstance(kode, str)]

hasil_sinyal = []

for kode in kode_saham:
    try:
        df = yf.download(kode, period='3mo', interval='1d', progress=False)
        if df.empty or len(df) < 21:
            continue

        close_series = df['Close']
        if len(close_series.shape) > 1:
            close_series = close_series.squeeze()

        df['MA5'] = SMAIndicator(close_series, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close_series, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close_series, window=14).rsi()
        macd = MACD(close_series)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]

        if last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
            continue

        # Cek sinyal
        macd_cross_buy = df['MACD'].iloc[-2] < df['Signal'].iloc[-2] and df['MACD'].iloc[-1] > df['Signal'].iloc[-1]
        macd_cross_sell = df['MACD'].iloc[-2] > df['Signal'].iloc[-2] and df['MACD'].iloc[-1] < df['Signal'].iloc[-1]

        buy = (
            (last['RSI'] < 30) or
            macd_cross_buy or
            (last['Close'] > last['MA5'] and last['Close'] > last['MA20'])
        )

        sell = (
            (last['RSI'] > 70) or
            macd_cross_sell or
            (last['Close'] < last['MA5'] and last['Close'] < last['MA20'])
        )

        if buy and not sell:
            hasil_sinyal.append(f"{kode.replace('.JK','')} → ✅ BUY")
        elif sell and not buy:
            hasil_sinyal.append(f"{kode.replace('.JK','')} → 🚨 SELL")

    except Exception as e:
        continue  # skip saham error

# === Kirim hasil ke Telegram ===
if hasil_sinyal:
    pesan = "📊 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = "🔍 Tidak ada sinyal kuat di saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan}
)
