import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Forex Signal App", layout="centered")

st.title("💹 Forex Signal App")
symbol = st.text_input("Enter Forex pair symbol (e.g., EURUSD=X):", "EURUSD=X")

@st.cache_data
def load_data(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1h")
        if df.empty:
            return pd.DataFrame()

        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['EMA200'] = df['Close'].ewm(span=200).mean()

        delta = df['Close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9).mean()

        df.dropna(inplace=True)
        return df

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()

def signal_generator(df):
    if df.empty or len(df) < 1:
        return "⚠️ Not enough data", None, None

    required_cols = ['Close', 'EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
    for col in required_cols:
        if col not in df.columns or df[col].isnull().all():
            return f"⚠️ Missing or invalid column: {col}", None, None

    try:
        last = df.iloc[-1]
        if (
            last['EMA50'] > last['EMA200'] and
            last['RSI'] < 70 and
            last['MACD'] > last['Signal']
        ):
            return "📈 Buy", round(last['Close'] * 0.98, 5), round(last['Close'] * 1.02, 5)

        elif (
            last['EMA50'] < last['EMA200'] and
            last['RSI'] > 30 and
            last['MACD'] < last['Signal']
        ):
            return "📉 Sell", round(last['Close'] * 1.02, 5), round(last['Close'] * 0.98, 5)

        else:
            return "⏸️ Hold", None, None

    except Exception as e:
        return f"⚠️ Error: {str(e)}", None, None

# Load data and generate signal
if symbol:
    with st.spinner("Loading data..."):
        data = load_data(symbol)
        signal, sl, tp = signal_generator(data)

    st.subheader(f"Signal for {symbol}")
    st.write(signal)

    if sl and tp:
        st.write(f"**Stop Loss:** {sl}")
        st.write(f"**Take Profit:** {tp}")
    st.line_chart(data['Close'] if not data.empty else pd.Series())
