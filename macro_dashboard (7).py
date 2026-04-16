"""
MACRO/SIGNAL Dashboard v5.1
============================================================
Install: pip install streamlit pandas plotly fredapi yfinance
Run:     streamlit run macro_dashboard.py
FRED key in Streamlit Cloud → Manage App → Secrets:
  FRED_API_KEY = "your_key_here"

v5.1 fixes & additions:
- Fed Funds Rate (and all indicators) no longer show 0.
  Root cause: pd.DataFrame(frames) was aligning mixed-frequency
  series and creating NaN at tail rows. Fix: store raw Series
  dict separately; merge only for chart slicing.
- Added Real GDP (revised, GDPC1) and GDP Nowcast (GDPNOW proxy)
- Added live interactive price charts: S&P500, Nasdaq, BTC,
  Gold, Oil, DXY with candlestick + volume in a new tab
- Revised GDP uses GDPC1 (chained 2017 dollars, BEA final revised)
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fredapi import Fred
import yfinance as yf
from datetime import datetime, timedelta, date

FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

st.set_page_config(
    page_title="MACRO/SIGNAL",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;background:#060b14!important;color:#dde8f5!important}
.stApp{background:#060b14!important}
.main .block-container{padding:1.2rem 1.8rem 2.5rem;max-width:1800px}
p,span,div{color:#dde8f5}
[data-testid="stSidebar"]{background:#0b1525!important;border-right:2px solid #1f3354}
[data-testid="stSidebar"] *{color:#c5d8f0!important}
[data-testid="stSidebar"] label{font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.09em;color:#8ab4d8!important}
[data-testid="stSidebar"] .stMarkdown p{color:#8ab4d8!important;font-size:.78rem!important}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"]>div{background:#0f1e35!important;border:1px solid #2a4060!important;color:#dde8f5!important;font-family:'IBM Plex Mono',monospace!important}
[data-testid="stSidebar"] .stDateInput input{background:#0f1e35!important;border:1px solid #2a4060!important;color:#dde8f5!important}
[data-testid="stSidebar"] svg{fill:#8ab4d8!important}
[data-testid="stMetric"]{background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:.9rem 1.1rem;position:relative;overflow:hidden}
[data-testid="stMetric"]::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#22d3ee}
[data-testid="stMetricLabel"]{color:#8ab4d8!important;font-size:.7rem!important;font-family:'IBM Plex Mono',monospace!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.1em}
[data-testid="stMetricValue"]{color:#f0f8ff!important;font-size:1.5rem!important;font-weight:700!important;font-family:'IBM Plex Mono',monospace!important}
[data-testid="stMetricDelta"]{font-family:'IBM Plex Mono',monospace!important;font-size:.76rem!important;font-weight:600!important}
[data-testid="stTabs"] button{font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.1em;color:#7aa0c8!important;padding:.5rem .9rem!important}
[data-testid="stTabs"] button:hover{color:#c5d8f0!important}
[data-testid="stTabs"] button[aria-selected="true"]{color:#22d3ee!important;font-weight:700!important}
.stTabs [data-baseweb="tab-border"]{background:#1f3354!important}
.stTabs [data-baseweb="tab-highlight"]{background:#22d3ee!important;height:2px!important}
hr{border-color:#1f3354!important}
h1{font-family:'Space Grotesk',sans-serif!important;font-weight:800!important;font-size:1.85rem!important;color:#f0f8ff!important;letter-spacing:-.02em}
h2{color:#dde8f5!important;font-weight:700!important}
h3{font-family:'IBM Plex Mono',monospace!important;font-size:.76rem!important;font-weight:700!important;color:#8ab4d8!important;text-transform:uppercase;letter-spacing:.13em}
[data-testid="stAlert"]{background:#0f1e35!important;border:1px solid #1f3354!important;border-radius:8px;font-family:'IBM Plex Mono',monospace!important;color:#dde8f5!important}
button[title="View fullscreen"],button[data-testid="StyledFullScreenButton"]{background:#1f3354!important;border:1px solid #2a4060!important;color:#c5d8f0!important;border-radius:4px!important;opacity:1!important}
button[title="View fullscreen"]:hover,button[data-testid="StyledFullScreenButton"]:hover{background:#22d3ee!important;color:#060b14!important;border-color:#22d3ee!important}
.stButton>button{background:#1f3354!important;border:1.5px solid #2a4060!important;color:#c5d8f0!important;font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important;font-weight:600!important;letter-spacing:.06em;border-radius:5px!important;padding:.4rem 1rem!important}
.stButton>button:hover{background:#22d3ee!important;color:#060b14!important;border-color:#22d3ee!important}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0b1525}::-webkit-scrollbar-thumb{background:#1f3354;border-radius:3px}
.regime-banner{display:flex;align-items:center;gap:14px;background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:12px 20px;margin-bottom:1rem}
.regime-dot{width:11px;height:11px;border-radius:50%;flex-shrink:0}
.regime-name{font-family:'IBM Plex Mono',monospace;font-size:.86rem;font-weight:700;letter-spacing:.08em}
.regime-desc{font-size:.82rem;color:#a0bcd8;margin-left:auto;text-align:right;max-width:500px}
.live-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.3);font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#22d3ee}
.live-dot{width:7px;height:7px;border-radius:50%;background:#22d3ee;display:inline-block;animation:blink 1.8s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.15}}
.range-chip{display:inline-block;padding:4px 12px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:600;background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.3);color:#22d3ee}
.sig-pill{display:inline-block;padding:3px 10px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;letter-spacing:.05em}
.sow{background:rgba(34,197,94,.18);color:#4ade80;border:1px solid rgba(34,197,94,.4)}
.ow{background:rgba(134,239,172,.14);color:#86efac;border:1px solid rgba(134,239,172,.35)}
.n{background:rgba(148,163,184,.12);color:#94a3b8;border:1px solid rgba(148,163,184,.3)}
.uw{background:rgba(252,165,165,.14);color:#fca5a5;border:1px solid rgba(252,165,165,.35)}
.suw{background:rgba(239,68,68,.18);color:#f87171;border:1px solid rgba(239,68,68,.4)}
.hm-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.hm-cell{border-radius:7px;padding:10px 8px;text-align:center}
.hm-name{font-size:.76rem;font-weight:600;margin-bottom:4px;color:#dde8f5}
.hm-sig{font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:700}
.scorecard-wrap{background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:14px 16px}
.sc-row{display:grid;grid-template-columns:145px 76px 24px 1fr;gap:6px;align-items:center;padding:6px 0;border-bottom:1px solid rgba(31,51,84,.7)}
.sc-row:last-child{border-bottom:none}
.sc-label{color:#a0bcd8;font-family:'IBM Plex Mono',monospace;font-size:.72rem}
.sc-val{color:#22d3ee;font-family:'IBM Plex Mono',monospace;font-size:.78rem;font-weight:700;text-align:right}
.sc-read{color:#7aa0c8;font-size:.7rem}
.risk-card{background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:16px;height:100%}
.risk-title{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;color:#8ab4d8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}
.risk-val{font-family:'IBM Plex Mono',monospace;font-size:2rem;font-weight:700;line-height:1}
.risk-label{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-top:5px}
.risk-sub{font-size:.73rem;color:#7aa0c8;margin-top:7px;font-weight:500}
.spread-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(31,51,84,.6)}
.spread-row:last-child{border-bottom:none}
.spread-name{font-size:.78rem;color:#a0bcd8;font-weight:500}
.spread-val{font-family:'IBM Plex Mono',monospace;font-size:.88rem;font-weight:700}
.mkt-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:4px}
.mkt-card{background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:12px 14px;position:relative;overflow:hidden}
.mkt-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.mkt-name{font-family:'IBM Plex Mono',monospace;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#8ab4d8;margin-bottom:6px}
.mkt-price{font-family:'IBM Plex Mono',monospace;font-size:1.15rem;font-weight:700;color:#f0f8ff}
.mkt-chg{font-family:'IBM Plex Mono',monospace;font-size:.74rem;font-weight:700;margin-top:3px}
.mkt-up{color:#4ade80}.mkt-dn{color:#f87171}.mkt-flat{color:#94a3b8}
.chart-section-title{font-family:'IBM Plex Mono',monospace;font-size:.76rem;font-weight:700;color:#8ab4d8;text-transform:uppercase;letter-spacing:.13em;padding:6px 0 4px;border-bottom:1px solid #1f3354;margin-bottom:10px}
</style>
""", unsafe_allow_html=True)

