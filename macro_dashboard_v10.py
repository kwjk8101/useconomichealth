"""
MACRO/SIGNAL Dashboard v10.0
============================================================
Install: pip install streamlit pandas plotly fredapi yfinance pytz requests
Run:     streamlit run macro_dashboard.py
Secrets (Streamlit Cloud → Manage App → Secrets):
  FRED_API_KEY     = "your_fred_key"
  FINNHUB_API_KEY  = "d7irilhr01qn2qav4v80d7irilhr01qn2qav4v8g"

v10.0 changes:
- Economic calendar: Finnhub live API (confirmed dates, real data, prev/est/actual)
- Finnhub market news feed: latest macro + markets headlines in sidebar
- Finnhub earnings calendar: upcoming major earnings near macro releases
- Fear & Greed: Finnhub sentiment data added as additional signal
- New: Options Put/Call ratio proxy from VIX term structure
- New: Global macro summary card (DXY + rates + commodities snapshot)
- New: MarketWatch calendar deep-link for full detail
- All sections: anchored nav, generous spacing, beginner descriptions
============================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fredapi import Fred
import yfinance as yf
from datetime import datetime, timedelta, date
import pytz
import time as _time

FRED_API_KEY    = st.secrets.get("FRED_API_KEY", "")
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "d7irilhr01qn2qav4v80d7irilhr01qn2qav4v8g")
SGT = pytz.timezone("Asia/Singapore")
def now_sgt(): return datetime.now(SGT)

st.set_page_config(page_title="MACRO/SIGNAL", page_icon="📡",
                   layout="wide", initial_sidebar_state="expanded")

APP_BG = "#060b14"   # solid — used for fullscreen background

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Space Grotesk',sans-serif;background:{APP_BG}!important;color:#dde8f5!important}}
.stApp{{background:{APP_BG}!important}}
.main .block-container{{padding:2rem 2.2rem 3rem;max-width:1800px}}
p,span,div{{color:#dde8f5}}
[data-testid="stSidebar"]{{background:#0b1525!important;border-right:2px solid #1f3354}}
[data-testid="stSidebar"] *{{color:#c5d8f0!important}}
[data-testid="stSidebar"] label{{font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.09em;color:#8ab4d8!important}}
[data-testid="stSidebar"] .stMarkdown p{{color:#8ab4d8!important;font-size:.78rem!important}}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"]>div{{background:#0f1e35!important;border:1px solid #2a4060!important;color:#dde8f5!important;font-family:'IBM Plex Mono',monospace!important}}
[data-testid="stSidebar"] .stDateInput input{{background:#0f1e35!important;border:1px solid #2a4060!important;color:#dde8f5!important}}
[data-testid="stSidebar"] svg{{fill:#8ab4d8!important}}
[data-testid="stMetric"]{{background:#0f1e35;border:1px solid #1f3354;border-radius:10px;padding:1rem 1.2rem;position:relative;overflow:hidden}}
[data-testid="stMetric"]::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#22d3ee}}
[data-testid="stMetricLabel"]{{color:#8ab4d8!important;font-size:.7rem!important;font-family:'IBM Plex Mono',monospace!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.1em}}
[data-testid="stMetricValue"]{{color:#f0f8ff!important;font-size:1.5rem!important;font-weight:700!important;font-family:'IBM Plex Mono',monospace!important}}
[data-testid="stMetricDelta"]{{font-family:'IBM Plex Mono',monospace!important;font-size:.76rem!important;font-weight:600!important}}
[data-testid="stTabs"] button{{font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;font-weight:600!important;text-transform:uppercase;letter-spacing:.1em;color:#7aa0c8!important;padding:.55rem 1rem!important}}
[data-testid="stTabs"] button:hover{{color:#c5d8f0!important}}
[data-testid="stTabs"] button[aria-selected="true"]{{color:#22d3ee!important;font-weight:700!important}}
.stTabs [data-baseweb="tab-border"]{{background:#1f3354!important}}
.stTabs [data-baseweb="tab-highlight"]{{background:#22d3ee!important;height:2px!important}}
hr{{border-color:#1f3354!important;margin:2rem 0!important}}
h1{{font-family:'Space Grotesk',sans-serif!important;font-weight:800!important;font-size:1.85rem!important;color:#f0f8ff!important;letter-spacing:-.02em}}
h2{{color:#dde8f5!important;font-weight:700!important}}
h3{{font-family:'IBM Plex Mono',monospace!important;font-size:.78rem!important;font-weight:700!important;color:#8ab4d8!important;text-transform:uppercase;letter-spacing:.13em}}
[data-testid="stAlert"]{{background:#0f1e35!important;border:1px solid #1f3354!important;border-radius:8px;font-family:'IBM Plex Mono',monospace!important;color:#dde8f5!important}}
button[title="View fullscreen"],button[data-testid="StyledFullScreenButton"]{{background:#1f3354!important;border:1px solid #2a4060!important;color:#c5d8f0!important;border-radius:4px!important;opacity:1!important}}
button[title="View fullscreen"]:hover,button[data-testid="StyledFullScreenButton"]:hover{{background:#22d3ee!important;color:{APP_BG}!important;border-color:#22d3ee!important}}
.stButton>button{{background:#1f3354!important;border:1.5px solid #2a4060!important;color:#c5d8f0!important;font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important;font-weight:600!important;letter-spacing:.06em;border-radius:5px!important;padding:.4rem 1rem!important}}
.stButton>button:hover{{background:#22d3ee!important;color:{APP_BG}!important;border-color:#22d3ee!important}}
.refresh-btn>button{{background:rgba(34,211,238,.15)!important;border:1.5px solid rgba(34,211,238,.5)!important;color:#22d3ee!important}}
.refresh-btn>button:hover{{background:#22d3ee!important;color:{APP_BG}!important}}
::-webkit-scrollbar{{width:5px}}::-webkit-scrollbar-track{{background:#0b1525}}::-webkit-scrollbar-thumb{{background:#1f3354;border-radius:3px}}
/* section spacing */
.section-gap{{margin-top:2.5rem;margin-bottom:0.5rem}}
.section-gap-sm{{margin-top:1.5rem;margin-bottom:0.25rem}}
/* regime banner */
.regime-banner{{display:flex;align-items:center;gap:14px;background:#0f1e35;border:1px solid #1f3354;border-radius:10px;padding:14px 22px;margin-bottom:0}}
.regime-dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0}}
.regime-name{{font-family:'IBM Plex Mono',monospace;font-size:.88rem;font-weight:700;letter-spacing:.08em}}
.regime-desc{{font-size:.83rem;color:#a0bcd8;margin-left:auto;text-align:right;max-width:500px}}
/* chips */
.live-chip{{display:inline-flex;align-items:center;gap:6px;padding:5px 13px;border-radius:20px;background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.3);font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#22d3ee}}
.live-dot{{width:7px;height:7px;border-radius:50%;background:#22d3ee;display:inline-block;animation:blink 1.8s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
.range-chip{{display:inline-block;padding:5px 13px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:600;background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.3);color:#22d3ee}}
/* pills */
.sig-pill{{display:inline-block;padding:3px 10px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;letter-spacing:.05em}}
.sow{{background:rgba(34,197,94,.18);color:#4ade80;border:1px solid rgba(34,197,94,.4)}}
.ow{{background:rgba(134,239,172,.14);color:#86efac;border:1px solid rgba(134,239,172,.35)}}
.n{{background:rgba(148,163,184,.12);color:#94a3b8;border:1px solid rgba(148,163,184,.3)}}
.uw{{background:rgba(252,165,165,.14);color:#fca5a5;border:1px solid rgba(252,165,165,.35)}}
.suw{{background:rgba(239,68,68,.18);color:#f87171;border:1px solid rgba(239,68,68,.4)}}
/* cards */
.risk-card{{background:#0f1e35;border:1px solid #1f3354;border-radius:10px;padding:18px;height:100%}}
.risk-title{{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;color:#8ab4d8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}}
.risk-val{{font-family:'IBM Plex Mono',monospace;font-size:2rem;font-weight:700;line-height:1}}
.risk-label{{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-top:5px}}
.risk-sub{{font-size:.74rem;color:#7aa0c8;margin-top:8px;font-weight:500;line-height:1.5}}
/* spreads */
.spread-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(31,51,84,.6)}}
.spread-row:last-child{{border-bottom:none}}
.spread-name{{font-size:.79rem;color:#a0bcd8;font-weight:500}}
.spread-val{{font-family:'IBM Plex Mono',monospace;font-size:.88rem;font-weight:700}}
/* market ticker */
.mkt-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-bottom:0}}
.mkt-card{{background:#0f1e35;border:1px solid #1f3354;border-radius:10px;padding:14px 16px;position:relative;overflow:hidden}}
.mkt-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.mkt-name{{font-family:'IBM Plex Mono',monospace;font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#8ab4d8;margin-bottom:7px}}
.mkt-price{{font-family:'IBM Plex Mono',monospace;font-size:1.15rem;font-weight:700;color:#f0f8ff}}
.mkt-chg{{font-family:'IBM Plex Mono',monospace;font-size:.74rem;font-weight:700;margin-top:4px}}
.mkt-up{{color:#4ade80}}.mkt-dn{{color:#f87171}}.mkt-flat{{color:#94a3b8}}
/* chart section titles */
.chart-section-title{{font-family:'IBM Plex Mono',monospace;font-size:.76rem;font-weight:700;color:#8ab4d8;text-transform:uppercase;letter-spacing:.13em;padding:8px 0 5px;border-bottom:1px solid #1f3354;margin-bottom:12px}}
/* heatmap */
.hm-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.hm-cell{{border-radius:8px;padding:12px 9px;text-align:center}}
.hm-name{{font-size:.77rem;font-weight:600;margin-bottom:5px;color:#dde8f5}}
.hm-sig{{font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:700}}
/* scorecard */
.scorecard-wrap{{background:#0f1e35;border:1px solid #1f3354;border-radius:10px;padding:16px 18px}}
.sc-row{{display:grid;grid-template-columns:145px 76px 24px 1fr;gap:6px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(31,51,84,.7)}}
.sc-row:last-child{{border-bottom:none}}
.sc-label{{color:#a0bcd8;font-family:'IBM Plex Mono',monospace;font-size:.72rem}}
.sc-val{{color:#22d3ee;font-family:'IBM Plex Mono',monospace;font-size:.78rem;font-weight:700;text-align:right}}
.sc-read{{color:#7aa0c8;font-size:.7rem}}
/* fear/greed + recession */
.rec-bar-wrap{{background:#0b1525;border-radius:6px;height:14px;overflow:hidden;border:1px solid #1f3354;margin-top:10px}}
/* 52w */
.hl-card{{background:#0f1e35;border:1px solid #1f3354;border-radius:8px;padding:11px 13px}}
.hl-name{{font-family:'IBM Plex Mono',monospace;font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#8ab4d8;margin-bottom:6px}}
.hl-price{{font-family:'IBM Plex Mono',monospace;font-size:1.05rem;font-weight:700;color:#f0f8ff}}
.hl-bar-bg{{background:#1a2a3a;border-radius:3px;height:6px;margin-top:7px}}
.hl-bar-fill{{height:6px;border-radius:3px;background:linear-gradient(90deg,#f87171,#f59e0b,#4ade80)}}
/* description boxes */
.desc-box{{background:rgba(34,211,238,.04);border:1px solid rgba(34,211,238,.15);border-radius:8px;padding:12px 16px;margin-bottom:18px}}
.desc-box p{{color:#a0bcd8!important;font-size:.81rem!important;line-height:1.6;margin:0}}
.desc-box strong{{color:#22d3ee!important}}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
BG_SOLID = APP_BG          # solid bg for fullscreen charts
BG_TRANS = "rgba(0,0,0,0)" # transparent for inline charts
GRID     = "rgba(31,51,84,0.8)"
MONO     = "'IBM Plex Mono', monospace"
TCLR     = "#7aa0c8"
TICK_W   = "#ffffff"        # pure white ticks on live charts
TICK_B   = "#e0eeff"        # bright ticks on macro charts
C = dict(blue="#22d3ee", red="#f87171", orange="#fb923c", green="#4ade80",
         purple="#a78bfa", yellow="#f59e0b", teal="#2dd4bf", pink="#f472b6")

def theme(fig, h=360, title=None, fullscreen_bg=False):
    """Standard macro chart theme. fullscreen_bg=True uses solid #060b14."""
    bg = BG_SOLID if fullscreen_bg else BG_TRANS
    upd = dict(
        height=h, paper_bgcolor=bg, plot_bgcolor=bg,
        font=dict(family=MONO, color=TCLR, size=13),
        legend=dict(bgcolor="rgba(15,30,53,.97)", bordercolor="#1f3354",
                    borderwidth=1, font=dict(size=12, color="#c5d8f0")),
        margin=dict(l=16, r=20, t=52 if title else 34, b=44),
        hoverlabel=dict(bgcolor="#0f1e35", bordercolor="#2a4060",
                        font=dict(family=MONO, size=13, color="#dde8f5")),
    )
    if title:
        upd["title"] = dict(text=title,
                            font=dict(size=15, color="#eaf4ff", family=MONO), x=0.01)
    fig.update_layout(**upd)
    fig.update_xaxes(gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=13, color=TICK_B, family=MONO),
                     linecolor="#2a4060", linewidth=1.5,
                     showspikes=True, spikecolor="#3a5070", spikethickness=1,
                     title_font=dict(size=12, color=TICK_B))
    fig.update_yaxes(gridcolor=GRID, zeroline=False,
                     tickfont=dict(size=13, color=TICK_B, family=MONO),
                     linecolor="#2a4060", linewidth=1.5,
                     title_font=dict(size=12, color=TICK_B))
    fig.update_annotations(font=dict(size=12, color="#a8c8e8"))
    return fig

def desc(text):
    """Render a beginner-friendly description box."""
    st.markdown(f'<div class="desc-box"><p>{text}</p></div>',
                unsafe_allow_html=True)

def section(label, anchor=""):
    st.markdown('<div style="margin-top:3.5rem"></div>', unsafe_allow_html=True)
    if anchor:
        st.markdown(f'<div id="{anchor}" style="position:relative;top:-70px;visibility:hidden"></div>',
                    unsafe_allow_html=True)
    st.markdown(f"### {label}")

# ── FRED IDs ──────────────────────────────────────────────────────────────────
FRED_IDS = {
    "fed_rate":  "FEDFUNDS",
    "cpi":       "CPIAUCSL",
    "core_cpi":  "CPILFESL",
    "pce":       "PCEPI",
    "unrate":    "UNRATE",
    "gdp":       "GDP",
    "gdpc1":     "GDPC1",
    "t10y":      "GS10",
    "t2y":       "GS2",
    "t3m":       "DTB3",
    "retail":    "RSAFS",
    "housing":   "HOUST",
    "m2":        "M2SL",
    "vix":       "VIXCLS",
    "hy_spread": "BAMLH0A0HYM2",
    "ig_spread": "BAMLC0A0CM",
    "cfnai":     "CFNAI",
    "ipman":     "IPMAN",
    "sahm":      "SAHMCURRENT",
}

