
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

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
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA200'] = ta.ema(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    return pd.concat([df, macd], axis=1)

data = load_data(symbol)

def signal_generator(df):
    last = df.iloc[-1]
    if (
        last['RSI'] < 30 and
        last['EMA50'] > last['EMA200'] and
        last['MACD_12_26_9'] > last['MACDs_12_26_9']
    ):
        return "📈 Call (Buy)", round(last['Close'] - 0.002, 5), round(last['Close'] + 0.004, 5)
    elif (
        last['RSI'] > 70 and
        last['EMA50'] < last['EMA200'] and
        last['MACD_12_26_9'] < last['MACDs_12_26_9']
    ):
        return "📉 Put (Sell)", round(last['Close'] + 0.002, 5), round(last['Close'] - 0.004, 5)
    else:
        return "❓ No Clear Signal", None, None

signal, sl, tp = signal_generator(data)

st.subheader(f"Signal for {pair_name}: {signal}")
if sl and tp:
    st.write(f"📍 **Stop Loss:** {sl}")
    st.write(f"🎯 **Take Profit:** {tp}")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index, open=data['Open'], high=data['High'],
    low=data['Low'], close=data['Close'], name="Candlestick"
))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='blue', width=1), name="EMA50"))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], line=dict(color='orange', width=1), name="EMA200"))
fig.update_layout(title=f"{pair_name} Price Chart", xaxis_title="Time", yaxis_title="Price", height=600)
st.plotly_chart(fig, use_container_width=True)
