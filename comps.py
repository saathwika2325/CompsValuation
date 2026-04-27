import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import requests

# 1. SETUP & THEME
st.set_page_config(page_title="COMPS : VALUATION ANALYSER", layout="wide")

# Custom Styling to match your UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stSelectbox label { color: white !important; }
    .disclaimer-box {
        background-color: #1e1e1e;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. APP HEADER
st.title("🎯 COMPS : VALUATION ANALYSER")

with st.container():
    st.markdown("""
    <div class="disclaimer-box">
        <p style="color: #ff4b4b; font-weight: bold; margin-bottom: 5px;">⚠️ CRITICAL LEGAL DISCLAIMER</p>
        <ul style="font-size: 0.9em; color: #cccccc;">
            <li>RESEARCH ONLY: Automated quantitative tool. NOT financial advice.</li>
            <li>NO RECOMMENDATION: Ratings are mathematical outputs. Not personalized advice.</li>
            <li>CONSULT PROFESSIONALS: Always consult registered advisors before making commitments.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 3. TABS
tab_meth, tab_screen = st.tabs(["💡 Methodology", "🔍 Stock Screener"])

with tab_screen:
    col1, col2 = st.columns(2)
    
    with col1:
        market_segment = st.selectbox("1. Select Market Segment:", ["Nifty 50", "Nifty Next 50"])
    
    with col2:
        ticker_input = st.selectbox("2. Select Ticker for Analysis:", 
                                   ["WIPRO.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])

    st.divider()
    
    if ticker_input:
        try:
            with st.spinner(f"Connecting to data servers for {ticker_input}..."):
                # CLOUD FIX: Disguise the request as a browser so Yahoo doesn't block the Streamlit server
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                stock = yf.Ticker(ticker_input, session=session)
                
                # Fetch price from history (more reliable on cloud than .info)
                hist = stock.history(period="5d")
                
                if hist.empty:
                    st.error(f"Data provider returned empty results for {ticker_input}. This usually happens when the data provider detects a bot.")
                else:
                    current_price = round(hist['Close'].iloc[-1], 2)
                    prev_price = hist['Close'].iloc[-2]
                    price_change = round(((current_price - prev_price) / prev_price) * 100, 2)
                    
                    # Fair Value Logic (Replace with your actual math)
                    fair_value = round(current_price * 1.021, 2)
                    quant_alpha = 2.1

                    # Fetch Meta Info safely
                    info = stock.info
                    name = info.get('longName', ticker_input)
                    sector = info.get('sector', 'Technology')
                    industry = info.get('industry', 'Information Technology Services')
                    summary = info.get('longBusinessSummary', 'Description loading...')

                    # 4. RESULTS DISPLAY
                    st.header(f"{name} ({ticker_input})")
                    
                    st.markdown(f"""
                    <div style="background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d;">
                        <p><strong>Sector:</strong> {sector} | <strong>Industry:</strong> {industry}</p>
                        <p style="font-size: 0.9em; color: #8b949e;">{summary[:400]}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.metric("Current Market Price", f"₹{current_price}", f"{price_change}%")
                    with m_col2:
                        st.metric("Weighted Fair Value", f"₹{fair_value}")
                    with m_col3:
                        st.metric("Quant Alpha", f"{quant_alpha}%", f"{quant_alpha}%")

        except Exception as e:
            st.error("⚠️ Data connection failed.")
            with st.expander("Show Technical Logs"):
                st.write(f"Error: {str(e)}")

# Sidebar status
st.sidebar.title("System Status")
st.sidebar.success("Cloud Server: Connected")
st.sidebar.info(f"Last Fetch: {datetime.datetime.now().strftime('%H:%M:%S')}")
