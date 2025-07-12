import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil daftar saham IHSG ===
def ambil_saham_ihsg():
    url = 'https://raw.githubusercontent.com/davidcesarino/idx-listed-companies/main/idx-listed.csv'
    df = pd.read_csv(url)
    return sorted(df['Kode'].dropna().unique())

saham_list = ambil_saham_ihsg()
hasil_sinyal = []

# === Loop semua saham IHSG ===
for kode in saham_list:
    ticker = kode + '.JK'
    try:
        df = yf.download(ticker, period='3mo', interval='1d', progress=False)

        if df.empty or len(df) < 30:
            continue

        df['MA5'] = SMAIndicator(df['Close'], window=5).sma_indicator()
        df['MA20'] = SMAIndicator(df['Close'], window=20).sma_indicator()
        df['RSI'] = RSIIndicator(df['Close']).rsi()
        macd = MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if pd.isnull(last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']]).any():
            continue

        # === Logika sinyal BUY ===
        macd_cross = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        harga_diatas_ma = last['Close'] > last['MA5'] and last['Close'] > last['MA20']
        rsi_oversold = last['RSI'] < 30

        if macd_cross or harga_diatas_ma or rsi_oversold:
            sinyal = f"{kode} → ✅ BUY\nClose: {last['Close']:.2f} | MA5: {last['MA5']:.2f} | MA20: {last['MA20']:.2f}\nRSI: {last['RSI']:.2f} | MACD: {last['MACD']:.2f} | Signal: {last['Signal']:.2f}"
            hasil_sinyal.append(sinyal)

    except Exception as e:
        print(f"Error {kode}: {e}")
        continue

# === Kirim ke Telegram ===
if hasil_sinyal:
    message = "📊 *Sinyal Otomatis IHSG (MACD/RSI/MA)*\n\n" + "\n\n".join(hasil_sinyal[:20])  # Batasi maksimal 20 saham
else:
    message = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
)
