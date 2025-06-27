import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("📈 Forex Signal Tool")

# Define your forex pairs
forex_pairs = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/INR": "USDINR=X"
}

pair_name = st.selectbox("Select Forex Pair", list(forex_pairs.keys()))
symbol = forex_pairs[pair_name]

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="1mo", interval="1h")
    if df.empty or len(df) < 50:
        st.warning("⚠️ Not enough data downloaded to calculate indicators.")
        return pd.DataFrame()

    # EMA calculations
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # RSI calculation
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD and Signal line
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    expected_cols = ['EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
    if any(col not in df.columns for col in expected_cols):
        st.error("❌ Required indicators not calculated properly.")
        return pd.DataFrame()

    df.dropna(subset=expected_cols, inplace=True)
    return df

def signal_generator(df):
    try:
        last = df.iloc[-1]
        required = ['EMA50', 'EMA200', 'RSI', 'MACD', 'Signal']
        for col in required:
            value = last[col]
            if pd.isna(value) or isinstance(value, pd.Series):
                return f"⚠️ Invalid value in column: {col}", None, None

        ema_buy = last['EMA50'] > last['EMA200']
        rsi_buy = last['RSI'] < 30
        macd_buy = last['MACD'] > last['Signal']

        ema_sell = last['EMA50'] < last['EMA200']
        rsi_sell = last['RSI'] > 70
        macd_sell = last['MACD'] < last['Signal']

        if ema_buy and rsi_buy and macd_buy:
            return "🟢 Buy", df['Close'].iloc[-1] * 0.99, df['Close'].iloc[-1] * 1.02
        elif ema_sell and rsi_sell and macd_sell:
            return "🔴 Sell", df['Close'].iloc[-1] * 1.01, df['Close'].iloc[-1] * 0.98
        else:
            return "❓ No Clear Signal", None, None

    except Exception as e:
        return f"⚠️ Error: {str(e)}", None, None

data = load_data(symbol)

if data.empty:
    st.error("❌ Failed to load valid data for analysis.")
else:
    signal, sl, tp = signal_generator(data)

    st.subheader(f"Signal for {pair_name}: {signal}")
    if sl and tp:
        st.write(f"📍 Stop Loss: `{sl:.4f}`")
        st.write(f"🎯 Take Profit: `{tp:.4f}`")

    # Plot chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candlesticks'
    ))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='blue', width=1), name='EMA50'))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], line=dict(color='red', width=1), name='EMA200'))

    fig.update_layout(title=f'{pair_name} Price Chart with EMA50 and EMA200',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
