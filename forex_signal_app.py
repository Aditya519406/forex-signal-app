import streamlit as st
import pandas as pd
import yfinance as yf

# ----- Signal Logic -----
def signal_generator(df):
    try:
        last = df.iloc[-1]
        ema50 = last["EMA50"]
        ema200 = last["EMA200"]
        rsi = last["RSI"]
        macd = last["MACD"]
        signal_line = last["Signal"]

        if pd.isna(ema50) or pd.isna(ema200) or pd.isna(rsi) or pd.isna(macd) or pd.isna(signal_line):
            return "⚠️ Invalid value in indicator", None, None

        if ema50 > ema200 and rsi < 30 and macd > signal_line:
            return "📈 Buy", last["Close"] * 0.99, last["Close"] * 1.02
        elif ema50 < ema200 and rsi > 70 and macd < signal_line:
            return "📉 Sell", last["Close"] * 1.01, last["Close"] * 0.98
        else:
            return "❓ No Clear Signal", None, None
    except Exception as e:
        return f"⚠️ Error: {str(e)}", None, None


# ----- Load and Prepare Data -----
@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, interval='1h', period='5d')
    if df.empty:
        return df

    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    required_cols = ['EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
    if all(col in df.columns for col in required_cols):
        df.dropna(subset=required_cols, inplace=True)

    return df

# ----- Streamlit UI -----
st.set_page_config(page_title="📊 Forex Signal Tool", layout="centered")
st.title("📈 Forex Signal Tool")

forex_pairs = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X",
    "USDCAD=X", "USDCHF=X", "NZDUSD=X", "USDINR=X"
]

symbol = st.selectbox("Select Forex Pair", forex_pairs)

if symbol:
    data = load_data(symbol)

    if data.empty:
        st.error("⚠️ Failed to load data. Check your symbol or internet connection.")
    else:
        st.subheader(f"Signal for {symbol}")
        signal, sl, tp = signal_generator(data)
        st.write(f"**Signal**: {signal}")
        if sl and tp:
            st.write(f"**Stop Loss (SL)**: {sl:.4f}")
            st.write(f"**Take Profit (TP)**: {tp:.4f}")
