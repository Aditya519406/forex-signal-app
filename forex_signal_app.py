import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ✅ Robust signal generator
def signal_generator(df):
    df = df.dropna()
    if df.empty:
        return "❓ Not enough data", None, None

    last = df.iloc[-1]
    required_cols = ['RSI', 'EMA50', 'EMA200', 'MACD', 'Signal', 'Close']

    for col in required_cols:
        if col not in df.columns or pd.isna(last[col]):
            return f"⚠️ Missing or NaN column: {col}", None, None

    if (
        last['RSI'] < 30 and
        last['EMA50'] > last['EMA200'] and
        last['MACD'] > last['Signal']
    ):
        return "📈 Call (Buy)", round(last['Close'] - 0.002, 5), round(last['Close'] + 0.004, 5)
    elif (
        last['RSI'] > 70 and
        last['EMA50'] < last['EMA200'] and
        last['MACD'] < last['Signal']
    ):
        return "📉 Put (Sell)", round(last['Close'] + 0.002, 5), round(last['Close'] - 0.004, 5)
    else:
        return "❓ No Clear Signal", None, None

# 🌐 Streamlit UI
st.set_page_config(page_title="Forex Signal Tool", layout="wide")
st.title("📈 Forex Signal Tool")

pairs = {
    "EUR/USD": "EURUSD=X",
    "USD/INR": "USDINR=X",
    "USD/JPY": "USDJPY=X"
}
pair_name = st.selectbox("Select Forex Pair", list(pairs.keys()))
symbol = pairs[pair_name]

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="1mo", interval="1h")
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

data = load_data(symbol)
signal, sl, tp = signal_generator(data)

st.subheader(f"Signal for {pair_name}: {signal}")
if sl and tp:
    st.write(f"📍 **Stop Loss:** {sl}")
    st.write(f"🎯 **Take Profit:** {tp}")

# 📊 Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index, open=data['Open'], high=data['High'],
    low=data['Low'], close=data['Close'], name="Candlestick"
))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='blue', width=1), name="EMA50"))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], line=dict(color='orange', width=1), name="EMA200"))
fig.update_layout(title=f"{pair_name} Price Chart", xaxis_title="Time", yaxis_title="Price", height=600)
st.plotly_chart(fig, use_container_width=True)