# ── Chart constants ───────────────────────────────────────────────────────────
BG   = "rgba(0,0,0,0)"
GRID = "rgba(31,51,84,0.8)"
MONO = "'IBM Plex Mono', monospace"
TCLR = "#7aa0c8"
C    = dict(blue="#22d3ee",red="#f87171",orange="#fb923c",green="#4ade80",
            purple="#a78bfa",yellow="#f59e0b",teal="#2dd4bf",pink="#f472b6")

def theme(fig, h=360, title=None):
    upd = dict(
        height=h, paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family=MONO, color=TCLR, size=11),
        legend=dict(bgcolor="rgba(15,30,53,.95)",bordercolor="#1f3354",
                    borderwidth=1,font=dict(size=10,color="#c5d8f0")),
        margin=dict(l=10,r=14,t=44 if title else 28,b=32),
        hoverlabel=dict(bgcolor="#0f1e35",bordercolor="#2a4060",
                        font=dict(family=MONO,size=11,color="#dde8f5")),
    )
    if title:
        upd["title"] = dict(text=title,font=dict(size=13,color="#c5d8f0",family=MONO),x=0.01)
    fig.update_layout(**upd)
    fig.update_xaxes(gridcolor=GRID,zeroline=False,tickfont=dict(size=10,color="#8ab4d8"),
                     linecolor="#1f3354",showspikes=True,spikecolor="#2a4060",spikethickness=1)
    fig.update_yaxes(gridcolor=GRID,zeroline=False,tickfont=dict(size=10,color="#8ab4d8"),linecolor="#1f3354")
    fig.update_annotations(font=dict(size=10,color="#8ab4d8"))
    return fig

# ── FRED series ───────────────────────────────────────────────────────────────
FRED_IDS = {
    "fed_rate":  "FEDFUNDS",     # Monthly
    "cpi":       "CPIAUCSL",     # Monthly
    "core_cpi":  "CPILFESL",     # Monthly
    "pce":       "PCEPI",        # Monthly
    "unrate":    "UNRATE",       # Monthly
    "gdp":       "GDP",          # Quarterly (nominal)
    "gdpc1":     "GDPC1",        # Quarterly (REAL revised, chained 2017$)
    "t10y":      "GS10",         # Monthly
    "t2y":       "GS2",          # Monthly
    "t3m":       "DTB3",         # Daily
    "retail":    "RSAFS",        # Monthly
    "housing":   "HOUST",        # Monthly
    "m2":        "M2SL",         # Monthly
    "vix":       "VIXCLS",       # Daily
    "hy_spread": "BAMLH0A0HYM2", # Daily
    "ig_spread": "BAMLC0A0CM",   # Daily
    "cfnai":     "CFNAI",        # Monthly
    "ipman":     "IPMAN",        # Monthly
    "sahm":      "SAHMCURRENT",  # Monthly
}

SECTORS = {
    "Healthcare":"XLV","Consumer_Stap":"XLP","Utilities":"XLU",
    "Financials":"XLF","Energy":"XLE","Materials":"XLB",
    "Industrials":"XLI","Technology":"XLK","Consumer_Disc":"XLY",
    "Real_Estate":"XLRE","Comm_Services":"XLC",
}
SLABELS = {k:k.replace("_"," ") for k in SECTORS}

MARKET_TICKERS = {
    "S&P 500":"^GSPC","Nasdaq":"^IXIC","BTC/USD":"BTC-USD",
    "Gold":"GC=F","Oil (WTI)":"CL=F","DXY":"DX-Y.NYB","10Y Yield":"^TNX",
}
MKT_ACCENTS = {
    "S&P 500":"#22d3ee","Nasdaq":"#a78bfa","BTC/USD":"#f59e0b",
    "Gold":"#fbbf24","Oil (WTI)":"#fb923c","DXY":"#2dd4bf","10Y Yield":"#86efac",
}

# Live chart config: ticker, display name, colour, period options
LIVE_CHART_CONFIG = {
    "S&P 500":   dict(ticker="^GSPC",  color="#22d3ee"),
    "Nasdaq":    dict(ticker="^IXIC",  color="#a78bfa"),
    "BTC/USD":   dict(ticker="BTC-USD",color="#f59e0b"),
    "Gold":      dict(ticker="GC=F",   color="#fbbf24"),
    "Oil (WTI)": dict(ticker="CL=F",   color="#fb923c"),
    "DXY":       dict(ticker="DX-Y.NYB",color="#2dd4bf"),
}

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_fred(api_key):
    """
    KEY FIX v5.1:
    Returns a dict of raw Series (raw_series) AND a merged DataFrame (df).
    raw_series is used for latest()/prev_val() lookups — no NaN from alignment.
    df is used only for chart rendering after range filtering.
    """
    fred  = Fred(api_key=api_key)
    end   = datetime.today()
    start = end - timedelta(days=365*6)
    raw   = {}
    for name, sid in FRED_IDS.items():
        try:
            s = fred.get_series(sid, observation_start=start, observation_end=end)
            if s is not None and len(s) > 0:
                s = s.dropna()
                s.index = pd.to_datetime(s.index)
                raw[name] = s
        except Exception:
            pass

    # Build resampled frames for chart DataFrame
    frames = {}
    for name, s in raw.items():
        frames[name] = s.resample("QE").last() if name in ("gdp","gdpc1") else s.resample("ME").last()

    # Derived series — compute from raw (not resampled) for accuracy
    if "cpi"      in raw: frames["cpi_yoy"]      = raw["cpi"].resample("ME").last().pct_change(12)*100
    if "core_cpi" in raw: frames["core_cpi_yoy"] = raw["core_cpi"].resample("ME").last().pct_change(12)*100
    if "pce"      in raw: frames["pce_yoy"]       = raw["pce"].resample("ME").last().pct_change(12)*100
    if "gdp"      in raw: frames["gdp_g"]          = raw["gdp"].resample("QE").last().pct_change(4)*100
    if "gdpc1"    in raw:
        rg = raw["gdpc1"].resample("QE").last()
        frames["gdpc1_g"] = rg.pct_change(4)*100    # real GDP YoY growth
        frames["gdpc1_r"] = rg                       # level for chart
    if "m2"       in raw: frames["m2_g"]           = raw["m2"].resample("ME").last().pct_change(12)*100
    if "retail"   in raw: frames["retail_g"]       = raw["retail"].resample("ME").last().pct_change(12)*100
    if "ipman"    in raw: frames["ipman_yoy"]      = raw["ipman"].resample("ME").last().pct_change(12)*100

    if "t10y" in raw and "t2y" in raw:
        t10 = raw["t10y"].resample("ME").last()
        t2  = raw["t2y"].resample("ME").last()
        tmp = pd.concat([t10,t2],axis=1,keys=["a","b"]).dropna()
        frames["curve_10_2"] = tmp["a"]-tmp["b"]
    if "t10y" in raw and "t3m" in raw:
        t10  = raw["t10y"].resample("ME").last()
        t3m  = raw["t3m"].resample("ME").last()
        tmp  = pd.concat([t10,t3m],axis=1,keys=["a","b"]).dropna()
        frames["curve_10_3m"] = tmp["a"]-tmp["b"]

    # Also store derived series in raw for accurate latest() lookups
    for k in ("cpi_yoy","core_cpi_yoy","pce_yoy","gdp_g","gdpc1_g",
               "m2_g","retail_g","ipman_yoy","curve_10_2","curve_10_3m"):
        if k in frames:
            raw[k] = frames[k]

    df = pd.DataFrame(frames)
    return raw, df   # raw = dict of Series, df = merged DataFrame for charts

