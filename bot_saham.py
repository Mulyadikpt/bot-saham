import yfinance as yf
import pandas as pd
import requests
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil daftar saham IHSG ===
url = "https://raw.githubusercontent.com/dhinosaurus/daftar-saham-ihsg/main/ihsg.csv"

try:
    df_saham = pd.read_csv(url)
    symbols = df_saham['Kode'].tolist()
except Exception as e:
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                  data={'chat_id': CHAT_ID, 'text': f"❌ Gagal mengambil daftar saham IHSG: {e}"})
    exit()

hasil_sinyal = []

for kode in symbols:
    ticker = kode + ".JK"
    try:
        data = yf.download(ticker, period="3mo", interval="1d")
        if data.empty:
            continue

        close = data['Close'].squeeze()

        # Indikator
        data['EMA5'] = EMAIndicator(close, window=5).ema_indicator()
        data['EMA20'] = EMAIndicator(close, window=20).ema_indicator()
        data['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        bb = BollingerBands(close)
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_lower'] = bb.bollinger_lband()

        last = data.iloc[-1]
        prev = data.iloc[-2]

        # Sinyal-sinyal
        ema_cross = last['EMA5'] > last['EMA20'] and prev['EMA5'] < prev['EMA20']
        rsi_oversold = last['RSI'] < 30
        macd_cross = prev['MACD'] < prev['MACD_signal'] and last['MACD'] > last['MACD_signal']
        breakout_bb = last['Close'] > last['BB_upper']

        sinyal = []
        if ema_cross: sinyal.append("📈 EMA Cross")
        if rsi_oversold: sinyal.append("🟢 RSI < 30")
        if macd_cross: sinyal.append("⚡ MACD Bullish")
        if breakout_bb: sinyal.append("💥 Breakout BB")

        if len(sinyal) >= 2:
            pesan = f"{kode} → ✅ Sinyal kuat:\n" + "\n".join(sinyal)
            hasil_sinyal.append(pesan)

    except Exception:
        continue

# Kirim hasil
if hasil_sinyal:
    final = "📊 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n\n".join(hasil_sinyal)
else:
    final = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
              data={'chat_id': CHAT_ID, 'text': final})