SECTORS = {
    "Healthcare":"XLV","Consumer_Stap":"XLP","Utilities":"XLU",
    "Financials":"XLF","Energy":"XLE","Materials":"XLB",
    "Industrials":"XLI","Technology":"XLK","Consumer_Disc":"XLY",
    "Real_Estate":"XLRE","Comm_Services":"XLC",
}
SLABELS = {k: k.replace("_"," ") for k in SECTORS}

MARKET_TICKERS = {
    "S&P 500":"^GSPC","Nasdaq":"^IXIC","BTC/USD":"BTC-USD",
    "Gold":"GC=F","Oil (WTI)":"CL=F","DXY":"DX-Y.NYB","10Y Yield":"^TNX",
}
MKT_ACCENTS = {
    "S&P 500":"#22d3ee","Nasdaq":"#a78bfa","BTC/USD":"#f59e0b",
    "Gold":"#fbbf24","Oil (WTI)":"#fb923c","DXY":"#2dd4bf","10Y Yield":"#86efac",
}

LIVE_CHART_CONFIG = {
    "S&P 500":   dict(ticker="^GSPC",    color="#22d3ee"),
    "Nasdaq":    dict(ticker="^IXIC",    color="#a78bfa"),
    "BTC/USD":   dict(ticker="BTC-USD",  color="#f59e0b"),
    "Gold":      dict(ticker="GC=F",     color="#fbbf24"),
    "Oil (WTI)": dict(ticker="CL=F",     color="#fb923c"),
    "DXY":       dict(ticker="DX-Y.NYB", color="#2dd4bf"),
}

ASIA_CHART_CONFIG = {
    "STI (Singapore)": dict(ticker="^STI",     color="#22d3ee"),
    "Nikkei 225":      dict(ticker="^N225",     color="#f59e0b"),
    "Hang Seng":       dict(ticker="^HSI",      color="#f87171"),
    "ASX 200":         dict(ticker="^AXJO",     color="#4ade80"),
    "KOSPI":           dict(ticker="^KS11",     color="#a78bfa"),
    "CSI 300 (China)": dict(ticker="000300.SS", color="#fb923c"),
}

CORR_TICKERS = {
    "SPX":  "^GSPC",
    "Gold": "GC=F",
    "BTC":  "BTC-USD",
    "DXY":  "DX-Y.NYB",
    "Oil":  "CL=F",
    "10Y":  "^TNX",
}

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_fred(api_key):
    fred  = Fred(api_key=api_key)
    end   = datetime.today()
    start = end - timedelta(days=365*6)
    raw   = {}
    for name, sid in FRED_IDS.items():
        try:
            s = fred.get_series(sid, observation_start=start, observation_end=end)
            if s is not None and len(s) > 0:
                s = s.dropna(); s.index = pd.to_datetime(s.index)
                raw[name] = s
        except Exception:
            pass
    frames = {}
    for name, s in raw.items():
        frames[name] = s.resample("QE").last() if name in ("gdp","gdpc1") else s.resample("ME").last()
    if "cpi"      in raw: frames["cpi_yoy"]      = raw["cpi"].resample("ME").last().pct_change(12)*100
    if "core_cpi" in raw: frames["core_cpi_yoy"] = raw["core_cpi"].resample("ME").last().pct_change(12)*100
    if "pce"      in raw: frames["pce_yoy"]       = raw["pce"].resample("ME").last().pct_change(12)*100
    if "gdp"      in raw: frames["gdp_g"]          = raw["gdp"].resample("QE").last().pct_change(4)*100
    if "gdpc1"    in raw:
        rg = raw["gdpc1"].resample("QE").last()
        frames["gdpc1_g"] = rg.pct_change(4)*100
        frames["gdpc1_r"] = rg
    if "m2"     in raw: frames["m2_g"]      = raw["m2"].resample("ME").last().pct_change(12)*100
    if "retail" in raw: frames["retail_g"]  = raw["retail"].resample("ME").last().pct_change(12)*100
    if "ipman"  in raw: frames["ipman_yoy"] = raw["ipman"].resample("ME").last().pct_change(12)*100
    if "t10y" in raw and "t2y" in raw:
        t10 = raw["t10y"].resample("ME").last(); t2 = raw["t2y"].resample("ME").last()
        tmp = pd.concat([t10,t2],axis=1,keys=["a","b"]).dropna()
        frames["curve_10_2"] = tmp["a"]-tmp["b"]
    if "t10y" in raw and "t3m" in raw:
        t10 = raw["t10y"].resample("ME").last(); t3m = raw["t3m"].resample("ME").last()
        tmp = pd.concat([t10,t3m],axis=1,keys=["a","b"]).dropna()
        frames["curve_10_3m"] = tmp["a"]-tmp["b"]
    for k in ("cpi_yoy","core_cpi_yoy","pce_yoy","gdp_g","gdpc1_g",
               "m2_g","retail_g","ipman_yoy","curve_10_2","curve_10_3m"):
        if k in frames: raw[k] = frames[k]
    return raw, pd.DataFrame(frames)

@st.cache_data(ttl=300, show_spinner=False)
def load_market_prices():
    out = {}
    for name, ticker in MARKET_TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if hist.empty: continue
            c = hist["Close"].dropna()
            now = float(c.iloc[-1]); prev = float(c.iloc[-2]) if len(c)>1 else now
            chg = now-prev; pct = (chg/prev*100) if prev else 0
            out[name] = dict(price=now,chg=chg,pct=pct)
        except Exception: pass
    return out

@st.cache_data(ttl=300, show_spinner=False)
def load_live_chart(ticker, period="6mo", interval="1d"):
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if hist.empty: return None
        hist.index = pd.to_datetime(hist.index)
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        return hist
    except Exception: return None

@st.cache_data(ttl=300, show_spinner=False)
def load_live_chart_dates(ticker, start_str, end_str, interval="1d"):
    """Fetch OHLCV for a custom date range."""
    try:
        hist = yf.Ticker(ticker).history(start=start_str, end=end_str, interval=interval)
        if hist.empty: return None
        hist.index = pd.to_datetime(hist.index)
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        return hist
    except Exception: return None

@st.cache_data(ttl=900, show_spinner=False)
def load_etfs():
    """
    ETF loader — three reliability improvements over previous version:
    1. Uses yf.download() in batch (one request) rather than 11 individual calls.
    2. Falls back to individual Ticker.history() with a retry if batch fails.
    3. pct() is a standalone function (not a closure) to avoid Python scoping bug
       where the variable 'c' gets overwritten by the next loop iteration.
    """
    rows   = []
    tickers = list(SECTORS.values())
    keys    = list(SECTORS.keys())

    def _pct_from_series(closes, n):
        """Compute % change from n bars ago — safe standalone function."""
        if closes is None or len(closes) < 2:
            return None
        idx  = max(0, len(closes) - n)
        base = float(closes.iloc[idx])
        now  = float(closes.iloc[-1])
        return round((now / base - 1) * 100, 2) if base > 0 else None

    # --- Attempt 1: batch download -------------------------------------------
    batch_ok = False
    try:
        raw = yf.download(
            tickers, period="1y", interval="1d",
            group_by="ticker", auto_adjust=True,
            progress=False, threads=True,
        )
        if not raw.empty:
            batch_ok = True
    except Exception:
        raw = None

    for i, (key, ticker) in enumerate(SECTORS.items()):
        try:
            if batch_ok and raw is not None:
                # Multi-ticker download nests columns as (ticker, field)
                if isinstance(raw.columns, pd.MultiIndex):
                    if ticker in raw.columns.get_level_values(0):
                        closes = raw[ticker]["Close"].dropna()
                    else:
                        closes = None
                else:
                    # Single-ticker fallback (shouldn't happen in batch)
                    closes = raw["Close"].dropna() if "Close" in raw.columns else None
            else:
                closes = None

            # --- Attempt 2: individual fetch if batch gave nothing -----------
            if closes is None or len(closes) < 5:
                for _attempt in range(2):
                    try:
                        hist = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
                        if not hist.empty:
                            closes = hist["Close"].dropna()
                            break
                    except Exception:
                        import time; time.sleep(0.4)

            if closes is None or len(closes) < 2:
                continue

            closes.index = pd.to_datetime(closes.index)
            if closes.index.tz is not None:
                closes.index = closes.index.tz_localize(None)

            now  = float(closes.iloc[-1])
            d1   = _pct_from_series(closes, 2)
            m1   = _pct_from_series(closes, 22)
            ys   = closes[closes.index >= pd.Timestamp(f"{datetime.today().year}-01-01")]
            ytd  = round((now / float(ys.iloc[0]) - 1) * 100, 2) if len(ys) > 0 else None

            rows.append(dict(
                key=key, label=SLABELS[key], ticker=ticker,
                price=round(now, 2), d1=d1, m1=m1, ytd=ytd,
            ))
        except Exception:
            pass

    return rows

@st.cache_data(ttl=600, show_spinner=False)
def load_52w_highs():
    results = {}
    for name, cfg in {**LIVE_CHART_CONFIG, **ASIA_CHART_CONFIG}.items():
        try:
            hist = yf.Ticker(cfg["ticker"]).history(period="1y")
            if hist.empty: continue
            c = hist["Close"].dropna()
            now=float(c.iloc[-1]); hi52=float(c.max()); lo52=float(c.min())
            pct_pos=(now-lo52)/(hi52-lo52)*100 if hi52>lo52 else 50
            results[name]=dict(price=now,hi52=hi52,lo52=lo52,pct_pos=pct_pos,color=cfg["color"])
        except Exception: pass
    return results

@st.cache_data(ttl=600, show_spinner=False)
def load_correlations():
    """
    Fetch 6mo daily closes for each asset independently,
    compute daily % returns, align on common dates, return correlation matrix.
    """
    closes = {}
    for label, ticker in CORR_TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="6mo")
            if hist.empty: continue
            s = hist["Close"].dropna()
            s.index = pd.to_datetime(s.index)
            if s.index.tz is not None:
                s.index = s.index.tz_localize(None)
            # Normalise index to date only for cross-asset alignment
            s.index = s.index.normalize()
            # Deduplicate any same-day entries
            s = s[~s.index.duplicated(keep="last")]
            closes[label] = s
        except Exception:
            pass
    if len(closes) < 2:
        return None
    df = pd.DataFrame(closes)
    # Forward-fill up to 3 days to bridge weekend/holiday gaps across markets
    df = df.ffill(limit=3).dropna()
    if len(df) < 20:
        return None
    rets = df.pct_change().dropna()
    if rets.empty or len(rets) < 10:
        return None
    return rets.corr().round(2)


