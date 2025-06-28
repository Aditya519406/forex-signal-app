import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Title
st.title("📊 Forex Signal Generator")

# Sidebar - Select symbol
symbol = st.sidebar.selectbox("Choose a Forex pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"])

# Load and process data
@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="60d", interval="1h")
    
    if df.empty:
        return pd.DataFrame()  # Return empty df if no data
    
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    df.dropna(inplace=True)
    return df

# Signal generator
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

# Load data
data = load_data(symbol)

# Generate signal
signal, sl, tp = signal_generator(data)

# Display results
st.subheader(f"Signal for {symbol.replace('=X', '')}:")
st.write(signal)
if sl:
    st.write(f"Stop Loss: {sl}")
if tp:
    st.write(f"Take Profit: {tp}")

# Plot
if not data.empty:
    st.line_chart(data[['Close', 'EMA50', 'EMA200']])