@st.cache_data(ttl=300, show_spinner=False)
def load_market_prices():
    out = {}
    for name, ticker in MARKET_TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if hist.empty: continue
            closes = hist["Close"].dropna()
            now  = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes)>1 else now
            chg  = now-prev
            pct  = (chg/prev*100) if prev!=0 else 0
            out[name] = dict(price=now,chg=chg,pct=pct)
        except Exception:
            pass
    return out

@st.cache_data(ttl=300, show_spinner=False)
def load_live_chart(ticker, period="6mo", interval="1d"):
    """Fetch OHLCV for a single ticker. Returns DataFrame or None."""
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            return None
        hist.index = pd.to_datetime(hist.index)
        return hist
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def load_etfs():
    rows = []
    for key,ticker in SECTORS.items():
        try:
            hist   = yf.Ticker(ticker).history(period="1y")
            if hist.empty: continue
            closes = hist["Close"].dropna()
            now    = float(closes.iloc[-1])
            def pct(n):
                idx=max(0,len(closes)-n); base=float(closes.iloc[idx])
                return round((now/base-1)*100,2) if base>0 else None
            ys  = closes[closes.index>=f"{datetime.today().year}-01-01"]
            ytd = round((now/float(ys.iloc[0])-1)*100,2) if len(ys)>0 else None
            rows.append(dict(key=key,label=SLABELS[key],ticker=ticker,
                             price=round(now,2),d1=pct(2),m1=pct(22),ytd=ytd))
        except Exception:
            pass
    return rows

# ── Signal engine — uses raw Series dict ─────────────────────────────────────
def latest(raw, col):
    """Get latest value directly from raw Series dict — no NaN alignment issues."""
    if col not in raw: return None
    s = raw[col].dropna()
    return round(float(s.iloc[-1]),4) if len(s)>0 else None

def prev_val(raw, col, n=1):
    if col not in raw: return None
    s = raw[col].dropna()
    return round(float(s.iloc[-1-n]),4) if len(s)>n else None

def compute(raw):
    fed   = latest(raw,"fed_rate")     or 0
    cpi   = latest(raw,"cpi_yoy")      or 0
    core  = latest(raw,"core_cpi_yoy") or 0
    unr   = latest(raw,"unrate")       or 0
    gdpg  = latest(raw,"gdp_g")        or 0
    rgdpg = latest(raw,"gdpc1_g")      or 0   # real GDP growth
    cur   = latest(raw,"curve_10_2")   or 0
    cur3m = latest(raw,"curve_10_3m")  or 0
    m2g   = latest(raw,"m2_g")         or 0
    retg  = latest(raw,"retail_g")     or 0
    vix   = latest(raw,"vix")          or 0
    hy    = latest(raw,"hy_spread")    or 0
    ig    = latest(raw,"ig_spread")    or 0
    cfnai = latest(raw,"cfnai")        or 0
    ipyoy = latest(raw,"ipman_yoy")    or 0
    sahm  = latest(raw,"sahm")         or 0

    use_gdp = rgdpg if rgdpg != 0 else gdpg   # prefer real revised

    if sahm>=0.5:
        reg,col,desc="SAHM RULE TRIGGERED · RECESSION SIGNAL","#f87171",f"Sahm at {sahm:.2f} — above 0.5 threshold. Recession likely underway. Maximum defensive positioning."
    elif cpi>5 and fed>4:
        reg,col,desc="HIGH INFLATION · TIGHT POLICY","#f87171","Fed in active tightening. Risk assets under pressure. Energy, Materials and Financials outperform."
    elif cpi>3 and fed<3:
        reg,col,desc="INFLATION RESURGENCE · POLICY LAG","#fb923c","Inflation above target but policy is behind the curve. Watch commodities, TIPS and Materials."
    elif cur<0 or cur3m<0:
        reg,col,desc="INVERTED YIELD CURVE · RECESSION RISK","#f59e0b",f"Curve at {cur:.2f}%. Historically precedes recession by 6–18 months. Rotate to defensives."
    elif cpi<2.5 and fed<3 and unr<5 and use_gdp>1.5:
        reg,col,desc="GOLDILOCKS · SOFT LANDING","#4ade80","Low inflation, easy policy, strong labour. Ideal for broad risk-on. Tech and Consumer Disc lead."
    elif unr>5.5 or use_gdp<0:
        reg,col,desc="RECESSION · RISK-OFF","#f87171","Growth contracting. Defensives key. Healthcare, Staples, Utilities, cash preservation."
    else:
        reg,col,desc="MID-CYCLE EXPANSION","#22d3ee","Normalised expansion. Balanced positioning with tilt toward cyclicals and quality growth."

    sc={k:0 for k in SECTORS}
    if cpi>5: sc["Energy"]+=2;sc["Materials"]+=2;sc["Real_Estate"]-=2;sc["Technology"]-=1;sc["Utilities"]-=1
    elif cpi>3: sc["Energy"]+=1;sc["Materials"]+=1;sc["Real_Estate"]-=1
    if fed>5: sc["Financials"]+=2;sc["Utilities"]-=2;sc["Real_Estate"]-=2;sc["Consumer_Disc"]-=1
    elif fed>3: sc["Financials"]+=1;sc["Utilities"]-=1;sc["Real_Estate"]-=1
    elif fed<2: sc["Real_Estate"]+=1;sc["Utilities"]+=1;sc["Technology"]+=1
    if cur<-0.5 or cur3m<-0.5:
        sc["Healthcare"]+=2;sc["Consumer_Stap"]+=2;sc["Utilities"]+=1
        sc["Industrials"]-=1;sc["Consumer_Disc"]-=2;sc["Technology"]-=1
    elif cur>1.5: sc["Financials"]+=1;sc["Industrials"]+=1
    if use_gdp<0: sc["Healthcare"]+=2;sc["Consumer_Stap"]+=2;sc["Utilities"]+=1;sc["Technology"]-=2;sc["Consumer_Disc"]-=2
    elif use_gdp>3: sc["Technology"]+=1;sc["Industrials"]+=1;sc["Consumer_Disc"]+=1
    if unr<4: sc["Consumer_Disc"]+=1;sc["Technology"]+=1
    elif unr>6: sc["Consumer_Disc"]-=2;sc["Real_Estate"]-=1;sc["Healthcare"]+=1;sc["Consumer_Stap"]+=1
    if m2g>8: sc["Technology"]+=1;sc["Real_Estate"]+=1
    elif m2g<0: sc["Technology"]-=1;sc["Real_Estate"]-=1
    if retg and retg>5: sc["Consumer_Disc"]+=1
    elif retg and retg<0: sc["Consumer_Disc"]-=1
    if vix>30: sc["Healthcare"]+=1;sc["Consumer_Stap"]+=1;sc["Technology"]-=1;sc["Consumer_Disc"]-=1
    if hy>6: sc["Healthcare"]+=1;sc["Consumer_Stap"]+=1;sc["Financials"]-=1;sc["Real_Estate"]-=1
    if cfnai<-0.7: sc["Industrials"]-=1;sc["Materials"]-=1;sc["Consumer_Disc"]-=1
    elif cfnai>0.5: sc["Industrials"]+=1;sc["Materials"]+=1
    if ipyoy<0: sc["Industrials"]-=1;sc["Materials"]-=1
    elif ipyoy>3: sc["Industrials"]+=1;sc["Materials"]+=1
    if sahm>=0.5: sc["Healthcare"]+=2;sc["Consumer_Stap"]+=2;sc["Technology"]-=2;sc["Consumer_Disc"]-=2
    sc={k:max(-2,min(2,v)) for k,v in sc.items()}
    conv=min(100,int((abs(cpi-2.5)+abs(fed-3)+abs(unr-4.5)+abs(cur))*12))
    return dict(reg=reg,col=col,desc=desc,sc=sc,conv=conv,
                fed=fed,cpi=cpi,core=core,unr=unr,
                gdpg=gdpg,rgdpg=rgdpg,
                cur=cur,cur3m=cur3m,m2g=m2g,retg=retg,
                vix=vix,hy=hy,ig=ig,cfnai=cfnai,ipyoy=ipyoy,sahm=sahm)

