import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------
# Signal generator function
# -------------------------------
def signal_generator(df):
    required_cols = ['Close', 'EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
    for col in required_cols:
        if col not in df.columns or df[col].isna().any():
            return f"⚠️ Invalid or missing value in column: {col}", None, None

    last = df.iloc[-1]

    if (
        last['EMA50'] > last['EMA200'] and
        last['RSI'] < 70 and
        last['MACD'] > last['Signal']
    ):
        return "📈 Buy", last['Close'] * 0.98, last['Close'] * 1.02
    elif (
        last['EMA50'] < last['EMA200'] and
        last['RSI'] > 30 and
        last['MACD'] < last['Signal']
    ):
        return "📉 Sell", last['Close'] * 1.02, last['Close'] * 0.98
    else:
        return "⏸️ Hold", None, None

# -------------------------------
# Data loader and indicator calculator
# -------------------------------
@st.cache_data
def load_data(symbol):
    # Sample mock data - in real use, load from API or CSV
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=100)
    close_prices = np.cumsum(np.random.randn(100)) + 100
    df = pd.DataFrame({'Date': dates, 'Close': close_prices})
    df.set_index('Date', inplace=True)

    # Technical indicators
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    df.dropna(inplace=True)
    return df

# -------------------------------
# Streamlit app layout
# -------------------------------
st.set_page_config(page_title="Forex Signal App", layout="centered")
st.title("💹 Forex Signal Generator")

symbols = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/INR"]

for symbol in symbols:
    st.subheader(f"Signal for {symbol}")
    data = load_data(symbol)
    signal, sl, tp = signal_generator(data)
    st.write(f"**Signal:** {signal}")
    if sl and tp:
        st.write(f"**Stop Loss:** {round(sl, 2)}")
        st.write(f"**Take Profit:** {round(tp, 2)}")
    st.line_chart(data[['Close', 'EMA50', 'EMA200']])
    st.divider()
