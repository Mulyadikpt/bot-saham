import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
import datetime

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Ambil daftar saham IHSG dari GitHub CSV ===
url = "https://raw.githubusercontent.com/dhinosaurus/daftar-saham-ihsg/main/ihsg.csv"
try:
    df_saham = pd.read_csv(url)
    daftar_saham = df_saham['Kode'].tolist()
except Exception as e:
    requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': f"❌ Gagal mengambil daftar saham IHSG: {e}"}
    )
    exit()

# === Fungsi untuk cek sinyal saham ===
def analisa_sinyal(kode):
    try:
        data = yf.download(f"{kode}.JK", period="3mo", interval="1d", progress=False)
        if data.empty or len(data) < 30:
            return None

        close_series = data['Close'].squeeze()
        data['MA5'] = SMAIndicator(close_series, window=5).sma_indicator()
        data['MA20'] = SMAIndicator(close_series, window=20).sma_indicator()
        data['RSI'] = RSIIndicator(close_series, window=14).rsi()
        macd = MACD(close_series)
        data['MACD'] = macd.macd()
        data['Signal'] = macd.macd_signal()

        last = data.iloc[-1]
        prev = data.iloc[-2]

        sinyal = 0
        alasan = []

        if last['RSI'] < 30:
            sinyal += 1
            alasan.append("RSI<30")
        if last['Close'] > last['MA5'] and last['Close'] > last['MA20']:
            sinyal += 1
            alasan.append("MA Bullish")
        if prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']:
            sinyal += 1
            alasan.append("MACD Golden Cross")

        if sinyal > 0:
            return {
                'kode': kode,
                'sinyal': sinyal,
                'alasan': ', '.join(alasan),
                'harga': round(last['Close'], 2)
            }
    except:
        return None

# === Proses semua saham IHSG ===
hasil = []
for kode in daftar_saham:
    info = analisa_sinyal(kode)
    if info:
        hasil.append(info)

# === Urutkan dan ambil Top 10 ===
top_saham = sorted(hasil, key=lambda x: x['sinyal'], reverse=True)[:10]

# === Kirim hasil ke Telegram ===
if top_saham:
    pesan = "📊 Top 10 Sinyal Saham IHSG Hari Ini:\n\n"
    for i, saham in enumerate(top_saham, 1):
        pesan += f"{i}. {saham['kode']} → ✅ {saham['sinyal']} sinyal aktif ({saham['alasan']}) – Close: {saham['harga']}\n"
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan}
)
