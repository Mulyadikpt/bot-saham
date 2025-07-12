import yfinance as yf
import pandas as pd
import requests
import datetime as dt
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Waktu saat ini (UTC+7) ===
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
jam = now.hour
mode = 'After Close' if jam >= 17 else 'Live'

# === Ambil daftar saham IHSG dari GitHub ===
def ambil_saham_ihsg():
    url = 'https://raw.githubusercontent.com/davidcesarino/idx-listed-companies/main/idx-listed.csv'
    df = pd.read_csv(url)
    return sorted(df['Kode'].dropna().unique())

saham_list = ambil_saham_ihsg()
hasil_sinyal = []

# === Proses tiap saham ===
for kode in saham_list:
    ticker = kode + '.JK'
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

    macd_buy = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
    harga_above_ma = last['Close'] > last['MA5'] and last['Close'] > last['MA20']
    rsi_oversold = last['RSI'] < 30

    if macd_buy or harga_above_ma or rsi_oversold:
        hasil_sinyal.append(f"{kode} → ✅ BUY ({mode})")

# === Kirim ke Telegram ===
if hasil_sinyal:
    pesan = f"📊 *Sinyal {mode} IHSG ({now.strftime('%H:%M')} WIB)*\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = f"🔍 Tidak ada sinyal kuat ({mode}) di saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}
)
