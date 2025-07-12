# bot_saham.py
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

# ===== KONFIGURASI TELEGRAM =====
TOKEN = '8151140696:AAGQ2DsmV_xlHrUtp2wPYj-YU8yd60pQdEo'
CHAT_ID = '5998549138'

# ===== LIST SAHAM IHSG (Statis agar tidak error) =====
def ambil_saham_ihsg():
    return [
        'ACES','ADHI','ADRO','AGII','AKRA','ANTM','ASII','AUTO','BBCA','BBNI','BBRI','BBTN','BFIN','BMRI','BNGA','BRIS',
        'BSDE','BTPS','CPIN','DMAS','DOID','ELSA','EMTK','ERAA','EXCL','GGRM','HRUM','ICBP','INCO','INDF','INDY','INKP',
        'INTP','ITMG','JPFA','JSMR','KLBF','LPKR','LSIP','MAPI','MDKA','MEDC','MIKA','MNCN','PGAS','PTBA','PTPP','PWON',
        'RAJA','SIDO','SMGR','SMRA','TINS','TKIM','TLKM','TOWR','UNTR','UNVR','WIKA','WSKT','WTON'
    ]

# ===== AMBIL SINYAL SAHAM =====
def analisa_saham(kode):
    try:
        df = yf.download(kode + ".JK", period='3mo', interval='1d')
        if df.empty or len(df) < 20:
            return None

        df['Close'] = df['Close'].ffill()
        close = df['Close']
        df['MA5'] = SMAIndicator(close, window=5).sma_indicator()
        df['MA20'] = SMAIndicator(close, window=20).sma_indicator()
        df['RSI'] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if last[['MA5','MA20','RSI','MACD','Signal']].isnull().any():
            return None

        # ==== Sinyal Buy ==== #
        macd_cross_up = prev['MACD'] < prev['Signal'] and last['MACD'] > last['Signal']
        price_above_ma = last['Close'] > last['MA5'] and last['Close'] > last['MA20']
        rsi_ok = last['RSI'] < 30

        if macd_cross_up or price_above_ma or rsi_ok:
            remark = f"✅ BUY untuk {kode}"
        else:
            return None

        # ==== Format Pesan ==== #
        pesan = f"""📊 Sinyal Otomatis {kode}

Close: {last['Close']:.2f}
MA5: {last['MA5']:.2f} | MA20: {last['MA20']:.2f}
RSI: {last['RSI']:.2f}
MACD: {last['MACD']:.2f} | Signal: {last['Signal']:.2f}

Sinyal:
{remark}
"""
        return pesan
    except Exception as e:
        return None

# ===== PROSES UTAMA =====
saham_list = ambil_saham_ihsg()
hasil = []

for kode in saham_list:
    sinyal = analisa_saham(kode)
    if sinyal:
        hasil.append(sinyal)

# ===== KIRIM KE TELEGRAM =====
if hasil:
    pesan_final = "\n===============================\n".join(hasil)
else:
    pesan_final = "🔍 Tidak ada sinyal kuat di Saham IHSG hari ini."

requests.post(
    f'https://api.telegram.org/bot{TOKEN}/sendMessage',
    data={'chat_id': CHAT_ID, 'text': pesan_final[:4000]}  # Telegram limit
)