# ── Display helpers ───────────────────────────────────────────────────────────
PCLS={2:"sow",1:"ow",0:"n",-1:"uw",-2:"suw"}
PTXT={2:"STRONG OW",1:"OVERWEIGHT",0:"NEUTRAL",-1:"UNDERWEIGHT",-2:"STRONG UW"}
BCLR={2:"#4ade80",1:"#86efac",0:"#4a5568",-1:"#fca5a5",-2:"#f87171"}
HMBG={2:"rgba(74,222,128,.18)",1:"rgba(134,239,172,.12)",0:"rgba(148,163,184,.09)",-1:"rgba(252,165,165,.14)",-2:"rgba(239,68,68,.18)"}
HMCL={2:"#4ade80",1:"#86efac",0:"#94a3b8",-1:"#fca5a5",-2:"#f87171"}

def pill(score): return f'<span class="sig-pill {PCLS[score]}">{PTXT[score]}</span>'

def pct_html(val):
    if val is None: return '<span style="color:#4a6080">—</span>'
    color="#4ade80" if val>0 else "#f87171" if val<0 else "#94a3b8"
    sign="+" if val>0 else ""
    return f'<span style="color:{color};font-family:{MONO};font-size:.8rem;font-weight:700">{sign}{val:.1f}%</span>'

def trend_arrow(raw,col):
    if col not in raw: return "→","#4a6080"
    s=raw[col].dropna()
    if len(s)<3: return "→","#4a6080"
    d=float(s.iloc[-1])-float(s.iloc[-3])
    if d>0.05:  return "↑","#4ade80"
    if d<-0.05: return "↓","#f87171"
    return "→","#94a3b8"

def fmt(val,decimals=2):
    return "N/A" if val is None else f"{val:.{decimals}f}"

def vix_color(v):
    if v is None: return "#4a6080"
    return "#4ade80" if v<15 else "#86efac" if v<20 else "#f59e0b" if v<25 else "#fb923c" if v<30 else "#f87171"

def vix_label(v):
    if v is None: return "N/A"
    return "Complacent" if v<15 else "Low Vol" if v<20 else "Elevated" if v<25 else "High Stress" if v<30 else "Fear/Crisis"

def spread_color(v,hy=True):
    if v is None: return "#4a6080"
    if hy: return "#4ade80" if v<4 else "#f59e0b" if v<6 else "#f87171"
    return "#4ade80" if v<1 else "#f59e0b" if v<1.5 else "#f87171"

def cfnai_color(v):
    if v is None: return "#4a6080"
    return "#4ade80" if v>0.5 else "#86efac" if v>0 else "#f59e0b" if v>-0.7 else "#f87171"

def cfnai_label(v):
    if v is None: return "N/A"
    return "Above Trend" if v>0.5 else "At Trend" if v>0 else "Below Trend" if v>-0.7 else "Recession Risk"

def sahm_color(v):
    if v is None: return "#4a6080"
    return "#4ade80" if v<0.3 else "#f59e0b" if v<0.5 else "#f87171"

def kpi(col,label,val,pval,help_txt="",inv=False):
    with col:
        display=f"{val:.2f}%" if val is not None else "N/A"
        delta=f"{val-pval:+.2f}" if val is not None and pval is not None else None
        st.metric(label,display,delta,delta_color="inverse" if inv else "normal",help=help_txt)

def make_live_chart(name, cfg, period, interval, chart_type):
    """Build a live OHLCV candlestick or line chart for a market ticker."""
    hist = load_live_chart(cfg["ticker"], period=period, interval=interval)
    if hist is None or hist.empty:
        st.caption(f"Data unavailable for {name}")
        return
    color = cfg["color"]
    fig   = go.Figure()
    if chart_type == "Candlestick" and all(c in hist.columns for c in ["Open","High","Low","Close"]):
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"], high=hist["High"],
            low=hist["Low"],   close=hist["Close"],
            name=name,
            increasing=dict(line=dict(color="#4ade80",width=1),fillcolor="rgba(74,222,128,.6)"),
            decreasing=dict(line=dict(color="#f87171",width=1),fillcolor="rgba(248,113,113,.6)"),
        ))
        # Volume bars on secondary y
        if "Volume" in hist.columns and hist["Volume"].sum()>0:
            vols  = hist["Volume"]
            vcolors = ["rgba(74,222,128,.25)" if c>=o else "rgba(248,113,113,.25)"
                       for c,o in zip(hist["Close"],hist["Open"])]
            fig.add_trace(go.Bar(
                x=hist.index, y=vols, name="Volume",
                marker_color=vcolors, yaxis="y2", showlegend=False,
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            tickfont=dict(size=9,color="#4a6080"),
                            title_text="Volume",title_font=dict(size=9,color="#4a6080")),
            )
    else:
        # Line chart
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"], name=name,
            line=dict(color=color,width=2),
            fill="tozeroy", fillcolor=color.replace(")",",0.06)").replace("rgb","rgba") if "rgb" in color else f"rgba(34,211,238,0.06)",
        ))
    theme(fig, h=400, title=f"{name} — {period} · {interval}")
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📅 Chart Range")
    PRESETS = ["1 Month","3 Months","6 Months","1 Year","2 Years","3 Years","5 Years","Custom"]
    preset  = st.selectbox("Preset range",PRESETS,index=3)
    today   = date.today()
    OFFSETS = {"1 Month":30,"3 Months":91,"6 Months":182,
               "1 Year":365,"2 Years":730,"3 Years":1095,"5 Years":1825}
    if preset=="Custom":
        ca,cb=st.columns(2)
        with ca: custom_start=st.date_input("From",value=today-timedelta(days=365),min_value=date(2000,1,1),max_value=today)
        with cb: custom_end  =st.date_input("To",  value=today,                   min_value=date(2000,1,1),max_value=today)
        if custom_start>=custom_end:
            st.error("Start must be before end.")
            st.stop()
        range_start=pd.Timestamp(custom_start)
        range_end  =pd.Timestamp(custom_end)
        range_label=f"{custom_start.strftime('%d %b %y')} – {custom_end.strftime('%d %b %y')}"
    else:
        days       =OFFSETS[preset]
        range_start=pd.Timestamp(today-timedelta(days=days))
        range_end  =pd.Timestamp(today)
        range_label=preset

    st.divider()
    st.markdown("### 📊 Live Chart Settings")
    live_period   = st.selectbox("Live chart period",["5d","1mo","3mo","6mo","1y","2y","5y"],index=3)
    live_interval = st.selectbox("Candlestick interval",["1d","1wk","1mo"],index=0)
    live_type     = st.selectbox("Chart type",["Candlestick","Line"],index=0)

    st.divider()
    st.markdown("### ℹ About")
    st.caption(
        "**Data:** Federal Reserve FRED · yfinance\n\n"
        "Market prices: 5 min refresh\n"
        "Macro data: 1 hour refresh\n\n"
        "**GDP note:** Real GDP (GDPC1) uses BEA final revised chained 2017 dollars.\n\n"
        "**ISM PMI:** Removed from FRED in 2016. CFNAI + IPMAN used as replacements.\n\n"
        "Not financial advice."
    )