@st.cache_data(ttl=3600, show_spinner=False)  # refresh hourly
def load_econ_calendar(finnhub_key, fred_key):
    """
    PRIMARY: Finnhub /calendar/economic — confirmed dates with previous value,
    estimate, and actual (once released). Returns real market-moving events
    identical to what you see on MarketWatch/Investing.com economic calendars.

    FALLBACK: If Finnhub fails, falls back to FRED /release/dates for confirmed
    scheduled dates (no prev/est/actual values, but correct dates).

    Finnhub endpoint: GET https://finnhub.io/api/v1/calendar/economic
    Params: from (YYYY-MM-DD), to (YYYY-MM-DD), token
    Response: { "economicCalendar": [ {
        "actual": null | number,
        "country": "US",
        "estimate": null | number,
        "event": "CPI m/m",
        "impact": "high" | "medium" | "low",
        "prev": number,
        "time": "2025-04-30" or "2025-04-30 08:30:00",
        "unit": "%" | ...
    } ] }

    MarketWatch full calendar: https://www.marketwatch.com/economy-politics/calendar
    """
    import requests as _req

    today      = date.today()
    look_ahead = today + timedelta(days=60)

    # ── Attempt 1: Finnhub ────────────────────────────────────────────────────
    try:
        url = "https://finnhub.io/api/v1/calendar/economic"
        params = {
            "from":  today.strftime("%Y-%m-%d"),
            "to":    look_ahead.strftime("%Y-%m-%d"),
            "token": finnhub_key,
        }
        r = _req.get(url, params=params, timeout=12,
                     headers={"User-Agent": "MacroSignal/10.0"})
        if r.status_code == 200:
            raw_items = r.json().get("economicCalendar", [])

            # Filter US-only events and map impact labels
            IMPACT_MAP = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
            # Keywords that identify the highest-value macro events
            HIGH_VALUE_KEYWORDS = [
                "nonfarm", "non-farm", "cpi", "pce", "gdp", "fomc", "fed funds",
                "unemployment rate", "payroll", "retail sales", "ppi",
                "housing starts", "ism", "consumer confidence", "jobless",
                "durable goods", "industrial production", "core inflation",
                "interest rate decision", "fed chair", "balance of trade",
                "consumer price", "producer price", "personal spending",
            ]

            results = []
            for item in raw_items:
                country = (item.get("country") or "").upper()
                if country and country != "US":
                    continue  # US events only
                event_name = item.get("event", "")
                time_str   = item.get("time", "") or ""
                impact_raw = (item.get("impact") or "low").lower()
                impact     = IMPACT_MAP.get(impact_raw, "LOW")

                # Parse date — Finnhub gives "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
                date_part = time_str[:10] if time_str else ""
                if not date_part:
                    continue
                try:
                    rel_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if rel_date < today:
                    continue

                days_away = (rel_date - today).days

                # Boost importance score for known high-value events
                name_lower = event_name.lower()
                is_high_value = any(kw in name_lower for kw in HIGH_VALUE_KEYWORDS)
                if impact == "LOW" and not is_high_value:
                    continue  # skip low-impact unknown events to keep list clean

                results.append({
                    "name":      event_name,
                    "date":      rel_date,
                    "days_away": days_away,
                    "impact":    impact,
                    "source":    "Finnhub",
                    "prev":      item.get("prev"),
                    "estimate":  item.get("estimate"),
                    "actual":    item.get("actual"),
                    "unit":      item.get("unit", ""),
                    "time_str":  time_str[11:16] if len(time_str) > 10 else "",
                })

            if results:
                # Sort by date, then by impact weight
                IMPACT_WEIGHT = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
                results.sort(key=lambda x: (x["date"], IMPACT_WEIGHT.get(x["impact"], 3)))
                return results[:20]
    except Exception:
        pass

    # ── Fallback: FRED /release/dates ─────────────────────────────────────────
    RELEASES = [
        (10,   "CPI Report (BLS)",                  "HIGH",   "BLS"),
        (175,  "Non-Farm Payrolls & Unemployment",  "HIGH",   "BLS"),
        (21,   "GDP Advance / Preliminary",         "HIGH",   "BEA"),
        (50,   "Personal Income & PCE Inflation",   "HIGH",   "BEA"),
        (18,   "FOMC Interest Rate Decision",       "HIGH",   "Federal Reserve"),
        (33,   "Unemployment Rate",                 "HIGH",   "BLS"),
        (46,   "Producer Price Index (PPI)",        "MEDIUM", "BLS"),
        (22,   "Retail Sales",                      "MEDIUM", "Census Bureau"),
        (20,   "Housing Starts",                    "MEDIUM", "Census Bureau"),
        (82,   "Initial Jobless Claims",            "MEDIUM", "DOL"),
        (323,  "ISM Manufacturing PMI",             "MEDIUM", "ISM"),
        (324,  "ISM Services PMI",                  "MEDIUM", "ISM"),
        (326,  "FOMC Minutes",                      "MEDIUM", "Federal Reserve"),
        (47,   "Durable Goods Orders",              "MEDIUM", "Census Bureau"),
        (19,   "Industrial Production",             "MEDIUM", "Federal Reserve"),
        (148,  "Consumer Confidence (Conf. Board)", "MEDIUM", "Conference Board"),
    ]
    results = []
    for release_id, name, impact, source in RELEASES:
        try:
            url = (
                f"https://api.stlouisfed.org/fred/release/dates"
                f"?release_id={release_id}"
                f"&realtime_start={today.strftime('%Y-%m-%d')}"
                f"&realtime_end={look_ahead.strftime('%Y-%m-%d')}"
                f"&api_key={fred_key}&file_type=json"
            )
            r = _req.get(url, timeout=8)
            if r.status_code != 200:
                continue
            dates_raw = r.json().get("release_dates", [])
            for entry in dates_raw:
                d_str = entry.get("date", "")
                if not d_str:
                    continue
                try:
                    rel_date = datetime.strptime(d_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if rel_date < today:
                    continue
                results.append({
                    "name":      name,
                    "date":      rel_date,
                    "days_away": (rel_date - today).days,
                    "impact":    impact,
                    "source":    "FRED",
                    "prev":      None,
                    "estimate":  None,
                    "actual":    None,
                    "unit":      "",
                    "time_str":  "",
                })
                break
        except Exception:
            continue

    seen, unique = set(), []
    for ev in sorted(results, key=lambda x: x["date"]):
        if ev["name"] not in seen:
            seen.add(ev["name"])
            unique.append(ev)
    return unique[:16]


@st.cache_data(ttl=1800, show_spinner=False)  # refresh every 30 min
def load_finnhub_news(finnhub_key):
    """
    Fetch latest market-moving macro & finance headlines from Finnhub.
    Endpoint: GET https://finnhub.io/api/v1/news?category=general&token=...
    Returns list of {headline, source, datetime, url, summary} dicts.
    """
    import requests as _req
    try:
        r = _req.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "general", "minId": 0, "token": finnhub_key},
            timeout=10,
            headers={"User-Agent": "MacroSignal/10.0"},
        )
        if r.status_code != 200:
            return []
        items = r.json()
        news = []
        for item in items[:20]:
            headline = item.get("headline", "").strip()
            if not headline or len(headline) < 10:
                continue
            ts = item.get("datetime", 0)
            try:
                dt = datetime.fromtimestamp(ts, tz=SGT)
            except Exception:
                dt = now_sgt()
            news.append({
                "headline": headline,
                "source":   item.get("source", ""),
                "url":      item.get("url", ""),
                "summary":  item.get("summary", "")[:200],
                "dt":       dt,
                "age_hrs":  round((now_sgt() - dt).total_seconds() / 3600, 1),
            })
        # Sort newest first
        news.sort(key=lambda x: x["dt"], reverse=True)
        return news[:12]
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def load_finnhub_earnings(finnhub_key):
    """
    Fetch upcoming S&P 500 company earnings near macro release dates.
    Endpoint: GET https://finnhub.io/api/v1/calendar/earnings
    Returns list of {symbol, date, epsEstimate, revenueEstimate} dicts.
    Filters for high-profile companies only.
    """
    import requests as _req
    today      = date.today()
    look_ahead = today + timedelta(days=14)

    # High-profile tickers that move the broader market
    WATCHLIST = {
        "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","JPM","BAC","GS",
        "MS","WFC","C","V","MA","BRK.B","XOM","CVX","JNJ","UNH","PFE","MRK",
        "WMT","HD","MCD","COST","SBUX","DIS","NFLX","AMD","INTC","CRM","ORCL",
        "IBM","PYPL","ADBE","QCOM","TXN","MMM","CAT","BA","GE","HON","UPS","FDX",
    }
    try:
        r = _req.get(
            "https://finnhub.io/api/v1/calendar/earnings",
            params={
                "from":  today.strftime("%Y-%m-%d"),
                "to":    look_ahead.strftime("%Y-%m-%d"),
                "token": finnhub_key,
            },
            timeout=10,
            headers={"User-Agent": "MacroSignal/10.0"},
        )
        if r.status_code != 200:
            return []
        items = r.json().get("earningsCalendar", [])
        results = []
        for item in items:
            sym = item.get("symbol", "")
            if sym not in WATCHLIST:
                continue
            d_str = item.get("date", "")
            try:
                earn_date = datetime.strptime(d_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if earn_date < today:
                continue
            results.append({
                "symbol":      sym,
                "date":        earn_date,
                "days_away":   (earn_date - today).days,
                "eps_est":     item.get("epsEstimate"),
                "rev_est":     item.get("revenueEstimate"),
                "hour":        item.get("hour", ""),  # "bmo" before market open, "amc" after
            })
        results.sort(key=lambda x: x["date"])
        return results[:16]
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def load_cnn_fear_greed():
    """
    Fetch CNN Business Fear & Greed Index from their public data API.
    Returns dict with value (0-100), label, and 30-day history list.
    Falls back to None gracefully if blocked.
    """
    import requests as _req
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    ]
    for ua in user_agents:
        try:
            r = _req.get(
                "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                headers={"User-Agent": ua, "Accept": "application/json"},
                timeout=8,
            )
            if r.status_code != 200:
                continue
            data   = r.json()
            score  = round(float(data["fear_and_greed"]["score"]), 1)
            label  = data["fear_and_greed"]["rating"].replace("_", " ").title()
            hist_raw = data.get("fear_and_greed_historical", {}).get("data", [])
            history = [
                (datetime.fromtimestamp(d["x"] / 1000), round(d["y"], 1))
                for d in hist_raw[-30:]
            ]
            return {"value": score, "label": label, "history": history, "source": "CNN"}
        except Exception:
            continue
    return None

# ── Signal engine ─────────────────────────────────────────────────────────────
def latest(raw, col):
    if col not in raw: return None
    s = raw[col].dropna()
    return round(float(s.iloc[-1]),4) if len(s)>0 else None

def prev_val(raw, col, n=1):
    if col not in raw: return None
    s = raw[col].dropna()
    return round(float(s.iloc[-1-n]),4) if len(s)>n else None

def compute(raw):
    fed  = latest(raw,"fed_rate")     or 0
    cpi  = latest(raw,"cpi_yoy")      or 0
    core = latest(raw,"core_cpi_yoy") or 0
    unr  = latest(raw,"unrate")       or 0
    gdpg = latest(raw,"gdp_g")        or 0
    rgdpg= latest(raw,"gdpc1_g")      or 0
    cur  = latest(raw,"curve_10_2")   or 0
    cur3m= latest(raw,"curve_10_3m")  or 0
    m2g  = latest(raw,"m2_g")         or 0
    retg = latest(raw,"retail_g")     or 0
    vix  = latest(raw,"vix")          or 0
    hy   = latest(raw,"hy_spread")    or 0
    ig   = latest(raw,"ig_spread")    or 0
    cfnai= latest(raw,"cfnai")        or 0
    ipyoy= latest(raw,"ipman_yoy")    or 0
    sahm = latest(raw,"sahm")         or 0
    use_gdp = rgdpg if rgdpg != 0 else gdpg

    if sahm>=0.5:
        reg,col,desc_="SAHM RULE TRIGGERED · RECESSION SIGNAL","#f87171",f"Sahm at {sahm:.2f} — above 0.5 threshold. Recession likely underway. Maximum defensive positioning."
    elif cpi>5 and fed>4:
        reg,col,desc_="HIGH INFLATION · TIGHT POLICY","#f87171","Fed in active tightening. Risk assets under pressure. Energy, Materials and Financials outperform."
    elif cpi>3 and fed<3:
        reg,col,desc_="INFLATION RESURGENCE · POLICY LAG","#fb923c","Inflation above target but policy is behind the curve. Watch commodities, TIPS and Materials."
    elif cur<0 or cur3m<0:
        reg,col,desc_="INVERTED YIELD CURVE · RECESSION RISK","#f59e0b",f"Curve at {cur:.2f}%. Historically precedes recession by 6–18 months. Rotate to defensives."
    elif cpi<2.5 and fed<3 and unr<5 and use_gdp>1.5:
        reg,col,desc_="GOLDILOCKS · SOFT LANDING","#4ade80","Low inflation, easy policy, strong labour. Ideal for broad risk-on. Tech and Consumer Disc lead."
    elif unr>5.5 or use_gdp<0:
        reg,col,desc_="RECESSION · RISK-OFF","#f87171","Growth contracting. Defensives key. Healthcare, Staples, Utilities, cash preservation."
    else:
        reg,col,desc_="MID-CYCLE EXPANSION","#22d3ee","Normalised expansion. Balanced positioning with tilt toward cyclicals and quality growth."

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
    return dict(reg=reg,col=col,desc=desc_,sc=sc,conv=conv,
                fed=fed,cpi=cpi,core=core,unr=unr,
                gdpg=gdpg,rgdpg=rgdpg,
                cur=cur,cur3m=cur3m,m2g=m2g,retg=retg,
                vix=vix,hy=hy,ig=ig,cfnai=cfnai,ipyoy=ipyoy,sahm=sahm)

def compute_fear_greed(sig):
    """
    Fear & Greed: 0=Extreme Fear, 100=Extreme Greed.
    Five equal-weighted inputs each mapped to 0-100 scale.
    Calibrated against realistic current market ranges.
    """
    scores = []

    # 1. VIX: <12 = peak greed (100), >45 = peak fear (0)
    vix = sig["vix"]
    if vix and vix > 0:
        vix_score = max(0.0, min(100.0, (45.0 - vix) / 33.0 * 100.0))
        scores.append(vix_score)

    # 2. HY Credit Spread: <2.5 = greed (100), >9 = fear (0)
    hy = sig["hy"]
    if hy and hy > 0:
        hy_score = max(0.0, min(100.0, (9.0 - hy) / 6.5 * 100.0))
        scores.append(hy_score)

    # 3. Yield Curve 10-2Y: >2 = greed (100), <-1 = fear (0)
    cur = sig["cur"]
    cur_score = max(0.0, min(100.0, (cur + 1.0) / 3.0 * 100.0))
    scores.append(cur_score)

    # 4. Real GDP growth: >3% = greed (100), <-1% = fear (0)
    gdpg = sig["rgdpg"] if sig["rgdpg"] != 0 else sig["gdpg"]
    gdp_score = max(0.0, min(100.0, (gdpg + 1.0) / 4.0 * 100.0))
    scores.append(gdp_score)

    # 5. CPI pressure: fed funds above CPI = greed, well below = fear
    pol_gap = sig["fed"] - sig["cpi"]  # positive = real positive rates = healthy
    pol_score = max(0.0, min(100.0, 50.0 + pol_gap * 10.0))
    scores.append(pol_score)

    if not scores:
        return 50
    return round(float(np.mean(scores)))

def recession_probability(sig):
    """
    Additive rule-based recession probability 0–100.
    Each component contributes proportionally; combined max is capped at 100.
    Components: Sahm Rule (max 40), Yield Curve (max 25),
                VIX stress (max 15), HY Spread stress (max 15), CFNAI (max 10), GDP (max 10).
    """
    score = 0.0

    # Sahm Rule — strongest single predictor (0–40)
    sahm = sig["sahm"]
    if sahm is not None and sahm > 0:
        if sahm >= 0.5:   score += 40.0
        elif sahm >= 0.3: score += 20.0
        elif sahm >= 0.1: score += 8.0

    # Yield Curve — inverted = 0 historically precedes recessions (0–25)
    cur = sig["cur"]
    if cur < -1.0:        score += 25.0
    elif cur < -0.5:      score += 18.0
    elif cur < 0.0:       score += 10.0
    elif cur < 0.5:       score += 3.0

    # VIX stress — elevated vol signals deteriorating conditions (0–15)
    vix = sig["vix"]
    if vix is not None:
        if vix > 40:      score += 15.0
        elif vix > 30:    score += 10.0
        elif vix > 25:    score += 5.0
        elif vix > 20:    score += 2.0

    # HY Credit Spread — widening = financial stress (0–15)
    hy = sig["hy"]
    if hy is not None and hy > 0:
        if hy > 8:        score += 15.0
        elif hy > 6:      score += 10.0
        elif hy > 5:      score += 6.0
        elif hy > 4:      score += 3.0

    # CFNAI — below-trend activity (0–10)
    cfnai = sig["cfnai"]
    if cfnai is not None:
        if cfnai < -0.7:  score += 10.0
        elif cfnai < -0.3: score += 5.0
        elif cfnai < 0:   score += 2.0

    # Real GDP growth negative (0–10)
    gdp = sig["rgdpg"] if sig["rgdpg"] != 0 else sig["gdpg"]
    if gdp < 0:           score += 10.0
    elif gdp < 1.0:       score += 4.0

    return min(100, round(score))

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

def fmt(val,decimals=2): return "N/A" if val is None else f"{val:.{decimals}f}"
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

def fmt_price(name,p):
    if name=="BTC/USD": return f"${p:,.0f}"
    if name in("S&P 500","Nasdaq"): return f"{p:,.0f}"
    if name=="10Y Yield": return f"{p:.3f}%"
    if name=="DXY": return f"{p:.2f}"
    return f"${p:.2f}"

