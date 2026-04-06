import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="COMPS : VALUATION ANALYSER", layout="wide")

# --- Institutional Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; }
    .verdict-card { padding: 20px; border-radius: 8px; border: 1px solid #30363d; background-color: #161b22; margin-top: 10px; }
    .disclaimer-box { padding: 15px; border-radius: 5px; background-color: rgba(239, 85, 59, 0.1); border-left: 5px solid #EF553B; margin-bottom: 25px; }
    .stock-info-card { padding: 15px; border-radius: 8px; background-color: #1c2128; border: 1px solid #444c56; margin-bottom: 20px; }
    .stExpander { border: 1px solid #30363d !important; border-radius: 8px !important; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Global Universe (Expanded for Peer Discovery) ---
STOCK_UNIVERSES = {
    "Nifty 50": ['ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS',
                 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BRITANNIA.NS', 'CIPLA.NS',
                 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS',
                 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICICBANK.NS', 'ITC.NS',
                 'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LTIM.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS',
                 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SHRIRAMFIN.NS',
                 'SBIN.NS', 'SUNPHARMA.NS', 'TCS.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS',
                 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS'],
    "Nifty Next 50": ["ABB.NS", "ADANIENSOL.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", "AMBUJACEM.NS", "BAJAJHLDNG.NS",
                      "BANKBARODA.NS", "BOSCHLTD.NS", "CANBK.NS", "CGPOWER.NS", "CHOLAFIN.NS", "COLPAL.NS", "DABUR.NS",
                      "DLF.NS", "DMART.NS", "GAIL.NS", "GODREJCP.NS", "HAVELLS.NS", "HAL.NS", "HDFCAMC.NS",
                      "ICICIGI.NS", "ICICIPRULI.NS", "IOC.NS", "INDIGO.NS", "NAUKRI.NS", "JINDALSTEL.NS",
                      "JSWENERGY.NS", "LICI.NS", "MARICO.NS", "MOTHERSON.NS", "PIDILITIND.NS", "PFC.NS", "PNB.NS",
                      "RECLTD.NS", "SHREECEM.NS", "SIEMENS.NS", "TATAPOWER.NS", "TORNTPHARM.NS", "TVSMOTOR.NS",
                      "MCDOWELL-N.NS", "VBL.NS", "VEDL.NS", "ZYDUSLIFE.NS", "ZOMATO.NS"]
}

GLOBAL_UNIVERSE = sorted(list(set([t for sub in STOCK_UNIVERSES.values() for t in sub])))


@st.cache_data(ttl=86400)
def get_global_sector_map(universe):
    ind_map, sec_map, industry_lookup = {}, {}, {}
    for ticker in universe:
        try:
            info = yf.Ticker(ticker).info
            ind, sec = info.get('industry', 'Other'), info.get('sector', 'Other')
            ind_map.setdefault(ind, []).append(ticker)
            sec_map.setdefault(sec, []).append(ticker)
            industry_lookup[ticker] = ind
        except:
            continue
    return ind_map, sec_map, industry_lookup


def get_valuation_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or ('currentPrice' not in info and 'previousClose' not in info): return None

        # --- ROE Robust Extraction ---
        roe = info.get('returnOnEquity') or info.get('trailingReturnOnEquity') or info.get('forwardReturnOnEquity')

        # Fallback Math: ROE = Net Income / Equity
        if roe is None:
            try:
                ni = info.get('netIncomeToCommon') or info.get('netIncome')
                pb = info.get('priceToBook')
                mcap = info.get('marketCap')
                if ni and pb and mcap and pb != 0:
                    equity = mcap / pb
                    if equity != 0:
                        roe = ni / equity
            except:
                pass

        return {
            "Ticker": ticker, "Name": info.get('shortName', ticker),
            "Description": info.get('longBusinessSummary', "No description available."),
            "Price": info.get('currentPrice') or info.get('previousClose'),
            "P/E": info.get('forwardPE') or info.get('trailingPE'),
            "P/S": info.get('priceToSalesTrailing12Months') or info.get('priceToSales'),
            "P/B": info.get('priceToBook'),
            "DivYield": info.get('dividendYield', 0),
            "DivRate": info.get('trailingAnnualDividendRate', 0),
            "EV/EBITDA": info.get('enterpriseToEbitda'),
            "EV/Rev": info.get('enterpriseToRevenue'),
            "ROE": roe, "EPS": info.get('forwardEps') or info.get('trailingEps'),
            "BVPS": info.get('bookValue'), "RevenuePS": info.get('revenuePerShare'),
            "EBITDA": info.get('ebitda'), "TotalDebt": info.get('totalDebt'),
            "Cash": info.get('totalCash'), "Industry": info.get('industry', 'Other'),
            "Sector": info.get('sector', 'Other'), "Market Cap": info.get('marketCap'),
            "SharesOut": info.get('sharesOutstanding')
        }
    except:
        return None


# --- UI Header ---
st.title("🎯 COMPS : VALUATION ANALYSER")

st.markdown("""
<div class="disclaimer-box">
    <b>⚠️ CRITICAL LEGAL DISCLAIMER</b><br>
    • <b>RESEARCH ONLY:</b> Automated quantitative tool. NOT financial advice.<br>
    • <b>NO RECOMMENDATION:</b> Ratings are mathematical outputs. Not personalized advice.<br>
    • <b>CONSULT PROFESSIONALS:</b> Always consult registered advisors before making commitments.
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💡 Methodology", "🔍 Stock Screener"])

with tab1:
    st.subheader("Quantitative Methodology")
    st.markdown("""
    * **Step 1: Peer Matching:** The system matches stocks strictly by Industry tag and selects the **Top 5 closest competitors** by Market Cap. 
    * **Step 2: Multiple Benchmarking:** Pivots between models based on sector profile.
        * **Banking/Financials:** Valuation pivots to a **Triple-Anchor Model**: P/B (Inventory Value), P/E (Earnings Yield), and Div Yield (Income Floor).
        * **All Other Sectors:** Triangulates value using **P/E, P/S, EV/EBITDA, and EV/Revenue**.
    * **Step 3: Statistical Weighting:** Uses **'Inverse Variance'** logic to trust stable metrics more than volatile ones.
    * **Step 4: Quality Adjustment (QARP):** Applies premiums based on target **ROE vs sector median**.
    * **Step 5: Quant Alpha Signaling:** Indicates the statistical dislocation between the current price and its peer-implied worth.
    """)

with tab2:
    ind_map, sec_map, ind_lookup = get_global_sector_map(GLOBAL_UNIVERSE)
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        sel_universe = st.selectbox("1. Select Market Segment:", list(STOCK_UNIVERSES.keys()))
    with col_u2:
        selected_ticker = st.selectbox("2. Select Ticker for Analysis:",
                                       ["Select a Stock..."] + sorted(STOCK_UNIVERSES[sel_universe]))

    if selected_ticker != "Select a Stock...":
        with st.spinner(f"Compiling Institutional Comps..."):
            target = get_valuation_data(selected_ticker)
            if target:
                st.markdown(f"## {target['Name']} ({target['Ticker']})")
                st.markdown(
                    f"""<div class="stock-info-card"><b>Sector:</b> {target['Sector']} | <b>Industry:</b> {target['Industry']}<br><p style='font-size:0.95em; color:#adbac7; margin-top:10px;'>{target['Description'][:500]}...</p></div>""",
                    unsafe_allow_html=True)

                raw_peers = [t for t in ind_map.get(target['Industry'], []) if t != selected_ticker]
                peer_info = []
                for t in raw_peers:
                    try:
                        peer_info.append({'ticker': t, 'mcap': yf.Ticker(t).info.get('marketCap', 0)})
                    except:
                        continue
                peer_info.sort(key=lambda x: abs(x['mcap'] - (target['Market Cap'] or 0)))
                peer_tickers = [x['ticker'] for x in peer_info[:5]]
                peer_results = [get_valuation_data(p_t) for p_t in peer_tickers]
                df_peers = pd.DataFrame([p for p in peer_results if p])

                if not df_peers.empty:
                    is_fin = "Financial" in target['Sector'] or "Bank" in target['Industry']

                    if is_fin:
                        metrics = ['P/B', 'P/E', 'DivYield']
                    else:
                        metrics = ['P/E', 'P/S', 'EV/EBITDA', 'EV/Rev']

                    for m in metrics: df_peers[m] = df_peers[m].replace(0, np.nan)
                    stats_table = df_peers[metrics].describe(percentiles=[.25, .5, .75]).transpose()

                    weights, total_inv_var = {}, 0
                    for m in metrics:
                        cv = df_peers[m].std() / df_peers[m].mean() if df_peers[m].mean() else 1
                        inv_var = 1 / (cv ** 2) if cv != 0 else 0
                        weights[m] = inv_var
                        total_inv_var += inv_var
                    for m in metrics: weights[m] = weights[m] / total_inv_var if total_inv_var > 0 else (
                                1 / len(metrics))

                    debt, cash, shares = target['TotalDebt'] or 0, target['Cash'] or 0, target['SharesOut'] or 1
                    val_pe = (target['EPS'] * stats_table.loc['P/E', '50%']) if target['EPS'] else 0

                    if is_fin:
                        val_pb = (target['BVPS'] * stats_table.loc['P/B', '50%']) if target['BVPS'] else 0
                        med_yield = stats_table.loc['DivYield', '50%']
                        val_div = (target['DivRate'] / med_yield) if med_yield and med_yield > 0 else 0
                        implied_val = (val_pe * weights['P/E']) + (val_pb * weights['P/B']) + (
                                    val_div * weights['DivYield'])
                    else:
                        val_ps = (target['RevenuePS'] * stats_table.loc['P/S', '50%']) if target['RevenuePS'] else 0
                        val_ev_ebitda = ((target['EBITDA'] * stats_table.loc[
                            'EV/EBITDA', '50%']) - debt + cash) / shares if target['EBITDA'] and not np.isnan(
                            stats_table.loc['EV/EBITDA', '50%']) else 0
                        val_ev_rev = (((target['RevenuePS'] * shares) * stats_table.loc[
                            'EV/Rev', '50%']) - debt + cash) / shares if target['RevenuePS'] and not np.isnan(
                            stats_table.loc['EV/Rev', '50%']) else 0
                        implied_val = (val_pe * weights['P/E']) + (val_ps * weights['P/S']) + (
                                    val_ev_ebitda * weights['EV/EBITDA']) + (val_ev_rev * weights['EV/Rev'])

                    q_factor = 1 + (target['ROE'] - df_peers['ROE'].median()) if target.get('ROE') and not np.isnan(
                        df_peers['ROE'].median()) else 1.0
                    final_fair_value = implied_val * q_factor
                    upside = (final_fair_value / target['Price']) - 1 if target['Price'] > 0 else 0

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Market Price", f"₹{target['Price']:.2f}")
                    m2.metric("Weighted Fair Value", f"₹{final_fair_value:.2f}")
                    alpha_color = "#00CC96" if upside >= 0 else "#EF553B"
                    st.markdown(
                        f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(3) [data-testid='stMetricValue'] > div {{color: {alpha_color} !important;}}</style>",
                        unsafe_allow_html=True)
                    m3.metric("Quant Alpha", f"{upside:.1%}", delta=f"{upside:.1%}")

                    st.divider()

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader("Statistical Multiple Percentiles")
                        st.dataframe(stats_table[['25%', '50%', '75%', 'max']].rename(columns={'50%': 'Median (Fair)'}),
                                     use_container_width=True)

                        with st.expander("📖 How to Read This Table"):
                            st.markdown(f"""
                            This table shows how companies in the peer group are valued across key metrics like {', '.join(metrics)}. It helps you understand where a company stands compared to its competitors.

                            * **25% (Lower Range):** Represents the cheaper end of the market — companies priced lower than most peers. This may indicate undervaluation or weaker fundamentals.
                            * **Median (Fair Value):** The midpoint of all companies — this reflects the typical valuation the market assigns and is used as the primary benchmark for fair value.
                            * **75% (Premium Range):** Represents stronger companies that trade at higher valuations due to better growth, profitability, or competitive advantages.
                            * **Max (Extreme Value):** The highest observed valuation in the group — often an outlier, which may reflect exceptional performance or possible overvaluation.
                            """)

                    with c2:
                        st.subheader("Institutional Verdict")
                        v_color = "#00CC96" if upside > 0.1 else "#EF553B" if upside < -0.1 else "#8b949e"
                        v_text = "ACCUMULATE" if upside > 0.1 else "TRIM" if upside < -0.1 else "HOLD/NEUTRAL"
                        st.markdown(
                            f"""<div class="verdict-card"><h3 style='color:{v_color}'>{v_text}</h3><p>Target is trading at a <b>{abs(upside):.1%}</b> dislocation from fair value.</p></div>""",
                            unsafe_allow_html=True)

                    st.divider()
                    st.subheader("Full Comparable Table")
                    st.dataframe(df_peers[['Name'] + metrics + ['Market Cap', 'ROE']].style.format({
                        'P/E': '{:.1f}', 'P/B': '{:.2f}', 'P/S': '{:.1f}', 'EV/EBITDA': '{:.1f}', 'EV/Rev': '{:.2f}',
                        'DivYield': '{:.2%}', 'ROE': '{:.1%}', 'Market Cap': '{:,.0f}'
                    }, na_rep='N/A'), hide_index=True, use_container_width=True)
                else:
                    st.warning("Insufficient peer data found.")