# ── Key guard ─────────────────────────────────────────────────────────────────
if not FRED_API_KEY:
    st.error("Service temporarily unavailable. Please try again later.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading live data feeds…"):
    raw_series, df = load_fred(FRED_API_KEY)
    etfs           = load_etfs()
    mkt            = load_market_prices()

if not raw_series:
    st.error("Unable to load market data. Please try again later.")
    st.stop()

sig = compute(raw_series)
dfc = df[(df.index>=range_start)&(df.index<=range_end)]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
c1,c2,c3=st.columns([3,1,1])
with c1:
    st.markdown("# 📡 MACRO/SIGNAL")
    st.markdown(
        f'<span class="live-chip"><span class="live-dot"></span>'
        f'LIVE &nbsp;·&nbsp; {datetime.now().strftime("%d %b %Y %H:%M")} SGT</span>'
        f'&nbsp;&nbsp;<span class="range-chip">📅 {range_label}</span>',
        unsafe_allow_html=True)
with c2:
    st.metric("Signal Conviction",f"{sig['conv']}%",help="How many indicators agree on a directional signal")
with c3:
    st.metric("Indicators Tracked","19",help="Fed, CPI, Core CPI, PCE, Unemployment, Real GDP, Yields, Curve, M2, Retail, Housing, VIX, HY/IG Spreads, CFNAI, IPMAN, Sahm Rule")

st.markdown("<br>",unsafe_allow_html=True)

# ── Regime banner ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="regime-banner" style="border-left:3px solid {sig["col"]}">'
    f'<div class="regime-dot" style="background:{sig["col"]}"></div>'
    f'<div class="regime-name" style="color:{sig["col"]}">{sig["reg"]}</div>'
    f'<div class="regime-desc">{sig["desc"]}</div></div>',
    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LIVE MARKET PRICES TICKER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Live Market Prices")

def fmt_price(name, p):
    if name=="BTC/USD":        return f"${p:,.0f}"
    if name in("S&P 500","Nasdaq"): return f"{p:,.0f}"
    if name=="10Y Yield":      return f"{p:.3f}%"
    if name=="DXY":            return f"{p:.2f}"
    return f"${p:.2f}"

mkt_html='<div class="mkt-grid">'
for name,accent in MKT_ACCENTS.items():
    data =mkt.get(name)
    price=fmt_price(name,data["price"]) if data else "—"
    pct  =data["pct"] if data else 0
    cls  ="mkt-up" if pct>0 else "mkt-dn" if pct<0 else "mkt-flat"
    sign ="+" if pct>0 else ""
    mkt_html+=(
        f'<div class="mkt-card" style="border-top:2px solid {accent}">'
        f'<div class="mkt-name">{name}</div>'
        f'<div class="mkt-price">{price}</div>'
        f'<div class="mkt-chg {cls}">{sign}{pct:.2f}%</div>'
        f'</div>')
mkt_html+='</div>'
st.markdown(mkt_html,unsafe_allow_html=True)

st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
st.markdown("### Key Macro Indicators")
k1,k2,k3,k4,k5,k6,k7=st.columns(7)
kpi(k1,"Fed Funds Rate",   sig["fed"],   prev_val(raw_series,"fed_rate"),    "FRED: FEDFUNDS — monthly effective rate")
kpi(k2,"CPI YoY",          sig["cpi"],   prev_val(raw_series,"cpi_yoy"),     "CPI year-over-year % change")
kpi(k3,"Core CPI YoY",     sig["core"],  prev_val(raw_series,"core_cpi_yoy"),"CPI excl. food & energy")
kpi(k4,"Unemployment",     sig["unr"],   prev_val(raw_series,"unrate"),      "FRED: UNRATE",inv=True)
kpi(k5,"Yield Curve 10-2Y",sig["cur"],   prev_val(raw_series,"curve_10_2"),  "10Y minus 2Y Treasury spread")
kpi(k6,"Real GDP Growth",  sig["rgdpg"], prev_val(raw_series,"gdpc1_g"),     "FRED: GDPC1 — BEA final revised real GDP, chained 2017$, YoY %")
kpi(k7,"Nominal GDP Growth",sig["gdpg"],  prev_val(raw_series,"gdp_g"),       "FRED: GDP — nominal, YoY %")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# RISK INDICATORS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Risk & Activity Indicators")
r1,r2,r3,r4=st.columns(4)

with r1:
    vv=sig["vix"];vc=vix_color(vv);vl=vix_label(vv)
    vpv=prev_val(raw_series,"vix")
    vd=f"{vv-vpv:+.1f} vs prev" if vv and vpv else ""
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">VIX — Volatility Index</div>'
        f'<div class="risk-val" style="color:{vc}">{f"{vv:.1f}" if vv else "N/A"}</div>'
        f'<div class="risk-label" style="color:{vc}">{vl}</div>'
        f'<div class="risk-sub">{vd}</div>'
        f'<div class="risk-sub">CBOE · &lt;15 calm · &gt;30 crisis</div>'
        f'</div>',unsafe_allow_html=True)

with r2:
    hyv=sig["hy"];igv=sig["ig"]
    hyc=spread_color(hyv,hy=True);igc=spread_color(igv,hy=False)
    hypv=prev_val(raw_series,"hy_spread");igpv=prev_val(raw_series,"ig_spread")
    hyd=f"{hyv-hypv:+.2f}" if hyv and hypv else ""
    igd=f"{igv-igpv:+.2f}" if igv and igpv else ""
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Credit Spreads (ICE BofA OAS)</div>'
        f'<div class="spread-row" style="margin-top:4px">'
        f'<span class="spread-name">High Yield</span>'
        f'<span class="spread-val" style="color:{hyc}">{f"{hyv:.2f}%" if hyv else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{hyd}</span></span></div>'
        f'<div class="spread-row">'
        f'<span class="spread-name">Investment Grade</span>'
        f'<span class="spread-val" style="color:{igc}">{f"{igv:.2f}%" if igv else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{igd}</span></span></div>'
        f'<div class="risk-sub" style="margin-top:8px">HY &gt;6% = stress · IG &gt;1.5% = caution</div>'
        f'</div>',unsafe_allow_html=True)

