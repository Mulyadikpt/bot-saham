import yfinance as yf
import pandas as pd
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# === Konfigurasi Telegram ===
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# === Daftar Saham IHSG (embed langsung agar aman) ===
daftar_saham = [
    'ACES', 'ADRO', 'AKRA', 'ANTM', 'ASII', 'BBCA', 'BBNI', 'BBRI', 'BBTN', 'BMRI',
    'BRIS', 'BRPT', 'BSDE', 'CPIN', 'EMTK', 'ERAA', 'EXCL', 'GGRM', 'HMSP', 'ICBP',
    'INCO', 'INDF', 'INKP', 'INTP', 'ITMG', 'JPFA', 'JSMR', 'KLBF', 'MDKA', 'MEDC',
    'MIKA', 'MPPA', 'PGAS', 'PTBA', 'PTPP', 'RAJA', 'SCMA', 'SMGR', 'SMRA', 'TBIG',
    'TINS', 'TKIM', 'TLKM', 'TOWR', 'TPIA', 'UNTR', 'UNVR', 'WIKA', 'WSKT', 'WTON'
]

# === Fungsi deteksi sinyal teknikal ===
def deteksi_sinyal(ticker):
    try:
        df = yf.download(f"{ticker}.JK", period='3mo', interval='1d', progress=False)
        if df.empty or len(df) < 20:
            return None

        close = df['Close'].squeeze()
        df['MA5'] = SMAIndicator(close, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if last[['MA5', 'MA20', 'RSI', 'MACD', 'Signal']].isnull().any():
            return None

        macd_cross_up = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        macd_cross_down = prev['MACD'] > prev['Signal'] and last['MACD'] < last['Signal']

        buy = (
            last['RSI'] < 30 or
            macd_cross_up or
            (last['Close'] > last['MA5'] and last['Close'] > last['MA20'])
        )

        sell = (
            last['RSI'] > 70 or
            macd_cross_down or
            (last['Close'] < last['MA5'] and last['Close'] < last['MA20'])
        )

        if buy and not sell:
            remark = f"{ticker} → ✅ BUY"
        elif sell and not buy:
            remark = f"{ticker} → 🚨 SELL"
        elif buy and sell:
            remark = f"{ticker} → ⚠️ Sinyal campuran"
        else:
            return None

        return remark
    except:
        return None

# === Proses semua saham IHSG ===
hasil_sinyal = []

for kode in daftar_saham:
    sinyal = deteksi_sinyal(kode)
    if sinyal:
        hasil_sinyal.append(sinyal)

# === Kirim hasil ke Telegram ===
if hasil_sinyal:
    pesan = "📈 Sinyal Kuat Saham IHSG Hari Ini:\n\n" + "\n".join(hasil_sinyal)
else:
    pesan = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": pesan}
)
