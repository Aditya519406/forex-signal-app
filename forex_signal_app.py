import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period='3mo', interval='1h')

    if df.empty:
        st.warning("⚠️ No data returned for symbol.")
        return pd.DataFrame()

    # Calculate EMA
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # Calculate RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Calculate MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Ensure required columns exist before dropping
    required_cols = ['EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
    existing_cols = [col for col in required_cols if col in df.columns]
    if existing_cols:
        df.dropna(subset=existing_cols, inplace=True)

    return df