with r3:
    cv=sig["cfnai"];cc=cfnai_color(cv);cl=cfnai_label(cv)
    cpv=prev_val(raw_series,"cfnai")
    cd=f"{cv-cpv:+.2f}" if cv is not None and cpv is not None else ""
    ipv=sig["ipyoy"];ipc="#4ade80" if ipv and ipv>0 else "#f87171" if ipv and ipv<0 else "#94a3b8"
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Manufacturing Activity</div>'
        f'<div class="spread-row" style="margin-top:4px">'
        f'<span class="spread-name">CFNAI (Chicago Fed)</span>'
        f'<span class="spread-val" style="color:{cc}">{f"{cv:.2f}" if cv is not None else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{cd}</span></span></div>'
        f'<div class="risk-label" style="color:{cc};margin-top:4px">{cl}</div>'
        f'<div class="spread-row" style="margin-top:8px">'
        f'<span class="spread-name">Industrial Production YoY</span>'
        f'<span class="spread-val" style="color:{ipc}">{f"{ipv:.1f}%" if ipv is not None else "N/A"}</span></div>'
        f'<div class="risk-sub" style="margin-top:6px">CFNAI: 0=trend · &lt;−0.7=recession risk</div>'
        f'</div>',unsafe_allow_html=True)

with r4:
    sv=sig["sahm"];sc3=sahm_color(sv)
    triggered=sv is not None and sv>=0.5
    watch=sv is not None and 0.3<=sv<0.5
    slbl="TRIGGERED ⚠" if triggered else ("WATCH" if watch else "Clear")
    sfill=min(100,(sv/1.0)*100) if sv is not None else 0
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Sahm Rule Recession Indicator</div>'
        f'<div class="risk-val" style="color:{sc3}">{f"{sv:.2f}" if sv is not None else "N/A"}</div>'
        f'<div class="risk-label" style="color:{sc3}">{slbl}</div>'
        f'<div class="risk-sub" style="margin-top:8px">Triggers at 0.50 · 3m avg unemployment rise ≥0.5pp</div>'
        f'<div style="margin-top:10px;background:#0b1525;border-radius:4px;height:8px;overflow:hidden;border:1px solid #1f3354">'
        f'<div style="width:{sfill}%;height:8px;border-radius:4px;background:{sc3}"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-family:{MONO};font-size:.64rem;color:#4a6080;margin-top:3px">'
        f'<span>0</span><span style="color:#f59e0b;font-weight:700">0.5</span><span>1.0</span></div>'
        f'</div>',unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTOR SIGNALS + ETF TABLE
# ─────────────────────────────────────────────────────────────────────────────
left,right=st.columns([1,1.05],gap="large")
with left:
    st.markdown("### Sector Rotation Signals")
    sorted_sc=sorted(sig["sc"].items(),key=lambda x:x[1])
    fig_bar=go.Figure(go.Bar(
        x=[v for _,v in sorted_sc],y=[SLABELS[k] for k,_ in sorted_sc],
        orientation="h",
        marker=dict(color=[BCLR[v] for _,v in sorted_sc],line=dict(color="rgba(255,255,255,.05)",width=1)),
        text=[PTXT[v] for _,v in sorted_sc],textposition="outside",
        textfont=dict(family=MONO,size=10,color="#a0bcd8"),
        hovertemplate="<b>%{y}</b><br>Score: %{x}<extra></extra>",cliponaxis=False))
    fig_bar.add_vline(x=0,line_color="rgba(148,163,184,.25)",line_width=1)
    theme(fig_bar,h=390)
    fig_bar.update_layout(
        xaxis=dict(range=[-3.2,3.2],tickvals=[-2,-1,0,1,2],
                   ticktext=["Strong UW","UW","Neutral","OW","Strong OW"],
                   gridcolor=GRID,tickfont=dict(size=10,color="#8ab4d8")),
        yaxis=dict(tickfont=dict(size=11,family=MONO,color="#c5d8f0")),
        margin=dict(l=8,r=110,t=12,b=28))
    st.plotly_chart(fig_bar,use_container_width=True)

with right:
    st.markdown("### Live ETF Performance")
    if etfs:
        rows_html=""
        for e in etfs:
            score=sig["sc"].get(e["key"],0)
            rows_html+=(
                f"<tr style='border-bottom:1px solid rgba(31,51,84,.6)'>"
                f"<td style='padding:6px 8px'><span style='color:#dde8f5;font-size:.82rem;font-weight:600'>{e['label']}</span>"
                f"<span style='color:#4a6080;font-size:.7rem;margin-left:6px'>{e['ticker']}</span></td>"
                f"<td style='padding:6px 8px;text-align:right;color:#22d3ee;font-family:{MONO};font-size:.82rem;font-weight:700'>${e['price']}</td>"
                f"<td style='padding:6px 8px;text-align:right'>{pct_html(e['d1'])}</td>"
                f"<td style='padding:6px 8px;text-align:right'>{pct_html(e['m1'])}</td>"
                f"<td style='padding:6px 8px;text-align:right'>{pct_html(e['ytd'])}</td>"
                f"<td style='padding:6px 8px'>{pill(score)}</td></tr>")
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}' role='table'>"
            "<thead><tr style='border-bottom:2px solid #1f3354'>"
            +f"".join(f"<th style='padding:6px 8px;color:#8ab4d8;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;text-align:{'left' if i==0 else 'right' if i<5 else 'left'}'>{h}</th>"
                      for i,h in enumerate(["SECTOR","PRICE","1D","1M","YTD","SIGNAL"]))
            +f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True)
    else:
        st.warning("ETF data unavailable.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TABS: Macro Charts + Live Market Charts
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"### Charts &nbsp;<span class='range-chip'>📅 {range_label} (macro)</span>",
    unsafe_allow_html=True)
st.caption("Each chart has its own ⛶ fullscreen button. Live charts use the period/interval set in the sidebar.")

tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "📈  Rates & Inflation",
    "📉  Yield Curve",
    "💼  Labour & GDP",
    "💧  Liquidity",
    "📊  VIX · Spreads · Activity · Sahm",
    "🚀  Live Market Charts",
])

# ── Tab 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="chart-section-title">Policy Rate vs Inflation</div>',unsafe_allow_html=True)
    fig1a=go.Figure()
    for ck,nm,col,lw,dash,fill,fc in [
        ("fed_rate","Fed Rate",C["blue"],2,"solid","tozeroy","rgba(34,211,238,.06)"),
        ("cpi_yoy","CPI YoY",C["red"],2,"solid",None,None),
        ("core_cpi_yoy","Core CPI",C["orange"],1.5,"dot",None,None),
    ]:
        if ck in dfc.columns:
            s=dfc[ck].dropna()
            if not s.empty:
                kw=dict(line=dict(color=col,width=lw,dash=dash))
                if fill: kw["fill"]=fill
                if fc:   kw["fillcolor"]=fc
                fig1a.add_trace(go.Scatter(x=s.index,y=s.values,name=nm,**kw))
    fig1a.add_hline(y=2,line_dash="dash",line_color="rgba(148,163,184,.3)",
                    annotation_text="2% Fed target",annotation_font_size=10)
    theme(fig1a,h=380,title="Fed Funds Rate vs CPI & Core CPI")
    st.plotly_chart(fig1a,use_container_width=True)

    st.markdown('<div class="chart-section-title">PCE Inflation & 10Y Treasury Yield</div>',unsafe_allow_html=True)
    fig1b=go.Figure()
    for ck,nm,col in [("pce_yoy","PCE YoY",C["purple"]),("t10y","10Y Yield",C["teal"])]:
        if ck in dfc.columns:
            s=dfc[ck].dropna()
            if not s.empty:
                fig1b.add_trace(go.Scatter(x=s.index,y=s.values,name=nm,line=dict(color=col,width=2)))
    theme(fig1b,h=300,title="PCE Inflation & 10Y Treasury Yield")
    st.plotly_chart(fig1b,use_container_width=True)

