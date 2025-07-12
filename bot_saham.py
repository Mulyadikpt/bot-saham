import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

try:
    url = "https://raw.githubusercontent.com/dhinosaurus/daftar-saham-ihsg/main/ihsg.csv"
    df_ihsg = pd.read_csv(url)
    daftar_saham = df_ihsg['Kode'].tolist()
except Exception as e:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"❌ Gagal mengambil daftar saham IHSG:\n{e}"}
    )
    exit()

hasil_sinyal = []

for kode in daftar_saham:
    ticker = f"{kode}.JK"
    try:
        df = yf.download(ticker, period='3mo', interval='1d', progress=False)
        if df.empty or len(df) < 25:
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

        macd_cross_up = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        rsi_low = last['RSI'] < 30
        price_above_ma = last['Close'] > last['MA5'] and last['Close'] > last['MA20']

        if macd_cross_up or rsi_low or price_above_ma:
            hasil_sinyal.append(f"{kode} → ✅ BUY")

    except Exception:
        continue

if hasil_sinyal:
    pesan = "📊 Sinyal BUY Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan}
)