def make_live_chart(name, cfg, hist):
    """
    Render a candlestick/line chart from a pre-fetched history DataFrame.
    Uses solid background so fullscreen looks correct.
    Pure white axis tick labels.
    """
    if hist is None or hist.empty:
        st.caption(f"Data unavailable for {name}")
        return
    color = cfg["color"]
    has_vol  = "Volume" in hist.columns and hist["Volume"].sum() > 0
    has_ohlc = all(c in hist.columns for c in ["Open","High","Low","Close"])

    if has_vol:
        fig = make_subplots(rows=2,cols=1,shared_xaxes=True,
                            row_heights=[0.78,0.22],vertical_spacing=0.03)
        pr,vr = 1,2
    else:
        fig = go.Figure(); pr = None

    if live_type == "Candlestick" and has_ohlc:
        candle = go.Candlestick(
            x=hist.index,
            open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],
            name=name,
            increasing=dict(line=dict(color="#4ade80",width=1.5),fillcolor="rgba(74,222,128,.82)"),
            decreasing=dict(line=dict(color="#f87171",width=1.5),fillcolor="rgba(248,113,113,.82)"),
        )
        if has_vol: fig.add_trace(candle,row=pr,col=1)
        else:       fig.add_trace(candle)
    else:
        tr = go.Scatter(x=hist.index,y=hist["Close"],name=name,
                        line=dict(color=color,width=2.5),fill="tozeroy",
                        fillcolor="rgba(34,211,238,0.05)")
        if has_vol: fig.add_trace(tr,row=pr,col=1)
        else:       fig.add_trace(tr)

    if has_vol:
        vcolors=["rgba(74,222,128,.38)" if c>=o else "rgba(248,113,113,.38)"
                 for c,o in zip(hist["Close"],hist["Open"])]
        fig.add_trace(go.Bar(x=hist.index,y=hist["Volume"],name="Volume",
                             marker_color=vcolors,marker_line_width=0,showlegend=False),row=vr,col=1)

    # Solid bg so fullscreen is consistent
    fig.update_layout(
        height=500, paper_bgcolor=BG_SOLID, plot_bgcolor=BG_SOLID,
        font=dict(family=MONO,color=TCLR,size=13),
        legend=dict(bgcolor="rgba(9,20,40,.97)",bordercolor="#1f3354",
                    borderwidth=1,font=dict(size=12,color="#dde8f5")),
        margin=dict(l=16,r=20,t=52,b=14),
        hoverlabel=dict(bgcolor="#0a1428",bordercolor="#2a4060",
                        font=dict(family=MONO,size=13,color="#dde8f5")),
        title=dict(text=name,font=dict(size=15,color="#ffffff",family=MONO),x=0.01),
        xaxis_rangeslider_visible=False,
    )
    ax = dict(gridcolor=GRID,zeroline=False,linecolor="#2a4060",linewidth=1.5,
              showspikes=True,spikecolor="#3a5070",spikethickness=1)
    pt = dict(tickfont=dict(size=14,color="#ffffff",family=MONO),
              title_font=dict(size=12,color="#aaccee"))
    if has_vol:
        fig.update_xaxes(ax,**pt)
        fig.update_yaxes(ax,**pt,row=1,col=1)
        fig.update_yaxes(row=vr,col=1,gridcolor="rgba(31,51,84,.3)",zeroline=False,
                         linecolor="#1f3354",title_text="Vol",
                         title_font=dict(size=10,color="#4a7090"),
                         tickfont=dict(size=10,color="#5a8090",family=MONO))
        fig.add_shape(type="line",xref="paper",yref="paper",
                      x0=0,x1=1,y0=0.235,y1=0.235,
                      line=dict(color="#1f3354",width=1.5,dash="dot"))
    else:
        fig.update_xaxes(ax,**pt)
        fig.update_yaxes(ax,**pt)
    st.plotly_chart(fig,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📅 Macro Chart Range")
    PRESETS=["1 Month","3 Months","6 Months","1 Year","2 Years","3 Years","5 Years","Custom"]
    preset=st.selectbox("Preset range",PRESETS,index=3)
    today=date.today()
    OFFSETS={"1 Month":30,"3 Months":91,"6 Months":182,
             "1 Year":365,"2 Years":730,"3 Years":1095,"5 Years":1825}
    if preset=="Custom":
        ca,cb=st.columns(2)
        with ca: cs=st.date_input("From",value=today-timedelta(days=365),min_value=date(2000,1,1),max_value=today)
        with cb: ce=st.date_input("To",value=today,min_value=date(2000,1,1),max_value=today)
        if cs>=ce: st.error("Start must be before end."); st.stop()
        range_start=pd.Timestamp(cs); range_end=pd.Timestamp(ce)
        range_label=f"{cs.strftime('%d %b %y')} – {ce.strftime('%d %b %y')}"
    else:
        days=OFFSETS[preset]
        range_start=pd.Timestamp(today-timedelta(days=days))
        range_end=pd.Timestamp(today)
        range_label=preset

    st.divider()
    st.markdown("### 📊 Live Chart Settings")
    live_interval = st.selectbox("Candlestick interval",["1d","1wk","1mo"],index=0)
    live_type     = st.selectbox("Chart type",["Candlestick","Line"],index=0)

    st.divider()
    st.markdown("### 🔄 Data")
    st.markdown('<div class="refresh-btn">',unsafe_allow_html=True)
    if st.button("⟳  Refresh All Data",use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    st.caption("Market prices: 5 min  ·  Macro data: 60 min")

    st.divider()
    st.markdown("### ℹ About")
    st.caption("**Data:** FRED (Federal Reserve) · yfinance · Finnhub\n\n"
               "**Economic calendar:** Finnhub API (live confirmed dates)\n\n"
               "**News & Earnings:** Finnhub financial data\n\n"
               "**Clock:** Singapore Time (SGT UTC+8)\n\n"
               "**Real GDP:** BEA GDPC1 chained 2017 dollars\n\n"
               "Not financial advice.")

# ── Key guard ─────────────────────────────────────────────────────────────────
if not FRED_API_KEY:
    st.error("FRED API key missing. Add FRED_API_KEY to Streamlit secrets.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading live data feeds…"):
    raw_series, df = load_fred(FRED_API_KEY)
    etfs           = load_etfs()
    mkt            = load_market_prices()
    hl_data        = load_52w_highs()
    corr_df        = load_correlations()
    cnn_fg         = load_cnn_fear_greed()
    econ_cal       = load_econ_calendar(FINNHUB_API_KEY, FRED_API_KEY)
    fh_news        = load_finnhub_news(FINNHUB_API_KEY)
    fh_earnings    = load_finnhub_earnings(FINNHUB_API_KEY)

if not raw_series:
    st.error("Unable to load FRED data.")
    st.stop()

sig      = compute(raw_series)
dfc      = df[(df.index>=range_start)&(df.index<=range_end)]
fg_score = compute_fear_greed(sig)
rec_prob = recession_probability(sig)

if fg_score>=75:   fg_label,fg_col="EXTREME GREED","#4ade80"
elif fg_score>=55: fg_label,fg_col="GREED","#86efac"
elif fg_score>=45: fg_label,fg_col="NEUTRAL","#94a3b8"
elif fg_score>=25: fg_label,fg_col="FEAR","#fb923c"
else:              fg_label,fg_col="EXTREME FEAR","#f87171"

if rec_prob>=60:   rp_col="#f87171"; rp_lbl="HIGH"
elif rec_prob>=35: rp_col="#fb923c"; rp_lbl="ELEVATED"
elif rec_prob>=20: rp_col="#f59e0b"; rp_lbl="MODERATE"
else:              rp_col="#4ade80"; rp_lbl="LOW"

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
hc1,hc2,hc3,hc4=st.columns([3,1,1,1])
with hc1:
    st.markdown("# 📡 MACRO/SIGNAL")
    sgt_now=now_sgt()
    st.markdown(
        f'<span class="live-chip"><span class="live-dot"></span>'
        f'LIVE &nbsp;·&nbsp; {sgt_now.strftime("%d %b %Y %H:%M")} SGT</span>'
        f'&nbsp;&nbsp;<span class="range-chip">📅 {range_label}</span>',
        unsafe_allow_html=True)
with hc2:
    st.metric("Signal Conviction",f"{sig['conv']}%",
              help="How aligned are current indicators — higher = stronger directional signal")
with hc3:
    st.metric("Indicators Tracked","19")
with hc4:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("⟳ Refresh",help="Reload all live data"):
        st.cache_data.clear(); st.rerun()

st.markdown("<br>",unsafe_allow_html=True)

# ── Hero description ──────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(34,211,238,.06) 0%,rgba(167,139,250,.04) 100%);
     border:1px solid rgba(34,211,238,.2);border-radius:12px;padding:20px 24px;margin-bottom:1.5rem">
  <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;
       color:#f0f8ff;margin-bottom:10px;letter-spacing:-.01em">
    Your real-time command centre for US macro markets
  </div>
  <div style="font-size:.84rem;color:#a0bcd8;line-height:1.7;max-width:1100px">
    <strong style="color:#22d3ee">MACRO/SIGNAL</strong> tracks 19 live Federal Reserve indicators — 
    Fed Funds Rate, CPI, GDP, yield curves, credit spreads, VIX and more — and translates them into 
    <strong style="color:#c5d8f0">actionable sector rotation signals</strong> for equities. 
    It tells you which economic regime we're in right now, which sectors historically outperform in that regime, 
    and how stressed or relaxed financial conditions are. Updated hourly from official FRED data, 
    with live market prices every 5 minutes. Built for investors who want to understand 
    <em>why</em> markets move, not just that they did.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Quick-Jump Navigation ──────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:8px;background:#0b1728;border:1px solid #1f3354;
     border-radius:10px;padding:12px 18px;margin-bottom:1.6rem;align-items:center">
  <span style="font-family:'IBM Plex Mono',monospace;font-size:.63rem;font-weight:700;
    text-transform:uppercase;letter-spacing:.12em;color:#4a6080;padding-right:6px">JUMP TO</span>
  <a href="#gauges"   style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">📊 Risk Gauges</a>
  <a href="#prices"   style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">💹 Live Prices</a>
  <a href="#macro"    style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">📈 Macro KPIs</a>
  <a href="#risk"     style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">⚠️ Risk Cards</a>
  <a href="#sectors"  style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">🔄 Sectors</a>
  <a href="#calendar" style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">📅 Calendar</a>
  <a href="#charts"   style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">📉 Charts</a>
  <a href="#heatmap"  style="padding:5px 13px;border-radius:5px;background:#0f1e35;border:1px solid #2a4060;
     font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;color:#8ab4d8;text-decoration:none">🗺️ Heatmap</a>
</div>
""", unsafe_allow_html=True)

# ── Regime banner ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="regime-banner" style="border-left:4px solid {sig["col"]}">'
    f'<div class="regime-dot" style="background:{sig["col"]}"></div>'
    f'<div class="regime-name" style="color:{sig["col"]}">{sig["reg"]}</div>'
    f'<div class="regime-desc">{sig["desc"]}</div></div>',
    unsafe_allow_html=True)

with st.expander("ℹ️  What is the Market Regime?", expanded=False):
    st.markdown("""The **Market Regime** is a single-sentence summary of where the economy stands right now, 
    derived from combining interest rates, inflation, unemployment, GDP growth, and the yield curve. 
    It tells you broadly what kind of economic environment we're in — whether that's one that historically 
    favours risk-taking (stocks, growth assets) or caution (bonds, cash, defensives). 
    Think of it as the "weather forecast" for your portfolio.""")

st.markdown("<br>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FEAR & GREED  +  RECESSION PROBABILITY  +  52-WEEK TRACKER
# ─────────────────────────────────────────────────────────────────────────────
section("Sentiment & Risk Gauges", "gauges")
desc("<strong>Fear & Greed Index</strong> — a composite of five macro indicators (VIX volatility, credit spreads, "
     "yield curve, GDP growth, and policy gap) scored 0–100. Below 25 = Extreme Fear (markets panicking, "
     "historically a buying opportunity). Above 75 = Extreme Greed (complacency, elevated risk). "
     "<strong>Recession Probability</strong> is a rules-based score using six predictors "
     "with different weights — Sahm Rule (40%), yield curve (25%), VIX (15%), HY spreads (15%), "
     "CFNAI and GDP (10% combined). It is not a forecast — it reflects the current stress level of indicators.")

fg1,fg2,fg3=st.columns([1,1,2],gap="large")

with fg1:
    # Use CNN F&G if available, otherwise fall back to internal macro composite
    if cnn_fg and cnn_fg.get("value") is not None:
        display_fg    = cnn_fg["value"]
        display_label = cnn_fg["label"]
        fg_source     = "CNN Business"
    else:
        display_fg    = fg_score
        display_label = fg_label
        fg_source     = "Macro Composite"

    if display_fg >= 75:   display_col = "#4ade80"
    elif display_fg >= 55: display_col = "#86efac"
    elif display_fg >= 45: display_col = "#94a3b8"
    elif display_fg >= 25: display_col = "#fb923c"
    else:                  display_col = "#f87171"

    fig_fg=go.Figure(go.Indicator(
        mode="gauge+number",value=display_fg,
        number=dict(font=dict(size=38,color=display_col,family=MONO),suffix=""),
        gauge=dict(
            axis=dict(range=[0,100],tickwidth=1,tickcolor="#1f3354",
                      tickfont=dict(size=11,color="#6a90b0")),
            bar=dict(color=display_col,thickness=0.28),
            bgcolor="rgba(15,30,53,0)",borderwidth=0,
            steps=[
                dict(range=[0,25],   color="rgba(248,113,113,.20)"),
                dict(range=[25,45],  color="rgba(251,146,60,.13)"),
                dict(range=[45,55],  color="rgba(148,163,184,.08)"),
                dict(range=[55,75],  color="rgba(134,239,172,.13)"),
                dict(range=[75,100], color="rgba(74,222,128,.20)"),
            ],
            threshold=dict(line=dict(color=display_col,width=3),thickness=0.78,value=display_fg),
        ),
        title=dict(text=f"Fear & Greed — {fg_source}",font=dict(size=12,color="#8ab4d8",family=MONO)),
        domain=dict(x=[0,1],y=[0,1]),
    ))
    fig_fg.update_layout(height=240,paper_bgcolor=BG_SOLID,plot_bgcolor=BG_SOLID,
                         margin=dict(l=20,r=20,t=48,b=10),font=dict(family=MONO))
    st.plotly_chart(fig_fg,use_container_width=True)
    st.markdown(
        f'<div style="text-align:center;margin-top:-16px;font-family:{MONO};'
        f'font-size:.85rem;font-weight:700;color:{display_col};letter-spacing:.1em">{display_label}</div>',
        unsafe_allow_html=True)

with fg2:
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Recession Probability</div>'
        f'<div class="risk-val" style="color:{rp_col}">{rec_prob}%</div>'
        f'<div class="risk-label" style="color:{rp_col}">{rp_lbl} RISK</div>'
        f'<div class="rec-bar-wrap">'
        f'<div style="width:{rec_prob}%;height:14px;border-radius:6px;background:{rp_col}"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
        f'font-size:.63rem;color:#4a6080;margin-top:4px"><span>0%</span><span>50%</span><span>100%</span></div>'
        f'<div class="risk-sub" style="margin-top:12px">'
        f'Inputs: Sahm Rule (40%) · Yield Curve (25%) · VIX (15%) · HY Spread (15%) · CFNAI + GDP (10%)'
        f'</div></div>',
        unsafe_allow_html=True)

with fg3:
    st.markdown('<div class="chart-section-title">52-Week High / Low Position</div>',unsafe_allow_html=True)
    desc("Shows where each asset's <strong>current price sits within its 52-week range</strong>. "
         "0% = at 52-week low, 100% = at 52-week high. "
         "Assets near highs may be extended; near lows may represent value or continued weakness.")
    if hl_data:
        cols_hl=st.columns(3)
        for i,name in enumerate(list(LIVE_CHART_CONFIG.keys())[:6]):
            d=hl_data.get(name)
            if not d: continue
            with cols_hl[i%3]:
                bp=d["pct_pos"]; co=d["color"]
                ps=f"${d['price']:,.2f}" if d["price"]<10000 else f"{d['price']:,.0f}"
                st.markdown(
                    f'<div class="hl-card">'
                    f'<div class="hl-name">{name}</div>'
                    f'<div class="hl-price" style="color:{co}">{ps}</div>'
                    f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
                    f'font-size:.6rem;color:#4a6080;margin-top:6px">'
                    f'<span>52W Lo<br>{d["lo52"]:,.1f}</span>'
                    f'<span style="color:{co};font-weight:700">{bp:.0f}%ile</span>'
                    f'<span style="text-align:right">52W Hi<br>{d["hi52"]:,.1f}</span></div>'
                    f'<div class="hl-bar-bg"><div class="hl-bar-fill" style="width:{bp:.0f}%"></div></div>'
                    f'</div>',unsafe_allow_html=True)

st.markdown("<br>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# LIVE MARKET PRICES
# ─────────────────────────────────────────────────────────────────────────────
section("Live Market Prices", "prices")
desc("Real-time prices for the world's most-watched markets, updated every 5 minutes. "
     "The colour shows whether each asset is up (green) or down (red) versus the previous session's close.")

# TradingView note: yfinance refreshes every 5 minutes — good enough for macro context.
# True per-minute data requires TradingView Pro embed or a paid data vendor.
# yfinance is free, runs server-side, and is sufficient for this dashboard's purpose.
mkt_items = list(MKT_ACCENTS.items())
row1_items = mkt_items[:4]
row2_items = mkt_items[4:]

def _mkt_card(name, accent):
    data=mkt.get(name)
    price=fmt_price(name,data["price"]) if data else "—"
    pct=data["pct"] if data else 0
    cls="mkt-up" if pct>0 else "mkt-dn" if pct<0 else "mkt-flat"
    sign="+" if pct>0 else ""
    return (f'<div class="mkt-card" style="border-top:2px solid {accent}">'
            f'<div class="mkt-name">{name}</div>'
            f'<div class="mkt-price">{price}</div>'
            f'<div class="mkt-chg {cls}">{sign}{pct:.2f}%</div></div>')

mkt_row1 = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px">' + ''.join(_mkt_card(n,a) for n,a in row1_items) + '</div>'
mkt_row2 = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:0">' + ''.join(_mkt_card(n,a) for n,a in row2_items) + '</div>'
st.markdown(mkt_row1 + mkt_row2, unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# KEY MACRO INDICATORS (KPI row)
# ─────────────────────────────────────────────────────────────────────────────
section("Key Macro Indicators", "macro")
desc("These seven numbers form the backbone of the US macro picture. "
     "The <strong>green/red delta</strong> beneath each value shows change from the prior reading. "
     "<strong>Fed Funds Rate</strong> — the interest rate set by the Federal Reserve; higher = tighter money. "
     "<strong>CPI/Core CPI</strong> — inflation; Fed target is 2%. "
     "<strong>Unemployment</strong> — healthy economy typically below 5%. "
     "<strong>Yield Curve</strong> — when negative (inverted), historically signals recession within 1–2 years. "
     "<strong>Real GDP</strong> — inflation-adjusted economic growth; below 0% = contraction.")

# Row 1: monetary & inflation (4 cards)
kr1a,kr1b,kr1c,kr1d=st.columns(4)
kpi(kr1a,"Fed Funds Rate",sig["fed"],prev_val(raw_series,"fed_rate"),"FRED FEDFUNDS — monthly effective rate")
kpi(kr1b,"CPI YoY",sig["cpi"],prev_val(raw_series,"cpi_yoy"),"CPI year-over-year % change")
kpi(kr1c,"Core CPI YoY",sig["core"],prev_val(raw_series,"core_cpi_yoy"),"CPI excl. food & energy")
kpi(kr1d,"Unemployment",sig["unr"],prev_val(raw_series,"unrate"),"FRED UNRATE",inv=True)
st.markdown("<div style='margin-top:10px'></div>",unsafe_allow_html=True)
# Row 2: growth & curve (3 cards)
kr2a,kr2b,kr2c,_=st.columns(4)
kpi(kr2a,"Yield Curve 10-2Y",sig["cur"],prev_val(raw_series,"curve_10_2"),"10Y minus 2Y Treasury spread")
kpi(kr2b,"Real GDP Growth",sig["rgdpg"],prev_val(raw_series,"gdpc1_g"),"FRED GDPC1 — BEA real GDP YoY %")
kpi(kr2c,"Nominal GDP Growth",sig["gdpg"],prev_val(raw_series,"gdp_g"),"FRED GDP — nominal YoY %")
st.markdown("<br>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# RISK INDICATORS
# ─────────────────────────────────────────────────────────────────────────────
section("Risk & Activity Indicators", "risk")
desc("<strong>VIX</strong> (\"fear index\") measures how much volatility options markets expect over the next 30 days — "
     "below 15 is calm, above 30 is crisis-level fear. "
     "<strong>Credit Spreads</strong> show how much extra interest rate companies pay over government bonds — "
     "when they widen sharply, it signals investors are nervous about corporate defaults. "
     "<strong>CFNAI</strong> (Chicago Fed National Activity Index) measures US economic activity across 85 indicators; "
     "below −0.7 has historically signalled recession. "
     "<strong>Sahm Rule</strong> is a real-time recession indicator that triggers when unemployment rises "
     "0.5 percentage points above its 12-month low — it has correctly called every recession since 1970.")

r1,r2,r3,r4=st.columns(4)
with r1:
    vv=sig["vix"];vc=vix_color(vv);vl=vix_label(vv)
    vpv=prev_val(raw_series,"vix")
    vd=f"{vv-vpv:+.1f} vs prev" if vv and vpv else ""
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">VIX — Volatility Index</div>'
        f'<div class="risk-val" style="color:{vc}">{f"{vv:.1f}" if vv else "N/A"}</div>'
        f'<div class="risk-label" style="color:{vc}">{vl}</div>'
        f'<div class="risk-sub">{vd}</div>'
        f'<div class="risk-sub">CBOE · &lt;15 calm · 20–25 elevated · &gt;30 crisis</div>'
        f'</div>',unsafe_allow_html=True)
with r2:
    hyv=sig["hy"];igv=sig["ig"]
    hyc=spread_color(hyv,hy=True);igc=spread_color(igv,hy=False)
    hypv=prev_val(raw_series,"hy_spread");igpv=prev_val(raw_series,"ig_spread")
    hyd=f"{hyv-hypv:+.2f}" if hyv and hypv else ""
    igd=f"{igv-igpv:+.2f}" if igv and igpv else ""
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">Credit Spreads (ICE BofA OAS)</div>'
        f'<div class="spread-row" style="margin-top:4px"><span class="spread-name">High Yield</span>'
        f'<span class="spread-val" style="color:{hyc}">{f"{hyv:.2f}%" if hyv else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{hyd}</span></span></div>'
        f'<div class="spread-row"><span class="spread-name">Investment Grade</span>'
        f'<span class="spread-val" style="color:{igc}">{f"{igv:.2f}%" if igv else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{igd}</span></span></div>'
        f'<div class="risk-sub" style="margin-top:10px">HY &gt;6% = stress · IG &gt;1.5% = caution</div>'
        f'</div>',unsafe_allow_html=True)
with r3:
    cv=sig["cfnai"];cc=cfnai_color(cv);cl=cfnai_label(cv)
    cpv=prev_val(raw_series,"cfnai")
    cd=f"{cv-cpv:+.2f}" if cv is not None and cpv is not None else ""
    ipv=sig["ipyoy"];ipc="#4ade80" if ipv and ipv>0 else "#f87171" if ipv and ipv<0 else "#94a3b8"
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">Manufacturing Activity</div>'
        f'<div class="spread-row" style="margin-top:4px"><span class="spread-name">CFNAI (Chicago Fed)</span>'
        f'<span class="spread-val" style="color:{cc}">{f"{cv:.2f}" if cv is not None else "N/A"}'
        f'<span style="font-size:.68rem;color:#4a6080;margin-left:5px">{cd}</span></span></div>'
        f'<div class="risk-label" style="color:{cc};margin-top:4px">{cl}</div>'
        f'<div class="spread-row" style="margin-top:8px"><span class="spread-name">Industrial Production YoY</span>'
        f'<span class="spread-val" style="color:{ipc}">{f"{ipv:.1f}%" if ipv is not None else "N/A"}</span></div>'
        f'<div class="risk-sub" style="margin-top:8px">CFNAI: 0=trend · &lt;−0.7=recession risk</div>'
        f'</div>',unsafe_allow_html=True)
with r4:
    sv=sig["sahm"];sc3=sahm_color(sv)
    slbl="TRIGGERED ⚠" if sv is not None and sv>=0.5 else ("WATCH" if sv is not None and 0.3<=sv<0.5 else "Clear")
    sfill=min(100,(sv/1.0)*100) if sv is not None else 0
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">Sahm Rule Recession Indicator</div>'
        f'<div class="risk-val" style="color:{sc3}">{f"{sv:.2f}" if sv is not None else "N/A"}</div>'
        f'<div class="risk-label" style="color:{sc3}">{slbl}</div>'
        f'<div class="risk-sub" style="margin-top:10px">Triggers at 0.50 · 3m avg unemployment rise ≥0.5pp above 12m low</div>'
        f'<div style="margin-top:10px;background:#0b1525;border-radius:4px;height:8px;overflow:hidden;border:1px solid #1f3354">'
        f'<div style="width:{sfill}%;height:8px;border-radius:4px;background:{sc3}"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-family:{MONO};font-size:.64rem;color:#4a6080;margin-top:4px">'
        f'<span>0</span><span style="color:#f59e0b;font-weight:700">0.5 trigger</span><span>1.0</span></div>'
        f'</div>',unsafe_allow_html=True)

st.markdown("<br>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTOR SIGNALS + ETF TABLE
# ─────────────────────────────────────────────────────────────────────────────
section("Sector Rotation Signals & ETF Performance", "sectors")
desc("<strong>Sector Rotation</strong> refers to the idea that different parts of the economy outperform "
     "at different stages of the economic cycle. This dashboard scores each sector from −2 (Strong Underweight) "
     "to +2 (Strong Overweight) based on the combination of inflation, rates, GDP, and unemployment. "
     "The ETF table shows real performance — use it to validate whether the signals are playing out.")

# ── Signal summary cards (top 3 OW + top 3 UW) ────────────────────────────────
sorted_all = sorted(sig["sc"].items(), key=lambda x: x[1], reverse=True)
top_ow  = [(SLABELS[k], v) for k,v in sorted_all if v > 0][:3]
top_uw  = [(SLABELS[k], v) for k,v in reversed(sorted_all) if v < 0][:3]

PTXT_SHORT = {2:"Strong OW", 1:"OW", 0:"Neutral", -1:"UW", -2:"Strong UW"}
ss_html = (
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">' +
    '<div style="background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);' +
    'border-radius:8px;padding:12px 14px">' +
    '<div style="font-family:' + MONO + ';font-size:.65rem;font-weight:700;color:#4ade80;' +
    'text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">▲ Top Overweights</div>' +
    ''.join(
        f'<div style="display:flex;justify-content:space-between;padding:3px 0;'
        f'font-size:.8rem"><span style="color:#dde8f5">{nm}</span>'
        f'<span style="color:#4ade80;font-family:{MONO};font-weight:700">{PTXT_SHORT[v]}</span></div>'
        for nm,v in top_ow
    ) +
    '</div>' +
    '<div style="background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.25);' +
    'border-radius:8px;padding:12px 14px">' +
    '<div style="font-family:' + MONO + ';font-size:.65rem;font-weight:700;color:#f87171;' +
    'text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">▼ Top Underweights</div>' +
    ''.join(
        f'<div style="display:flex;justify-content:space-between;padding:3px 0;'
        f'font-size:.8rem"><span style="color:#dde8f5">{nm}</span>'
        f'<span style="color:#f87171;font-family:{MONO};font-weight:700">{PTXT_SHORT[v]}</span></div>'
        for nm,v in top_uw
    ) +
    '</div></div>'
)
st.markdown(ss_html, unsafe_allow_html=True)

left,right=st.columns([1,1.05],gap="large")
with left:
    sorted_sc=sorted(sig["sc"].items(),key=lambda x:x[1])
    fig_bar=go.Figure(go.Bar(
        x=[v for _,v in sorted_sc],y=[SLABELS[k] for k,_ in sorted_sc],
        orientation="h",
        marker=dict(color=[BCLR[v] for _,v in sorted_sc],line=dict(color="rgba(255,255,255,.05)",width=1)),
        text=[PTXT[v] for _,v in sorted_sc],textposition="outside",
        textfont=dict(family=MONO,size=10,color="#a0bcd8"),
        hovertemplate="<b>%{y}</b><br>Score: %{x}<extra></extra>",cliponaxis=False))
    fig_bar.add_vline(x=0,line_color="rgba(148,163,184,.25)",line_width=1)
    theme(fig_bar,h=390,fullscreen_bg=True)
    fig_bar.update_layout(
        xaxis=dict(range=[-3.2,3.2],tickvals=[-2,-1,0,1,2],
                   ticktext=["Strong UW","UW","Neutral","OW","Strong OW"],
                   gridcolor=GRID,tickfont=dict(size=11,color="#b8d4f0")),
        yaxis=dict(tickfont=dict(size=12,family=MONO,color="#dde8f5")),
        margin=dict(l=8,r=120,t=14,b=28))
    st.plotly_chart(fig_bar,use_container_width=True)
with right:
    if etfs:
        rows_html=""
        for e in etfs:
            sc=sig["sc"].get(e["key"],0)
            rows_html+=(f"<tr style='border-bottom:1px solid rgba(31,51,84,.6)'>"
                        f"<td style='padding:8px 8px'><span style='color:#dde8f5;font-size:.82rem;font-weight:600'>{e['label']}</span>"
                        f"<span style='color:#4a6080;font-size:.7rem;margin-left:6px'>{e['ticker']}</span></td>"
                        f"<td style='padding:8px 8px;text-align:right;color:#22d3ee;font-family:{MONO};font-size:.82rem;font-weight:700'>${e['price']}</td>"
                        f"<td style='padding:8px 8px;text-align:right'>{pct_html(e['d1'])}</td>"
                        f"<td style='padding:8px 8px;text-align:right'>{pct_html(e['m1'])}</td>"
                        f"<td style='padding:8px 8px;text-align:right'>{pct_html(e['ytd'])}</td>"
                        f"<td style='padding:8px 8px'>{pill(sc)}</td></tr>")
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}' role='table'>"
            "<thead><tr style='border-bottom:2px solid #1f3354'>"
            + "".join(
                      "<th style='padding:8px 8px;color:#8ab4d8;font-size:.7rem;font-weight:700;"
                      "text-transform:uppercase;letter-spacing:.08em;"
                      f"text-align:{align}'>{h}</th>"
                      for h,align in zip(
                          ["SECTOR","PRICE","1D","1M","YTD","SIGNAL"],
                          ["left","right","right","right","right","left"]
                      ))
            + f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True)
    else:
        st.info(
            "ETF price data is temporarily unavailable from yfinance. "
            "This is usually a rate-limit on Streamlit Cloud — click **⟳ Refresh** in the sidebar "
            "to retry, or wait a few minutes.",
            icon="ℹ️"
        )

st.markdown("<br>",unsafe_allow_html=True)
st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# ECONOMIC CALENDAR — upcoming high-impact US releases
# ─────────────────────────────────────────────────────────────────────────────
section("Upcoming Economic Releases", "calendar")
desc(
    "Live economic calendar sourced from <strong>Finnhub</strong> — confirmed dates with "
    "previous readings, consensus estimates, and actual results once published. "
    "This is the same data used by professional trading terminals. "
    "For the complete global calendar, visit "
    "<a href='https://www.marketwatch.com/economy-politics/calendar' target='_blank' "
    "style='color:#22d3ee'>MarketWatch Economic Calendar ↗</a>. "
    "<strong>High impact</strong> releases move equities, bonds and FX sharply — "
    "traders often reduce position size before these events."
)

IMPACT_CLR = {"HIGH": "#f87171", "MEDIUM": "#f59e0b", "LOW": "#94a3b8"}
IMPACT_BG  = {"HIGH": "rgba(248,113,113,.12)", "MEDIUM": "rgba(245,158,11,.09)", "LOW": "rgba(148,163,184,.07)"}
cal_source = econ_cal[0]["source"] if econ_cal else "unavailable"

if econ_cal:
    # ── Countdown strip: next 3 HIGH-impact events ──────────────────────────────
    high_evs = [e for e in econ_cal if e["impact"] == "HIGH"]
    next3    = high_evs[:3] if len(high_evs) >= 3 else econ_cal[:3]
    strip_html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px">'
    for ev in next3:
        ic  = IMPACT_CLR.get(ev["impact"], "#94a3b8")
        ibg = IMPACT_BG.get(ev["impact"], "rgba(148,163,184,.07)")
        da  = ev["days_away"]
        if da == 0:   cd = '<span style="color:#f87171;font-weight:800;font-size:.85rem">TODAY</span>'
        elif da == 1: cd = '<span style="color:#fb923c;font-weight:800;font-size:.85rem">TOMORROW</span>'
        else:         cd = f'<span style="color:#22d3ee;font-weight:700">In {da} days</span>'
        unit = ev.get("unit","")
        def _fv(v): return f"{v:+.2f}{unit}" if isinstance(v,(int,float)) else "—"
        extras = ""
        if any(ev.get(k) is not None for k in ("prev","estimate","actual")):
            act_col = "#4ade80" if ev.get("actual") is not None else "#5a7890"
            extras = (
                f'<div style="display:flex;gap:10px;margin-top:9px;font-family:{MONO};font-size:.68rem">'
                f'<span style="color:#4a6080">Prev <span style="color:#8ab4d8">{_fv(ev.get("prev"))}</span></span>'
                f'<span style="color:#4a6080">Est <span style="color:#f59e0b">{_fv(ev.get("estimate"))}</span></span>'
                f'<span style="color:#4a6080">Act <span style="color:{act_col}">{_fv(ev.get("actual"))}</span></span>'
                f'</div>'
            )
        time_lbl = f' · {ev["time_str"]} ET' if ev.get("time_str") else ""
        strip_html += (
            f'<div style="background:{ibg};border:1px solid {ic}55;border-radius:10px;'
            f'padding:16px 18px;border-left:4px solid {ic}">'
            f'<div style="font-family:{MONO};font-size:.62rem;font-weight:700;color:{ic};'
            f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">'
            f'{ev["impact"]} · {ev["source"]}</div>'
            f'<div style="font-size:.9rem;font-weight:700;color:#f0f8ff;margin-bottom:5px">{ev["name"]}</div>'
            f'<div style="font-family:{MONO};font-size:.72rem;color:#8ab4d8">'
            f'{ev["date"].strftime("%a, %d %b %Y")}{time_lbl}</div>'
            f'<div style="margin-top:6px;font-size:.75rem">{cd}</div>'
            f'{extras}'
            f'</div>'
        )
    strip_html += '</div>'
    st.markdown(strip_html, unsafe_allow_html=True)

    # ── Full table ──────────────────────────────────────────────────────────────
    st.markdown('<div class="chart-section-title">Full Release Schedule</div>', unsafe_allow_html=True)
    tbl_html = (
        f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
        "<thead><tr style='border-bottom:2px solid #1f3354'>"
    )
    for h, align in [("Date","left"),("Time ET","center"),("Release","left"),
                     ("Impact","center"),("Prev","right"),("Estimate","right"),("Actual","right")]:
        tbl_html += (f"<th style='padding:9px 8px;color:#8ab4d8;font-size:.65rem;font-weight:700;"
                     f"text-transform:uppercase;letter-spacing:.08em;text-align:{align}'>{h}</th>")
    tbl_html += "</tr></thead><tbody>"
    for ev in econ_cal:
        ic      = IMPACT_CLR.get(ev["impact"], "#94a3b8")
        badge_bg= IMPACT_BG.get(ev["impact"], "rgba(148,163,184,.07)")
        da      = ev["days_away"]
        day_col = "#f87171" if da<=1 else "#22d3ee" if da<=7 else "#8ab4d8"
        unit    = ev.get("unit","")
        def _fval(v, col="#dde8f5"):
            if v is None: return f'<span style="color:#3a5070">—</span>'
            return f'<span style="color:{col};font-weight:600">{v:+.2f}{unit}</span>' if isinstance(v,(int,float)) else f'<span style="color:{col}">{v}</span>'
        act_col = "#4ade80" if ev.get("actual") is not None else "#dde8f5"
        tbl_html += (
            f"<tr style='border-bottom:1px solid rgba(31,51,84,.5)'>"
            f"<td style='padding:9px 8px;color:{day_col};font-weight:600'>{ev['date'].strftime('%a %d %b')}</td>"
            f"<td style='padding:9px 8px;text-align:center;color:#5a7890;font-size:.71rem'>{ev.get('time_str') or '—'}</td>"
            f"<td style='padding:9px 8px;color:#f0f8ff;font-size:.83rem'>{ev['name']}</td>"
            f"<td style='padding:9px 8px;text-align:center'>"
            f"<span style='background:{badge_bg};color:{ic};border:1px solid {ic}55;"
            f"border-radius:4px;padding:2px 8px;font-size:.63rem;font-weight:700;"
            f"text-transform:uppercase'>{ev['impact']}</span></td>"
            f"<td style='padding:9px 8px;text-align:right;font-size:.77rem'>{_fval(ev.get('prev'),'#8ab4d8')}</td>"
            f"<td style='padding:9px 8px;text-align:right;font-size:.77rem'>{_fval(ev.get('estimate'),'#f59e0b')}</td>"
            f"<td style='padding:9px 8px;text-align:right;font-size:.77rem'>{_fval(ev.get('actual'),act_col)}</td>"
            f"</tr>"
        )
    tbl_html += "</tbody></table>"
    st.markdown(tbl_html, unsafe_allow_html=True)
    mw_link = "https://www.marketwatch.com/economy-politics/calendar"
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-top:10px;font-family:{MONO};font-size:.67rem;color:#4a6080">'
        f'<span>Source: <strong style="color:#8ab4d8">{cal_source}</strong> · '
        f'Refreshed hourly · {now_sgt().strftime("%d %b %Y %H:%M")} SGT</span>'
        f'<a href="{mw_link}" target="_blank" style="color:#22d3ee;text-decoration:none;'
        f'padding:4px 12px;border:1px solid rgba(34,211,238,.3);border-radius:4px">'
        f'📅 Full Calendar on MarketWatch ↗</a></div>',
        unsafe_allow_html=True,
    )
else:
    col_cal, col_link = st.columns([3,1])
    with col_cal:
        st.warning(
            "Economic calendar data is loading. Finnhub is the primary source with FRED as fallback. "
            "Click **⟳ Refresh** to retry.",
            icon="📅",
        )
    with col_link:
        st.markdown(
            f'<br><a href="https://www.marketwatch.com/economy-politics/calendar" target="_blank" '
            f'style="color:#22d3ee;font-family:{MONO};font-size:.78rem">'
            f'📅 View on MarketWatch ↗</a>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MARKET NEWS + UPCOMING EARNINGS
# ─────────────────────────────────────────────────────────────────────────────
section("Market News & Upcoming Earnings")
desc(
    "<strong>Market News</strong> headlines are sourced live from Finnhub — professional-grade "
    "news used by institutional traders. Click any headline to read the full article. "
    "<strong>Upcoming Earnings</strong> shows major S&P 500 companies reporting in the next 14 days. "
    "Big earnings (AAPL, NVDA, JPM etc.) can move the whole index and sector, not just the single stock — "
    "watch for beats vs misses against the EPS estimate shown."
)

news_col, earn_col = st.columns([3, 2], gap="large")

with news_col:
    st.markdown('<div class="chart-section-title">Latest Macro & Market Headlines (Finnhub)</div>',
                unsafe_allow_html=True)
    if fh_news:
        for item in fh_news[:9]:
            age_str = (f"{item['age_hrs']:.0f}h ago"
                       if item['age_hrs'] < 24 else f"{item['age_hrs']/24:.0f}d ago")
            url = item.get("url","#")
            st.markdown(
                f'<div style="padding:11px 0;border-bottom:1px solid rgba(31,51,84,.55)">'
                f'<a href="{url}" target="_blank" style="color:#dde8f5;text-decoration:none;'
                f'font-size:.84rem;font-weight:600;line-height:1.45;display:block">'
                f'{item["headline"]}</a>'
                f'<div style="font-family:{MONO};font-size:.65rem;color:#4a6080;margin-top:4px">'
                f'{item.get("source","")} &nbsp;·&nbsp; {age_str}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("News unavailable — Finnhub may be rate-limited. Refresh to retry.")

with earn_col:
    st.markdown('<div class="chart-section-title">Upcoming S&P 500 Earnings (Next 14 Days)</div>',
                unsafe_allow_html=True)
    if fh_earnings:
        earn_html = (
            f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
            "<thead><tr style='border-bottom:2px solid #1f3354'>"
            + "".join(
                f"<th style='padding:7px 6px;color:#8ab4d8;font-size:.62rem;"
                f"text-transform:uppercase;letter-spacing:.07em;text-align:{align}'>{h}</th>"
                for h, align in [("Symbol","left"),("Date","left"),("When","center"),("EPS Est","right")]
            )
            + "</tr></thead><tbody>"
        )
        for e in fh_earnings[:14]:
            da    = e["days_away"]
            dc    = "#f87171" if da==0 else "#fb923c" if da==1 else "#22d3ee" if da<=5 else "#8ab4d8"
            day_s = "Today" if da==0 else "Tomorrow" if da==1 else f"In {da}d"
            hour_s= " BMO" if e.get("hour")=="bmo" else " AMC" if e.get("hour")=="amc" else ""
            eps_s = f"${e['eps_est']:.2f}" if e.get("eps_est") is not None else "—"
            earn_html += (
                f"<tr style='border-bottom:1px solid rgba(31,51,84,.4)'>"
                f"<td style='padding:7px 6px;color:#22d3ee;font-weight:700;font-size:.82rem'>{e['symbol']}</td>"
                f"<td style='padding:7px 6px;color:#8ab4d8;font-size:.74rem'>{e['date'].strftime('%d %b')}</td>"
                f"<td style='padding:7px 6px;text-align:center;font-size:.72rem'>"
                f"<span style='color:{dc};font-weight:600'>{day_s}</span>"
                f"<span style='color:#4a6080;font-size:.63rem'>{hour_s}</span></td>"
                f"<td style='padding:7px 6px;text-align:right;color:#f59e0b;font-size:.78rem'>{eps_s}</td>"
                f"</tr>"
            )
        earn_html += "</tbody></table>"
        st.markdown(earn_html, unsafe_allow_html=True)
        st.caption("BMO = Before Market Open  ·  AMC = After Market Close  ·  EPS Est = consensus")
    else:
        st.caption("No major S&P 500 earnings in the next 14 days, or Finnhub data unavailable.")

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MACRO CHART TABS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div id="charts" style="position:relative;top:-70px;visibility:hidden"></div>',
    unsafe_allow_html=True)
st.markdown(
    f"### Macro Charts &nbsp;<span class='range-chip'>📅 {range_label}</span>",
    unsafe_allow_html=True)
st.caption("Use the sidebar to change the date range. Each chart supports fullscreen via ⛶.")

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8=st.tabs([
    "📈  Rates & Inflation",
    "📉  Yield Curve",
    "💼  Labour & GDP",
    "💧  Liquidity",
    "📊  VIX · Spreads · Activity",
    "🚀  Live US Markets",
    "🌏  Asia Markets",
    "🔗  Correlations",
])

# ── Tab 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    desc("<strong>Fed Funds Rate vs Inflation:</strong> When the Fed rate is above CPI, monetary policy is "
         "\"restrictive\" — actively slowing the economy to control inflation. When it's below CPI, "
         "policy is \"accommodative\" — stimulating growth. The 2% dashed line is the Fed's official inflation target. "
         "<strong>PCE</strong> (Personal Consumption Expenditures) is the Fed's preferred inflation gauge "
         "as it better captures how consumers substitute cheaper alternatives.")

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
                if fc: kw["fillcolor"]=fc
                fig1a.add_trace(go.Scatter(x=s.index,y=s.values,name=nm,**kw))
    fig1a.add_hline(y=2,line_dash="dash",line_color="rgba(148,163,184,.35)",
                    annotation_text="2% Fed target",annotation_font_size=12)
    theme(fig1a,h=400,title="Fed Funds Rate vs CPI & Core CPI",fullscreen_bg=True)
    st.plotly_chart(fig1a,use_container_width=True)

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div class="chart-section-title">PCE Inflation & 10Y Treasury Yield</div>',unsafe_allow_html=True)
    fig1b=go.Figure()
    for ck,nm,col in [("pce_yoy","PCE YoY",C["purple"]),("t10y","10Y Yield",C["teal"])]:
        if ck in dfc.columns:
            s=dfc[ck].dropna()
            if not s.empty:
                fig1b.add_trace(go.Scatter(x=s.index,y=s.values,name=nm,line=dict(color=col,width=2)))
    theme(fig1b,h=320,title="PCE Inflation & 10Y Treasury Yield",fullscreen_bg=True)
    st.plotly_chart(fig1b,use_container_width=True)

# ── Tab 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    desc("<strong>The Yield Curve</strong> plots interest rates across different maturities. "
         "Normally long-term rates are higher than short-term rates (positive spread = normal). "
         "When short-term rates exceed long-term ones (inversion, red zone), it means the market expects "
         "economic slowdown. The 10Y–2Y spread has inverted before every US recession since 1955, "
         "typically 6–18 months before the recession begins. <strong>The 10Y–3M spread</strong> is "
         "considered by the Fed to be the most reliable recession predictor of all spread pairs.")

    for ck,ttl in [("curve_10_2","10Y – 2Y Spread (Inversion Monitor)"),("curve_10_3m","10Y – 3M Spread")]:
        st.markdown(f'<div class="chart-section-title">{ttl}</div>',unsafe_allow_html=True)
        if ck in dfc.columns:
            s=dfc[ck].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.clip(lower=0).values,name="Normal",
                    fill="tozeroy",fillcolor="rgba(74,222,128,.12)",line=dict(color=C["green"],width=2)))
                f.add_trace(go.Scatter(x=s.index,y=s.clip(upper=0).values,name="Inverted",
                    fill="tozeroy",fillcolor="rgba(248,113,113,.15)",line=dict(color=C["red"],width=2)))
                f.add_hline(y=0,line_color="rgba(148,163,184,.45)",line_width=1.5,
                            annotation_text="Inversion line",annotation_font_size=12)
                theme(f,h=340,title=ttl+" (%)",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
                st.markdown("<br>",unsafe_allow_html=True)

# ── Tab 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    desc("<strong>Labour market & GDP</strong> — together these reveal whether the economy is expanding, "
         "stagnating, or contracting. A rising unemployment rate combined with slowing GDP is the classic "
         "recession combo. <strong>Housing Starts</strong> is a leading indicator: home construction slows "
         "well before the overall economy does, because people stop buying homes when they're nervous.")

    col_a,col_b=st.columns(2)
    with col_a:
        st.markdown('<div class="chart-section-title">Unemployment Rate</div>',unsafe_allow_html=True)
        if "unrate" in dfc.columns:
            s=dfc["unrate"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Unemployment",
                    line=dict(color=C["purple"],width=2),fill="tozeroy",fillcolor="rgba(167,139,250,.08)"))
                theme(f,h=300,title="US Unemployment Rate (%)",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Retail Sales Growth YoY</div>',unsafe_allow_html=True)
        if "retail_g" in dfc.columns:
            s=dfc["retail_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Retail Sales",line=dict(color=C["teal"],width=2)))
                f.add_hline(y=0,line_color="rgba(148,163,184,.35)")
                theme(f,h=300,title="Retail Sales Growth YoY (%)",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Housing Starts (HOUST)</div>',unsafe_allow_html=True)
        if "housing" in dfc.columns:
            s=dfc["housing"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Housing Starts",
                    line=dict(color=C["pink"],width=2),fill="tozeroy",fillcolor="rgba(244,114,182,.07)"))
                theme(f,h=280,title="Housing Starts — Monthly (Thousands)",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
    with col_b:
        st.markdown('<div class="chart-section-title">Real GDP Growth YoY (BEA GDPC1)</div>',unsafe_allow_html=True)
        if "gdpc1_g" in dfc.columns:
            s=dfc["gdpc1_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Bar(x=s.index,y=s.values,name="Real GDP Growth",
                    marker_color=["#4ade80" if v>=0 else "#f87171" for v in s.values],opacity=.85))
                f.add_hline(y=0,line_color="rgba(148,163,184,.35)")
                theme(f,h=300,title="Real GDP Growth YoY % — BEA Revised (GDPC1)",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Nominal GDP Growth YoY</div>',unsafe_allow_html=True)
        if "gdp_g" in dfc.columns:
            s=dfc["gdp_g"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_trace(go.Bar(x=s.index,y=s.values,name="Nominal GDP",
                    marker_color=["#86efac" if v>=0 else "#fca5a5" for v in s.values],opacity=.8))
                f.add_hline(y=0,line_color="rgba(148,163,184,.35)")
                theme(f,h=300,title="Nominal GDP Growth YoY %",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)

# ── Tab 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    desc("<strong>Liquidity</strong> refers to how much money is circulating in the economy. "
         "<strong>M2 Money Supply</strong> includes cash, savings, and money market funds — "
         "when M2 grows rapidly, there's more money chasing assets (historically bullish). "
         "When M2 shrinks (negative YoY), it has historically preceded market stress. "
         "This tab also shows the relationship between the Fed rate and the yield curve spread, "
         "helping you see how monetary policy shapes the shape of the curve.")

    st.markdown('<div class="chart-section-title">M2 Money Supply Growth YoY</div>',unsafe_allow_html=True)
    if "m2_g" in dfc.columns:
        s=dfc["m2_g"].dropna()
        if not s.empty:
            f=go.Figure()
            f.add_trace(go.Scatter(x=s.index,y=s.values,name="M2 YoY",
                line=dict(color=C["yellow"],width=2),fill="tozeroy",fillcolor="rgba(245,158,11,.07)"))
            f.add_hline(y=0,line_color="rgba(148,163,184,.35)")
            theme(f,h=340,title="M2 Money Supply Growth YoY (%)",fullscreen_bg=True)
            st.plotly_chart(f,use_container_width=True)

    st.markdown("<br>",unsafe_allow_html=True)
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
    f2.add_hline(y=0,line_color="rgba(148,163,184,.35)")
    theme(f2,h=320,title="Fed Funds Rate vs 10Y–2Y Yield Spread (%)",fullscreen_bg=True)
    st.plotly_chart(f2,use_container_width=True)

# ── Tab 5 ─────────────────────────────────────────────────────────────────────
with tab5:
    desc("<strong>VIX</strong> is the market's \"speedometer\" of fear — it spikes during crashes and collapses in calm markets. "
         "<strong>Credit Spreads</strong> widen when investors demand more compensation for lending to companies, "
         "signalling rising default fears. "
         "<strong>CFNAI</strong> aggregates 85 monthly US economic indicators into a single number; think of it "
         "as a real-time health check on the whole economy. "
         "<strong>Sahm Rule</strong> historically triggers at or just after the start of a recession — "
         "unlike lagging indicators, it's designed to be an early warning system.")

    col_x,col_y=st.columns(2)
    with col_x:
        st.markdown('<div class="chart-section-title">VIX — Live Daily (2-Year History)</div>',unsafe_allow_html=True)
        vix_hist=load_live_chart("^VIX",period="2y",interval="1d")
        if vix_hist is not None and not vix_hist.empty:
            fv=go.Figure()
            vix_vals=vix_hist["Close"]
            fv.add_trace(go.Scatter(x=vix_hist.index,y=vix_vals,name="VIX",mode="lines",
                line=dict(color=C["orange"],width=2.5),fill="tozeroy",fillcolor="rgba(251,146,60,.10)"))
            fv.add_hline(y=15,line_dash="dot",line_color="rgba(74,222,128,.45)",line_width=1,
                         annotation_text="15 low vol",annotation_font_size=12,annotation_font_color="#4ade80")
            fv.add_hline(y=20,line_dash="dash",line_color="rgba(200,220,240,.50)",line_width=1.5,
                         annotation_text="20 elevated",annotation_font_size=12,annotation_font_color="#e0eeff")
            fv.add_hline(y=30,line_dash="dash",line_color="rgba(248,113,113,.65)",line_width=1.5,
                         annotation_text="30 crisis",annotation_font_size=12,annotation_font_color="#f87171")
            fv.add_hrect(y0=30,y1=max(float(vix_vals.max())+5,40),
                         fillcolor="rgba(248,113,113,.05)",line_width=0)
            theme(fv,h=360,title="VIX — CBOE Volatility Index",fullscreen_bg=True)
            fv.update_layout(xaxis_rangeslider_visible=False)
            st.plotly_chart(fv,use_container_width=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">CFNAI</div>',unsafe_allow_html=True)
        if "cfnai" in dfc.columns:
            s=dfc["cfnai"].dropna()
            if not s.empty:
                f=go.Figure()
                f.add_hrect(y0=-0.7,y1=float(s.min())-0.05,fillcolor="rgba(248,113,113,.07)",line_width=0)
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="CFNAI",
                    line=dict(color=C["teal"],width=2),fill="tozeroy",fillcolor="rgba(45,212,191,.07)"))
                f.add_hline(y=0,line_color="rgba(148,163,184,.35)",line_width=1.5)
                f.add_hline(y=-0.7,line_dash="dash",line_color="rgba(248,113,113,.5)",
                            annotation_text="−0.7 recession risk",annotation_font_size=12)
                theme(f,h=320,title="Chicago Fed National Activity Index",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)
    with col_y:
        st.markdown('<div class="chart-section-title">Credit Spreads — HY & IG</div>',unsafe_allow_html=True)
        f=go.Figure()
        if "hy_spread" in dfc.columns:
            s=dfc["hy_spread"].dropna()
            if not s.empty: f.add_trace(go.Scatter(x=s.index,y=s.values,name="HY Spread",line=dict(color=C["red"],width=2)))
        if "ig_spread" in dfc.columns:
            s=dfc["ig_spread"].dropna()
            if not s.empty: f.add_trace(go.Scatter(x=s.index,y=s.values,name="IG Spread",line=dict(color=C["teal"],width=2,dash="dot")))
        theme(f,h=340,title="Credit Spreads — HY & IG (ICE BofA OAS, %)",fullscreen_bg=True)
        st.plotly_chart(f,use_container_width=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Sahm Rule</div>',unsafe_allow_html=True)
        if "sahm" in dfc.columns:
            s=dfc["sahm"].dropna()
            if not s.empty:
                f=go.Figure()
                maxv=max(float(s.max())+0.05,0.6)
                f.add_hrect(y0=0.5,y1=maxv,fillcolor="rgba(248,113,113,.07)",line_width=0,
                            annotation_text="Recession zone",annotation_font_size=12,annotation_font_color="#f87171")
                f.add_trace(go.Scatter(x=s.index,y=s.values,name="Sahm Rule",
                    line=dict(color=C["yellow"],width=2.5),fill="tozeroy",fillcolor="rgba(245,158,11,.08)"))
                f.add_hline(y=0.5,line_dash="dash",line_color="#f87171",line_width=2,
                            annotation_text="0.5 trigger",annotation_font_size=12)
                theme(f,h=340,title="Sahm Rule Recession Indicator",fullscreen_bg=True)
                st.plotly_chart(f,use_container_width=True)

# ── Tab 6: Live US Markets ─────────────────────────────────────────────────────
with tab6:
    desc("<strong>Live candlestick charts</strong> — each candle shows the Open, High, Low, and Close price "
         "for one period (day/week/month). Green candles mean the price closed higher than it opened; "
         "red means lower. The <strong>volume bars</strong> below show how many shares/contracts traded — "
         "high volume on a big move makes that move more significant. "
         "Use the <strong>custom date range</strong> below to zoom in on any historical period.")

    # Custom date range picker — independent of macro range
    st.markdown('<div class="chart-section-title">Custom Date Range for Live Charts</div>',unsafe_allow_html=True)
    lr1,lr2,lr3,lr4=st.columns([1,1,1,2])
    with lr1:
        live_start=st.date_input("From",value=date.today()-timedelta(days=182),
                                  min_value=date(2000,1,1),max_value=date.today(),key="live_from")
    with lr2:
        live_end=st.date_input("To",value=date.today(),
                                min_value=date(2000,1,1),max_value=date.today(),key="live_to")
    with lr3:
        st.markdown("<br>",unsafe_allow_html=True)
        use_custom_range=st.checkbox("Use custom range",value=False)
    with lr4:
        if not use_custom_range:
            quick=st.selectbox("Quick preset",["5d","1mo","3mo","6mo","1y","2y","5y","max"],index=3,key="live_quick")

    if live_start>=live_end and use_custom_range:
        st.error("Start date must be before end date.")
    else:
        c1,c2=st.columns(2)
        for col_idx,(pname,pcfg) in enumerate(LIVE_CHART_CONFIG.items()):
            with (c1 if col_idx%2==0 else c2):
                st.markdown(f'<div class="chart-section-title">{pname}</div>',unsafe_allow_html=True)
                if use_custom_range:
                    hist=load_live_chart_dates(pcfg["ticker"],
                                               live_start.strftime("%Y-%m-%d"),
                                               live_end.strftime("%Y-%m-%d"),
                                               interval=live_interval)
                else:
                    hist=load_live_chart(pcfg["ticker"],period=quick,interval=live_interval)
                make_live_chart(pname,pcfg,hist)
                if col_idx%2==1:
                    st.markdown("<br>",unsafe_allow_html=True)

# ── Tab 7: Asia Markets ────────────────────────────────────────────────────────
with tab7:
    desc("<strong>Asia-Pacific equity indices</strong> — Singapore's STI, Japan's Nikkei 225, Hong Kong's Hang Seng, "
         "Australia's ASX 200, South Korea's KOSPI, and China's CSI 300. These markets open before US markets, "
         "so they often give early clues about global risk sentiment. "
         "Strong performance in Asia often (but not always) carries over into the European and US sessions.")

    # Asia price strip
    asia_html='<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px">'
    for aname,acfg in ASIA_CHART_CONFIG.items():
        try:
            ah=yf.Ticker(acfg["ticker"]).history(period="5d")
            if not ah.empty:
                ac=ah["Close"].dropna()
                ap=float(ac.iloc[-1]); av=float(ac.iloc[-2]) if len(ac)>1 else ap
                apct=(ap-av)/av*100 if av else 0
                acls="mkt-up" if apct>0 else "mkt-dn" if apct<0 else "mkt-flat"
                asign="+" if apct>0 else ""
                asia_html+=(f'<div class="mkt-card" style="border-top:2px solid {acfg["color"]}">'
                            f'<div class="mkt-name">{aname}</div>'
                            f'<div class="mkt-price">{ap:,.1f}</div>'
                            f'<div class="mkt-chg {acls}">{asign}{apct:.2f}%</div></div>')
        except Exception: pass
    asia_html+='</div>'
    st.markdown(asia_html,unsafe_allow_html=True)

    # Asia custom range
    st.markdown('<div class="chart-section-title">Custom Date Range</div>',unsafe_allow_html=True)
    ar1,ar2,ar3,ar4=st.columns([1,1,1,2])
    with ar1: asia_start=st.date_input("From",value=date.today()-timedelta(days=182),min_value=date(2000,1,1),max_value=date.today(),key="asia_from")
    with ar2: asia_end=st.date_input("To",value=date.today(),min_value=date(2000,1,1),max_value=date.today(),key="asia_to")
    with ar3:
        st.markdown("<br>",unsafe_allow_html=True)
        asia_custom=st.checkbox("Use custom range",value=False,key="asia_custom")
    with ar4:
        if not asia_custom:
            asia_quick=st.selectbox("Quick preset",["5d","1mo","3mo","6mo","1y","2y","5y"],index=3,key="asia_quick")

    ac1,ac2=st.columns(2)
    for col_idx,(aname,acfg) in enumerate(ASIA_CHART_CONFIG.items()):
        with (ac1 if col_idx%2==0 else ac2):
            st.markdown(f'<div class="chart-section-title">{aname}</div>',unsafe_allow_html=True)
            if asia_custom and asia_start<asia_end:
                ah=load_live_chart_dates(acfg["ticker"],asia_start.strftime("%Y-%m-%d"),asia_end.strftime("%Y-%m-%d"),interval=live_interval)
            else:
                ah=load_live_chart(acfg["ticker"],period=asia_quick if not asia_custom else "6mo",interval=live_interval)
            make_live_chart(aname,acfg,ah)
            if col_idx%2==1:
                st.markdown("<br>",unsafe_allow_html=True)

# ── Tab 8: Correlations ────────────────────────────────────────────────────────
with tab8:
    desc("<strong>Correlation</strong> measures how two assets move relative to each other, on a scale from "
         "<strong>−1 to +1</strong>. "
         "+1 = they move in perfect lockstep. "
         "−1 = they move in exactly opposite directions (true diversification). "
         "0 = no relationship. For portfolio construction, assets with low or negative correlation "
         "provide genuine diversification — when one falls, the other may not. "
         "This matrix uses 6 months of daily returns. Correlations change over time — "
         "in a crash, many assets that normally diversify suddenly become correlated.")

    if corr_df is not None and not corr_df.empty and len(corr_df.columns)>=2:
        labels=list(corr_df.columns)
        z=corr_df.values.tolist()
        text=[[f"{v:.2f}" for v in row] for row in z]
        fig_corr=go.Figure(go.Heatmap(
            z=z,x=labels,y=labels,
            text=text,texttemplate="%{text}",
            textfont=dict(size=15,color="white",family=MONO),
            colorscale=[
                [0.0, "#f87171"],
                [0.4, "rgba(30,50,90,1)"],
                [0.5, "rgba(20,35,65,1)"],
                [0.6, "rgba(30,50,90,1)"],
                [1.0, "#4ade80"],
            ],
            zmid=0,zmin=-1,zmax=1,
            colorbar=dict(
                title=dict(text="Corr",font=dict(size=13,color="#8ab4d8",family=MONO)),
                tickfont=dict(size=13,color="#ffffff",family=MONO),
                thickness=16,
                tickvals=[-1,-0.5,0,0.5,1],
                ticktext=["-1.0","-0.5","0","0.5","1.0"],
            ),
            hovertemplate="<b>%{y} vs %{x}</b><br>Correlation: %{z:.2f}<extra></extra>",
        ))
        theme(fig_corr,h=520,title="6-Month Return Correlations (Daily)",fullscreen_bg=True)
        fig_corr.update_layout(margin=dict(l=70,r=90,t=70,b=70))
        fig_corr.update_xaxes(tickfont=dict(size=15,color="#ffffff",family=MONO),
                               tickangle=0,title_text="")
        fig_corr.update_yaxes(tickfont=dict(size=15,color="#ffffff",family=MONO),
                               title_text="")
        st.plotly_chart(fig_corr,use_container_width=True)

        # Key insights
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Key Correlation Insights (|r| ≥ 0.5)</div>',unsafe_allow_html=True)
        insights=[]
        for i,a in enumerate(labels):
            for j,b in enumerate(labels):
                if j<=i: continue
                v=corr_df.loc[a,b]
                if abs(v)>=0.5:
                    direction="strongly positive ↑↑" if v>=0.7 else ("positive ↑" if v>=0.5 else ("negative ↓" if v<=-0.5 else "strongly negative ↓↓"))
                    color="#4ade80" if v>0 else "#f87171"
                    insights.append((a,b,v,direction,color))
        if insights:
            ihtml=""
            for a,b,v,direction,color in sorted(insights,key=lambda x:-abs(x[2])):
                ihtml+=(f'<div class="spread-row">'
                        f'<span class="spread-name"><b style="color:#dde8f5">{a}</b> &nbsp;vs&nbsp; <b style="color:#dde8f5">{b}</b></span>'
                        f'<span class="spread-val" style="color:{color}">{v:+.2f} — {direction}</span>'
                        f'</div>')
            st.markdown(f'<div class="scorecard-wrap">{ihtml}</div>',unsafe_allow_html=True)
        else:
            st.info("No asset pairs exceed the |0.5| correlation threshold in this period — good diversification!")
    else:
        st.warning("Correlation data unavailable — this can happen when yfinance has rate-limited requests. "
                   "Click ⟳ Refresh to retry, or check your internet connection.")
        if st.button("Retry Correlation Data"):
            st.cache_data.clear(); st.rerun()

st.markdown("<br>",unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# FED RATE DECISION COUNTDOWN  +  TRADE SIGNAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
section("Fed Watch & Trade Signal Summary")
desc(
    "<strong>Fed Watch</strong> — the next FOMC meeting date (confirmed from FRED calendar) and "
    "the current Fed Funds Rate vs CPI gap, which determines whether policy is truly restrictive. "
    "<strong>Trade Signal Summary</strong> distils all 19 macro indicators into a single "
    "actionable read: <em>Risk-On</em> (expand equity exposure), <em>Neutral</em> (balanced positioning), "
    "or <em>Risk-Off</em> (rotate to defensives or cash). This is not financial advice."
)

fw1, fw2 = st.columns([1, 2], gap="large")

with fw1:
    # Next FOMC date from calendar
    fomc_event = next((e for e in econ_cal if "FOMC" in e["name"] and "Minute" not in e["name"]), None)
    real_rate  = round(sig["fed"] - sig["cpi"], 2)
    real_col   = "#4ade80" if real_rate > 0 else "#f87171"
    real_lbl   = "Restrictive" if real_rate > 0 else "Accommodative"

    fomc_html = ""
    if fomc_event:
        da  = fomc_event["days_away"]
        day_str = "Today" if da == 0 else f"{da} days"
        day_col = "#f87171" if da <= 3 else "#f59e0b" if da <= 14 else "#22d3ee"
        fomc_html = (
            f'<div style="margin-top:14px;padding-top:14px;border-top:1px solid #1f3354">'
            f'<div style="font-family:{MONO};font-size:.65rem;font-weight:700;color:#8ab4d8;'
            f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">Next FOMC Decision</div>'
            f'<div style="font-size:.95rem;font-weight:700;color:#f0f8ff">'
            f'{fomc_event["date"].strftime("%a %d %b %Y")}</div>'
            f'<div style="font-family:{MONO};font-size:.78rem;color:{day_col};font-weight:700;margin-top:3px">'
            f'In {day_str}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Fed Watch</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div>'
        f'<div style="font-size:.73rem;color:#8ab4d8;margin-bottom:3px">Fed Funds Rate</div>'
        f'<div style="font-family:{MONO};font-size:1.6rem;font-weight:700;color:#22d3ee">{sig["fed"]:.2f}%</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:.73rem;color:#8ab4d8;margin-bottom:3px">Real Rate (Fed−CPI)</div>'
        f'<div style="font-family:{MONO};font-size:1.6rem;font-weight:700;color:{real_col}">'
        f'{real_rate:+.2f}%</div>'
        f'<div style="font-family:{MONO};font-size:.7rem;color:{real_col};font-weight:700">{real_lbl}</div>'
        f'</div></div>'
        f'<div class="risk-sub">Real rate = Fed Funds minus CPI YoY. '
        f'Positive = monetary policy is truly tight and suppressing inflation. '
        f'Negative = policy is still stimulative despite rate hikes.</div>'
        f'{fomc_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

with fw2:
    # Trade Signal Score — synthesise all indicators into one read
    # Each indicator casts a vote: +1 risk-on, -1 risk-off, 0 neutral
    votes = []
    # Rates & inflation
    votes.append(+1 if sig["fed"] < 3 else (-1 if sig["fed"] > 5 else 0))
    votes.append(+1 if sig["cpi"] < 2.5 else (-1 if sig["cpi"] > 4 else 0))
    votes.append(+1 if sig["core"] < 2.5 else (-1 if sig["core"] > 3.5 else 0))
    # Growth
    gdp = sig["rgdpg"] if sig["rgdpg"] else sig["gdpg"]
    votes.append(+1 if gdp and gdp > 2 else (-1 if gdp and gdp < 0 else 0))
    # Labour
    votes.append(+1 if sig["unr"] < 4.5 else (-1 if sig["unr"] > 5.5 else 0))
    # Yield curve
    votes.append(+1 if sig["cur"] > 0.5 else (-1 if sig["cur"] < -0.3 else 0))
    # Sentiment
    votes.append(+1 if sig["vix"] < 18 else (-1 if sig["vix"] > 25 else 0))
    votes.append(+1 if sig["hy"] < 4 else (-1 if sig["hy"] > 6 else 0))
    votes.append(+1 if sig["ig"] < 1.0 else (-1 if sig["ig"] > 1.5 else 0))
    # Activity
    votes.append(+1 if sig["cfnai"] > 0 else (-1 if sig["cfnai"] < -0.7 else 0))
    votes.append(+1 if sig["retg"] and sig["retg"] > 2 else (-1 if sig["retg"] and sig["retg"] < 0 else 0))
    votes.append(+1 if sig["m2g"] and sig["m2g"] > 0 else (-1 if sig["m2g"] and sig["m2g"] < -2 else 0))
    # Recession risk
    votes.append(-2 if sig["sahm"] and sig["sahm"] >= 0.5 else (0 if sig["sahm"] and sig["sahm"] >= 0.3 else +1))

    total_votes  = sum(votes)
    max_possible = sum(abs(v) for v in votes) or 1
    score_pct    = round((total_votes / max_possible) * 100)
    ron_count    = sum(1 for v in votes if v > 0)
    roff_count   = sum(1 for v in votes if v < 0)
    neut_count   = sum(1 for v in votes if v == 0)

    if score_pct >= 35:
        ts_label, ts_col, ts_bg, ts_icon = "RISK-ON", "#4ade80", "rgba(74,222,128,.12)", "▲"
        ts_action = "Macro supports equity exposure. Favour cyclicals, growth, and commodities."
    elif score_pct <= -35:
        ts_label, ts_col, ts_bg, ts_icon = "RISK-OFF", "#f87171", "rgba(248,113,113,.12)", "▼"
        ts_action = "Macro warns of stress. Reduce risk, favour defensives, bonds, cash."
    else:
        ts_label, ts_col, ts_bg, ts_icon = "NEUTRAL", "#94a3b8", "rgba(148,163,184,.08)", "→"
        ts_action = "Mixed signals. Balanced positioning. Avoid concentrated bets."

    bar_w_on   = int(ron_count  / len(votes) * 100)
    bar_w_off  = int(roff_count / len(votes) * 100)
    bar_w_neut = 100 - bar_w_on - bar_w_off

    st.markdown(
        f'<div style="background:{ts_bg};border:1px solid {ts_col}44;border-radius:10px;'
        f'padding:20px 24px;border-left:4px solid {ts_col}">'
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">'
        f'<div style="font-family:{MONO};font-size:2.4rem;font-weight:800;color:{ts_col};line-height:1">'
        f'{ts_icon} {ts_label}</div>'
        f'<div style="font-family:{MONO};font-size:1.3rem;font-weight:700;color:{ts_col};'
        f'opacity:.7">{score_pct:+d}%</div>'
        f'</div>'
        f'<div style="font-size:.85rem;color:#c5d8f0;margin-bottom:14px">{ts_action}</div>'
        f'<div style="margin-bottom:8px">'
        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;gap:2px">'
        f'<div style="width:{bar_w_on}%;background:#4ade80;border-radius:4px 0 0 4px"></div>'
        f'<div style="width:{bar_w_neut}%;background:#4a5568"></div>'
        f'<div style="width:{bar_w_off}%;background:#f87171;border-radius:0 4px 4px 0"></div>'
        f'</div></div>'
        f'<div style="display:flex;gap:20px;font-family:{MONO};font-size:.7rem">'
        f'<span style="color:#4ade80">▲ {ron_count} Risk-On</span>'
        f'<span style="color:#94a3b8">→ {neut_count} Neutral</span>'
        f'<span style="color:#f87171">▼ {roff_count} Risk-Off</span>'
        f'</div>'
        f'<div style="margin-top:12px;font-size:.71rem;color:#4a6080;font-family:{MONO}">'
        f'Based on {len(votes)} macro indicators · Not financial advice · Educational only'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# HEATMAP + SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
section("Sector Regime Heatmap & Macro Scorecard", "heatmap")
desc("The <strong>Heatmap</strong> gives a quick visual of which sectors the macro model favours right now. "
     "The <strong>Scorecard</strong> shows every tracked indicator, its latest value, direction of change (↑↓→), "
     "and a human-readable assessment. The arrow reflects whether the indicator improved or worsened "
     "versus 3 readings ago.")

hm_col,sc_col=st.columns([1.3,1],gap="large")
with hm_col:
    st.markdown("#### Sector Heatmap")
    cells="".join(
        f'<div class="hm-cell" style="background:{HMBG[v]};border:1px solid {HMCL[v]}40">'
        f'<div class="hm-name" style="color:{HMCL[v]}">{SLABELS[k]}</div>'
        f'<div class="hm-sig" style="color:{HMCL[v]}">{PTXT[v]}</div></div>'
        for k,v in sig["sc"].items())
    st.markdown(f'<div class="hm-grid">{cells}</div>',unsafe_allow_html=True)
with sc_col:
    st.markdown("#### Macro Scorecard")
    sc_data=[
        ("Fed Funds","fed_rate","fed","Tight" if sig["fed"]>4 else "Easy" if sig["fed"]<2 else "Neutral"),
        ("CPI YoY","cpi_yoy","cpi","Hot" if sig["cpi"]>4 else "Elevated" if sig["cpi"]>2.5 else "Anchored"),
        ("Core CPI","core_cpi_yoy","core","Sticky" if sig["core"]>3 else "Softening"),
        ("Unemployment","unrate","unr","Tight" if sig["unr"]<4.5 else "Loose"),
        ("Real GDP Growth","gdpc1_g","rgdpg","Expanding" if sig["rgdpg"] and sig["rgdpg"]>2 else "Slowing"),
        ("Nominal GDP","gdp_g","gdpg","Expanding" if sig["gdpg"] and sig["gdpg"]>2 else "Slowing"),
        ("Yield Curve","curve_10_2","cur","Inverted ⚠" if sig["cur"]<0 else "Normal"),
        ("VIX","vix","vix",vix_label(sig["vix"])),
        ("HY Spread","hy_spread","hy","Stressed ⚠" if sig["hy"] and sig["hy"]>6 else "Normal"),
        ("IG Spread","ig_spread","ig","Elevated ⚠" if sig["ig"] and sig["ig"]>1.5 else "Normal"),
        ("CFNAI","cfnai","cfnai",cfnai_label(sig["cfnai"])),
        ("Indust. Prod YoY","ipman_yoy","ipyoy","Expanding" if sig["ipyoy"] and sig["ipyoy"]>0 else "Contracting"),
        ("Sahm Rule","sahm","sahm","Triggered ⚠" if sig["sahm"] and sig["sahm"]>=0.5 else "Watch" if sig["sahm"] and sig["sahm"]>=0.3 else "Clear"),
        ("M2 Growth","m2_g","m2g","Contracting ⚠" if sig["m2g"] and sig["m2g"]<0 else "Expanding"),
        ("Retail Sales","retail_g","retg","Strong" if sig["retg"] and sig["retg"]>4 else "Resilient"),
    ]
    rows="".join(
        f'<div class="sc-row"><span class="sc-label">{lbl}</span>'
        f'<span class="sc-val">{fmt(sig.get(sk))}</span>'
        f'<span style="color:{trend_arrow(raw_series,ck)[1]};font-size:.95rem;text-align:center;font-weight:700">{trend_arrow(raw_series,ck)[0]}</span>'
        f'<span class="sc-read">{rd}</span></div>'
        for lbl,ck,sk,rd in sc_data)
    st.markdown(f'<div class="scorecard-wrap">{rows}</div>',unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>",unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)
sgt_f=now_sgt()
st.markdown(
    f'<div style="display:flex;justify-content:space-between;padding-top:16px;'
    f'border-top:1px solid #1f3354;margin-top:0.5rem;flex-wrap:wrap;gap:8px">'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080">'
    f'Data: FRED · yfinance · Last loaded: {sgt_f.strftime("%d %b %Y %H:%M")} SGT</span>'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080">'
    f'Educational use only — not financial advice — all signals are informational</span>'
    f'<span style="font-family:{MONO};font-size:.7rem;color:#4a6080">MACRO/SIGNAL v10.0 · {sgt_f.year}</span>'
    f'</div>',unsafe_allow_html=True)