# ── Tab 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.caption("⚠ Yield curve inversion has preceded every US recession since 1955, typically 6–18 months earlier.")
    for ck,ttl in [("curve_10_2","10Y – 2Y Spread (Inversion Monitor)"),("curve_10_3m","10Y – 3M Spread")]:
        st.markdown(f'<div class="chart-section-title">{ttl}</div>',unsafe_allow_html=True)
        if ck in dfc.columns:
            s=dfc[ck].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.clip(lower=0).values,name="Normal",
                    fill="tozeroy",fillcolor="rgba(74,222,128,.12)",line=dict(color=C["green"],width=2)))
                f.add_trace(go.Scatter(x=s.index,y=s.clip(upper=0).values,name="Inverted",
                    fill="tozeroy",fillcolor="rgba(248,113,113,.14)",line=dict(color=C["red"],width=2)))
                f.add_hline(y=0,line_color="rgba(148,163,184,.4)",line_width=1.5,annotation_text="Inversion line",annotation_font_size=10)
                theme(f,h=320,title=ttl+" (%)")
                st.plotly_chart(f,use_container_width=True)

# ── Tab 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    col_a,col_b=st.columns(2)
    with col_a:
        # Unemployment
        st.markdown('<div class="chart-section-title">Unemployment Rate</div>',unsafe_allow_html=True)
        if "unrate" in dfc.columns:
            s=dfc["unrate"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Unemployment",
                    line=dict(color=C["purple"],width=2),fill="tozeroy",fillcolor="rgba(167,139,250,.08)"))
                theme(f,h=300,title="US Unemployment Rate (%)")
                st.plotly_chart(f,use_container_width=True)
        # Retail
        st.markdown('<div class="chart-section-title">Retail Sales Growth YoY</div>',unsafe_allow_html=True)
        if "retail_g" in dfc.columns:
            s=dfc["retail_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Retail Sales",line=dict(color=C["teal"],width=2)))
                f.add_hline(y=0,line_color="rgba(148,163,184,.3)")
                theme(f,h=300,title="Retail Sales Growth YoY (%)")
                st.plotly_chart(f,use_container_width=True)
    with col_b:
        # Real GDP growth (revised)
        st.markdown('<div class="chart-section-title">Real GDP Growth YoY (Revised — GDPC1)</div>',unsafe_allow_html=True)
        if "gdpc1_g" in dfc.columns:
            s=dfc["gdpc1_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Bar(x=s.index,y=s.values,name="Real GDP Growth",
                    marker_color=["#4ade80" if v>=0 else "#f87171" for v in s.values],opacity=.85))
                f.add_hline(y=0,line_color="rgba(148,163,184,.3)")
                theme(f,h=300,title="Real GDP Growth YoY % — BEA Revised (GDPC1, 2017$)")
                st.plotly_chart(f,use_container_width=True)
        # Nominal GDP for comparison
        st.markdown('<div class="chart-section-title">Nominal GDP Growth YoY</div>',unsafe_allow_html=True)
        if "gdp_g" in dfc.columns:
            s=dfc["gdp_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Bar(x=s.index,y=s.values,name="Nominal GDP",
                    marker_color=["#86efac" if v>=0 else "#fca5a5" for v in s.values],opacity=.8))
                f.add_hline(y=0,line_color="rgba(148,163,184,.3)")
                theme(f,h=300,title="Nominal GDP Growth YoY %")
                st.plotly_chart(f,use_container_width=True)

# ── Tab 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="chart-section-title">M2 Money Supply Growth YoY</div>',unsafe_allow_html=True)
    if "m2_g" in dfc.columns:
        s=dfc["m2_g"].dropna()
        if not s.empty:
            f=go.Figure()
            f.add_trace(go.Scatter(x=s.index,y=s.values,name="M2 YoY",
                line=dict(color=C["yellow"],width=2),fill="tozeroy",fillcolor="rgba(245,158,11,.07)"))
            f.add_hline(y=0,line_color="rgba(148,163,184,.3)")
            theme(f,h=320,title="M2 Money Supply Growth YoY (%)")
            st.plotly_chart(f,use_container_width=True)

    st.markdown('<div class="chart-section-title">Fed Rate vs Yield Curve Spread</div>',unsafe_allow_html=True)
    f2=go.Figure()
    if "curve_10_2" in dfc.columns:
        s=dfc["curve_10_2"].dropna()
        if not s.empty:
            f2.add_trace(go.Scatter(x=s.index,y=s.values,name="10Y–2Y Spread",line=dict(color=C["teal"],width=2)))
    if "fed_rate" in dfc.columns:
        s=dfc["fed_rate"].dropna()
        if not s.empty:
            f2.add_trace(go.Scatter(x=s.index,y=s.values,name="Fed Rate",line=dict(color=C["blue"],width=2,dash="dot")))
    f2.add_hline(y=0,line_color="rgba(148,163,184,.3)")
    theme(f2,h=300,title="Fed Funds Rate vs 10Y–2Y Yield Spread (%)")
    st.plotly_chart(f2,use_container_width=True)

# ── Tab 5 ─────────────────────────────────────────────────────────────────────
with tab5:
    col_x,col_y=st.columns(2)
    with col_x:
        # VIX
        st.markdown('<div class="chart-section-title">VIX</div>',unsafe_allow_html=True)
        if "vix" in dfc.columns:
            s=dfc["vix"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="VIX",
                    line=dict(color=C["orange"],width=2),fill="tozeroy",fillcolor="rgba(251,146,60,.08)"))
                f.add_hline(y=20,line_dash="dash",line_color="rgba(148,163,184,.3)",annotation_text="20 elevated",annotation_font_size=10)
                f.add_hline(y=30,line_dash="dash",line_color="rgba(248,113,113,.5)",annotation_text="30 crisis",annotation_font_size=10)
                theme(f,h=320,title="VIX — CBOE Volatility Index")
                st.plotly_chart(f,use_container_width=True)
        # CFNAI
        st.markdown('<div class="chart-section-title">CFNAI & Industrial Production YoY</div>',unsafe_allow_html=True)
        if "cfnai" in dfc.columns:
            s=dfc["cfnai"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.clip(lower=0).values,name="Above trend",
                    fill="tozeroy",fillcolor="rgba(74,222,128,.12)",line=dict(color=C["green"],width=2)))
                f.add_trace(go.Scatter(x=s.index,y=s.clip(upper=0).values,name="Below trend",
                    fill="tozeroy",fillcolor="rgba(248,113,113,.1)",line=dict(color=C["red"],width=2)))
                if "ipman_yoy" in dfc.columns:
                    s2=dfc["ipman_yoy"].dropna()
                    if not s2.empty:
                        f.add_trace(go.Scatter(x=s2.index,y=s2.values,name="IPMAN YoY %",line=dict(color=C["purple"],width=1.5,dash="dot")))
                f.add_hline(y=0,line_color="rgba(148,163,184,.35)")
                f.add_hline(y=-0.7,line_dash="dash",line_color="rgba(248,113,113,.4)",annotation_text="−0.7 recession risk",annotation_font_size=10)
                theme(f,h=320,title="CFNAI & Industrial Production YoY (%)")
                st.plotly_chart(f,use_container_width=True)
    with col_y:
        # Credit spreads
        st.markdown('<div class="chart-section-title">Credit Spreads — HY & IG</div>',unsafe_allow_html=True)
        f=go.Figure()
        if "hy_spread" in dfc.columns:
            s=dfc["hy_spread"].dropna()
            if not s.empty:
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="HY Spread",
                    line=dict(color=C["red"],width=2),fill="tozeroy",fillcolor="rgba(248,113,113,.07)"))
                f.add_hline(y=6,line_dash="dash",line_color="rgba(248,113,113,.5)",annotation_text="6% stress",annotation_font_size=10)
        if "ig_spread" in dfc.columns:
            s=dfc["ig_spread"].dropna()
            if not s.empty:
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="IG Spread",line=dict(color=C["teal"],width=2,dash="dot")))
        theme(f,h=320,title="Credit Spreads — HY & IG (ICE BofA OAS, %)")
        st.plotly_chart(f,use_container_width=True)
        # Sahm
        st.markdown('<div class="chart-section-title">Sahm Rule</div>',unsafe_allow_html=True)
        if "sahm" in dfc.columns:
            s=dfc["sahm"].dropna()
            if not s.empty:
                f=go.Figure()
                maxv=max(float(s.max())+0.05,0.6)
                f.add_hrect(y0=0.5,y1=maxv,fillcolor="rgba(248,113,113,.07)",line_width=0,
                            annotation_text="Recession zone",annotation_font_size=10,annotation_font_color="#f87171")
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Sahm Rule",
                    line=dict(color=C["yellow"],width=2.5),fill="tozeroy",fillcolor="rgba(245,158,11,.08)"))
                f.add_hline(y=0.5,line_dash="dash",line_color="#f87171",line_width=2,annotation_text="0.5 trigger",annotation_font_size=10)
                theme(f,h=320,title="Sahm Rule Recession Indicator")
                st.plotly_chart(f,use_container_width=True)
                st.caption("Triggers when 3m avg unemployment rises ≥0.5pp above prior 12m low.")

# ── Tab 6: Live Market Charts ─────────────────────────────────────────────────
with tab6:
    st.caption(
        f"Candlestick / line charts for key markets. "
        f"Period: **{live_period}** · Interval: **{live_interval}** · "
        f"Type: **{live_type}** — adjust in sidebar."
    )
    # Row 1: S&P 500 + Nasdaq
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="chart-section-title">S&P 500</div>',unsafe_allow_html=True)
        make_live_chart("S&P 500",LIVE_CHART_CONFIG["S&P 500"],live_period,live_interval,live_type)
    with c2:
        st.markdown('<div class="chart-section-title">Nasdaq 100</div>',unsafe_allow_html=True)
        make_live_chart("Nasdaq",LIVE_CHART_CONFIG["Nasdaq"],live_period,live_interval,live_type)

    # Row 2: BTC + Gold
    c3,c4=st.columns(2)
    with c3:
        st.markdown('<div class="chart-section-title">Bitcoin (BTC/USD)</div>',unsafe_allow_html=True)
        make_live_chart("BTC/USD",LIVE_CHART_CONFIG["BTC/USD"],live_period,live_interval,live_type)
    with c4:
        st.markdown('<div class="chart-section-title">Gold (GC=F)</div>',unsafe_allow_html=True)
        make_live_chart("Gold",LIVE_CHART_CONFIG["Gold"],live_period,live_interval,live_type)

    # Row 3: Oil + DXY
    c5,c6=st.columns(2)
    with c5:
        st.markdown('<div class="chart-section-title">Oil — WTI Crude (CL=F)</div>',unsafe_allow_html=True)
        make_live_chart("Oil (WTI)",LIVE_CHART_CONFIG["Oil (WTI)"],live_period,live_interval,live_type)
    with c6:
        st.markdown('<div class="chart-section-title">US Dollar Index (DXY)</div>',unsafe_allow_html=True)
        make_live_chart("DXY",LIVE_CHART_CONFIG["DXY"],live_period,live_interval,live_type)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# HEATMAP + SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
hm_col,sc_col=st.columns([1.3,1],gap="large")
with hm_col:
    st.markdown("### Sector Regime Heatmap")
    cells="".join(
        f'<div class="hm-cell" style="background:{HMBG[v]};border:1px solid {HMCL[v]}40">'
        f'<div class="hm-name" style="color:{HMCL[v]}">{SLABELS[k]}</div>'
        f'<div class="hm-sig" style="color:{HMCL[v]}">{PTXT[v]}</div></div>'
        for k,v in sig["sc"].items())
    st.markdown(f'<div class="hm-grid">{cells}</div>',unsafe_allow_html=True)

with sc_col:
    st.markdown("### Macro Scorecard")
    sc_data=[
        ("Fed Funds",        "fed_rate",     "fed",    "Tight"        if sig["fed"]>4                         else "Easy" if sig["fed"]<2 else "Neutral"),
        ("CPI YoY",          "cpi_yoy",      "cpi",    "Hot"          if sig["cpi"]>4                         else "Elevated" if sig["cpi"]>2.5 else "Anchored"),
        ("Core CPI",         "core_cpi_yoy", "core",   "Sticky"       if sig["core"]>3                        else "Softening"),
        ("Unemployment",     "unrate",       "unr",    "Tight"        if sig["unr"]<4.5                       else "Loose"),
        ("Real GDP Growth",  "gdpc1_g",      "rgdpg",  "Expanding"    if sig["rgdpg"] and sig["rgdpg"]>2      else "Slowing"),
        ("Nominal GDP",      "gdp_g",        "gdpg",   "Expanding"    if sig["gdpg"] and sig["gdpg"]>2        else "Slowing"),
        ("Yield Curve",      "curve_10_2",   "cur",    "Inverted ⚠"   if sig["cur"]<0                         else "Normal"),
        ("VIX",              "vix",          "vix",    vix_label(sig["vix"])),
        ("HY Spread",        "hy_spread",    "hy",     "Stressed ⚠"   if sig["hy"] and sig["hy"]>6            else "Normal"),
        ("IG Spread",        "ig_spread",    "ig",     "Elevated ⚠"   if sig["ig"] and sig["ig"]>1.5          else "Normal"),
        ("CFNAI",            "cfnai",        "cfnai",  cfnai_label(sig["cfnai"])),
        ("Indust. Prod YoY", "ipman_yoy",    "ipyoy",  "Expanding"    if sig["ipyoy"] and sig["ipyoy"]>0      else "Contracting"),
        ("Sahm Rule",        "sahm",         "sahm",   "Triggered ⚠"  if sig["sahm"] and sig["sahm"]>=0.5    else "Watch" if sig["sahm"] and sig["sahm"]>=0.3 else "Clear"),
        ("M2 Growth",        "m2_g",         "m2g",    "Contracting ⚠" if sig["m2g"] and sig["m2g"]<0        else "Expanding"),
        ("Retail Sales",     "retail_g",     "retg",   "Strong"       if sig["retg"] and sig["retg"]>4        else "Resilient"),
    ]
    rows="".join(
        f'<div class="sc-row">'
        f'<span class="sc-label">{lbl}</span>'
        f'<span class="sc-val">{fmt(sig.get(sk))}</span>'
        f'<span style="color:{trend_arrow(raw_series,ck)[1]};font-size:.95rem;text-align:center;font-weight:700">'
        f'{trend_arrow(raw_series,ck)[0]}</span>'
        f'<span class="sc-read">{rd}</span>'
        f'</div>'
        for lbl,ck,sk,rd in sc_data)
    st.markdown(f'<div class="scorecard-wrap">{rows}</div>',unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;justify-content:space-between;padding-top:12px;'
    f'border-top:1px solid #1f3354;margin-top:1.5rem">'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080;font-weight:500">Data: Federal Reserve FRED (GDPC1, FEDFUNDS, VIXCLS…) · yfinance</span>'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080;font-weight:500">Educational only — not financial advice</span>'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080;font-weight:500">MACRO/SIGNAL v5.1 · {datetime.now().year}</span>'
    f'</div>',unsafe_allow_html=True)
