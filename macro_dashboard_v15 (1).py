# MACRO/SIGNAL Dashboard v15.0
# Install: pip install streamlit pandas plotly fredapi yfinance pytz requests
# Run:     streamlit run macro_dashboard_v15.py
# v15.0: emoji-free UI, Singapore Hub enhanced, Crypto & Volatility separated
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

st.set_page_config(page_title="MACRO/SIGNAL", page_icon=":satellite_antenna:",
                   layout="wide", initial_sidebar_state="expanded")

APP_BG = "#060b14"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Space Grotesk',sans-serif;background:{APP_BG}!important;color:#dde8f5!important}}
.stApp{{background:{APP_BG}!important}}
.main .block-container{{padding:1.5rem 2rem 2.5rem;max-width:1820px}}
p,span,div{{color:#dde8f5}}

/* ── Sidebar ── */
[data-testid="stSidebar"]{{background:#07101e!important;border-right:1px solid #162236}}
[data-testid="stSidebar"] *{{color:#c5d8f0!important}}
[data-testid="stSidebar"] label{{font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.1em;color:#5a80a0!important}}
[data-testid="stSidebar"] .stMarkdown p{{color:#6a90b0!important;font-size:.75rem!important}}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"]>div{{background:#0c1a2e!important;border:1px solid #1f3354!important;color:#dde8f5!important;font-family:'IBM Plex Mono',monospace!important}}
[data-testid="stSidebar"] .stDateInput input{{background:#0c1a2e!important;border:1px solid #1f3354!important;color:#dde8f5!important}}
[data-testid="stSidebar"] svg{{fill:#6a90b0!important}}
[data-testid="stSidebar"] .stRadio label{{font-family:'Space Grotesk',sans-serif!important;font-size:.85rem!important;font-weight:500!important;text-transform:none!important;letter-spacing:0!important;color:#c5d8f0!important}}
[data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p{{color:#c5d8f0!important;font-size:.85rem!important}}

/* ── Metrics ── */
[data-testid="stMetric"]{{background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:.85rem 1.1rem;position:relative;overflow:hidden}}
[data-testid="stMetric"]::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#22d3ee,#a78bfa)}}
[data-testid="stMetricLabel"]{{color:#6a90b0!important;font-size:.68rem!important;font-family:'IBM Plex Mono',monospace!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.1em}}
[data-testid="stMetricValue"]{{color:#f0f8ff!important;font-size:1.4rem!important;font-weight:700!important;font-family:'IBM Plex Mono',monospace!important}}
[data-testid="stMetricDelta"]{{font-family:'IBM Plex Mono',monospace!important;font-size:.73rem!important;font-weight:600!important}}

/* ── Tabs ── */
[data-testid="stTabs"] button{{font-family:'IBM Plex Mono',monospace!important;font-size:.7rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.08em;color:#6a90b0!important;padding:.5rem .9rem!important}}
[data-testid="stTabs"] button:hover{{color:#c5d8f0!important;background:rgba(34,211,238,.06)!important}}
[data-testid="stTabs"] button[aria-selected="true"]{{color:#22d3ee!important;font-weight:700!important}}
.stTabs [data-baseweb="tab-border"]{{background:#162236!important}}
.stTabs [data-baseweb="tab-highlight"]{{background:#22d3ee!important;height:2px!important}}

/* ── Buttons ── */
.stButton>button{{background:#0c1a2e!important;border:1px solid #1f3354!important;color:#a0bcd8!important;font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.06em;border-radius:5px!important;padding:.38rem .9rem!important;transition:all .15s}}
.stButton>button:hover{{background:#22d3ee!important;color:{APP_BG}!important;border-color:#22d3ee!important}}
.refresh-btn>button{{background:rgba(34,211,238,.08)!important;border:1px solid rgba(34,211,238,.35)!important;color:#22d3ee!important}}
.refresh-btn>button:hover{{background:#22d3ee!important;color:{APP_BG}!important}}

/* ── Global type ── */
h1{{font-family:'Space Grotesk',sans-serif!important;font-weight:800!important;font-size:1.75rem!important;color:#f0f8ff!important;letter-spacing:-.02em;margin-bottom:.2rem!important}}
h2{{color:#dde8f5!important;font-weight:700!important;font-size:1.1rem!important}}
h3{{font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;font-weight:700!important;color:#6a90b0!important;text-transform:uppercase;letter-spacing:.14em}}
hr{{border:none!important;border-top:1px solid #162236!important;margin:.5rem 0!important}}
[data-testid="stAlert"]{{background:#0c1a2e!important;border:1px solid #1f3354!important;border-radius:6px;font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important}}
::-webkit-scrollbar{{width:4px}}::-webkit-scrollbar-track{{background:#07101e}}::-webkit-scrollbar-thumb{{background:#1f3354;border-radius:2px}}
button[title="View fullscreen"],button[data-testid="StyledFullScreenButton"]{{background:#0c1a2e!important;border:1px solid #1f3354!important;color:#a0bcd8!important;border-radius:4px!important}}
button[title="View fullscreen"]:hover,button[data-testid="StyledFullScreenButton"]:hover{{background:#22d3ee!important;color:{APP_BG}!important}}

/* ── Section separator ── */
.sec-sep{{display:flex;align-items:center;gap:14px;margin:2rem 0 1.2rem}}
.sec-sep-line{{flex:1;height:1px;background:linear-gradient(90deg,#1f3354,transparent)}}
.sec-sep-label{{font-family:'IBM Plex Mono',monospace;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.18em;color:#2a4a6a;white-space:nowrap}}
.sec-sep-accent{{width:32px;height:2px;background:linear-gradient(90deg,#22d3ee,#a78bfa);border-radius:1px;flex-shrink:0}}

/* ── Page header ── */
.page-header{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding-bottom:14px;border-bottom:1px solid #162236;margin-bottom:1.4rem}}
.page-title{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:800;color:#f0f8ff;letter-spacing:-.01em}}
.page-subtitle{{font-family:'IBM Plex Mono',monospace;font-size:.68rem;color:#4a6a8a;margin-top:3px}}

/* ── Regime banner ── */
.regime-banner{{display:flex;align-items:center;gap:12px;background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:12px 18px}}
.regime-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.regime-name{{font-family:'IBM Plex Mono',monospace;font-size:.84rem;font-weight:700;letter-spacing:.07em}}
.regime-desc{{font-size:.8rem;color:#8ab4d8;margin-left:auto;text-align:right;max-width:460px}}

/* ── Chips ── */
.live-chip{{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.25);font-family:'IBM Plex Mono',monospace;font-size:.65rem;font-weight:700;color:#22d3ee}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:#22d3ee;display:inline-block;animation:blink 1.8s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
.range-chip{{display:inline-block;padding:4px 11px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.67rem;font-weight:600;background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.25);color:#22d3ee}}
.page-chip{{display:inline-block;padding:3px 10px;border-radius:3px;font-family:'IBM Plex Mono',monospace;font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.3);color:#a78bfa}}

/* ── Pills ── */
.sig-pill{{display:inline-block;padding:3px 9px;border-radius:3px;font-family:'IBM Plex Mono',monospace;font-size:.67rem;font-weight:700;letter-spacing:.04em}}
.sow{{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.35)}}
.ow{{background:rgba(134,239,172,.12);color:#86efac;border:1px solid rgba(134,239,172,.3)}}
.n{{background:rgba(148,163,184,.1);color:#94a3b8;border:1px solid rgba(148,163,184,.25)}}
.uw{{background:rgba(252,165,165,.12);color:#fca5a5;border:1px solid rgba(252,165,165,.3)}}
.suw{{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.35)}}

/* ── Cards ── */
.risk-card{{background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:16px;height:100%}}
.risk-title{{font-family:'IBM Plex Mono',monospace;font-size:.65rem;font-weight:700;color:#6a90b0;text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px}}
.risk-val{{font-family:'IBM Plex Mono',monospace;font-size:1.9rem;font-weight:700;line-height:1}}
.risk-label{{font-family:'IBM Plex Mono',monospace;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-top:4px}}
.risk-sub{{font-size:.71rem;color:#4a6a8a;margin-top:7px;font-weight:500;line-height:1.55}}

/* ── Spreads ── */
.spread-row{{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(22,34,54,.8)}}
.spread-row:last-child{{border-bottom:none}}
.spread-name{{font-size:.77rem;color:#8ab4d8;font-weight:500}}
.spread-val{{font-family:'IBM Plex Mono',monospace;font-size:.85rem;font-weight:700}}

/* ── Market ticker ── */
.mkt-card{{background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:12px 14px;position:relative;overflow:hidden}}
.mkt-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.mkt-name{{font-family:'IBM Plex Mono',monospace;font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#6a90b0;margin-bottom:6px}}
.mkt-price{{font-family:'IBM Plex Mono',monospace;font-size:1.08rem;font-weight:700;color:#f0f8ff}}
.mkt-chg{{font-family:'IBM Plex Mono',monospace;font-size:.71rem;font-weight:700;margin-top:3px}}
.mkt-up{{color:#4ade80}}.mkt-dn{{color:#f87171}}.mkt-flat{{color:#94a3b8}}

/* ── Chart section titles ── */
.chart-section-title{{font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:700;color:#6a90b0;text-transform:uppercase;letter-spacing:.14em;padding:6px 0 5px;border-bottom:1px solid #162236;margin-bottom:10px}}

/* ── Heatmap ── */
.hm-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
.hm-cell{{border-radius:6px;padding:10px 8px;text-align:center}}
.hm-name{{font-size:.74rem;font-weight:600;margin-bottom:4px}}
.hm-sig{{font-family:'IBM Plex Mono',monospace;font-size:.69rem;font-weight:700}}

/* ── Scorecard ── */
.scorecard-wrap{{background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:14px 16px}}
.sc-row{{display:grid;grid-template-columns:140px 72px 22px 1fr;gap:5px;align-items:center;padding:6px 0;border-bottom:1px solid rgba(22,34,54,.8)}}
.sc-row:last-child{{border-bottom:none}}
.sc-label{{color:#8ab4d8;font-family:'IBM Plex Mono',monospace;font-size:.69rem}}
.sc-val{{color:#22d3ee;font-family:'IBM Plex Mono',monospace;font-size:.75rem;font-weight:700;text-align:right}}
.sc-read{{color:#4a6a8a;font-size:.68rem}}

/* ── Misc ── */
.rec-bar-wrap{{background:#080f1c;border-radius:5px;height:12px;overflow:hidden;border:1px solid #162236;margin-top:8px}}
.hl-card{{background:#0c1a2e;border:1px solid #162236;border-radius:7px;padding:10px 12px}}
.hl-name{{font-family:'IBM Plex Mono',monospace;font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#6a90b0;margin-bottom:5px}}
.hl-price{{font-family:'IBM Plex Mono',monospace;font-size:1rem;font-weight:700;color:#f0f8ff}}
.hl-bar-bg{{background:#0f1e35;border-radius:3px;height:5px;margin-top:6px}}
.hl-bar-fill{{height:5px;border-radius:3px;background:linear-gradient(90deg,#f87171,#f59e0b,#4ade80)}}
.desc-box{{background:rgba(34,211,238,.03);border:1px solid rgba(34,211,238,.12);border-radius:7px;padding:10px 14px;margin-bottom:14px}}
.desc-box p{{color:#8ab4d8!important;font-size:.78rem!important;line-height:1.6;margin:0}}
.desc-box strong{{color:#22d3ee!important}}

/* ── Traffic light ── */
.tl-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.tl-card{{background:#0c1a2e;border:1px solid #162236;border-radius:7px;padding:12px 14px;position:relative;overflow:hidden}}
.tl-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0}}
.tl-label{{font-family:'IBM Plex Mono',monospace;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#6a90b0;margin-bottom:4px}}
.tl-val{{font-family:'IBM Plex Mono',monospace;font-size:.95rem;font-weight:700}}
.tl-read{{font-size:.7rem;margin-top:3px}}

/* ── Momentum bar ── */
.mom-bar{{height:6px;border-radius:3px;background:#0f1e35;overflow:hidden;margin:4px 0}}
.mom-fill{{height:6px;border-radius:3px}}

/* ── Nav page active ── */
.nav-page-active{{color:#22d3ee!important;font-weight:700!important}}
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

def sep(label="", accent_color="#22d3ee"):
    """Styled section separator with accent line — replaces st.divider() + br combos."""
    st.markdown(
        f'<div class="sec-sep">'
        f'<div class="sec-sep-accent" style="background:linear-gradient(90deg,{accent_color},#a78bfa)"></div>'
        f'<div class="sec-sep-label">{label}</div>'
        f'<div class="sec-sep-line"></div>'
        f'</div>',
        unsafe_allow_html=True
    )

def section(label, anchor="", chip=""):
    if anchor:
        st.markdown(f'<div id="{anchor}" style="position:relative;top:-60px;visibility:hidden"></div>',
                    unsafe_allow_html=True)
    chip_html = f'&nbsp;<span class="page-chip">{chip}</span>' if chip else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
        f'<div style="width:3px;height:20px;background:linear-gradient(180deg,#22d3ee,#a78bfa);'
        f'border-radius:2px;flex-shrink:0"></div>'
        f'<span style="font-family:\'Space Grotesk\',sans-serif;font-size:.98rem;font-weight:700;'
        f'color:#dde8f5">{label}</span>{chip_html}'
        f'</div>',
        unsafe_allow_html=True
    )

def desc(text):
    st.markdown(f'<div class="desc-box"><p>{text}</p></div>', unsafe_allow_html=True)

def page_header(title, subtitle="", right_html=""):
    sgt_now = now_sgt()
    live_html = (
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
        f'<span class="live-chip"><span class="live-dot"></span>LIVE &nbsp;·&nbsp; '
        f'{sgt_now.strftime("%d %b %Y %H:%M")} SGT</span>'
        f'<span class="range-chip">📅 {range_label}</span>'
        f'{right_html}</div>'
    )
    st.markdown(
        f'<div class="page-header">'
        f'<div><div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div></div>'
        f'{live_html}'
        f'</div>',
        unsafe_allow_html=True
    )

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
    "STI":  "^STI",
    "SGD":  "SGD=X",
}

# ── Singapore-specific tickers ────────────────────────────────────────────────
SGX_BANKS = {
    "DBS Group":  ("D05.SI",  "#22d3ee"),
    "OCBC Bank":  ("O39.SI",  "#4ade80"),
    "UOB":        ("U11.SI",  "#a78bfa"),
}
SGX_BLUE_CHIPS = {
    # Major STI constituents (non-bank, non-REIT)
    "Singtel":          ("Z74.SI",   "#f59e0b"),
    "CapitaLand Invmt": ("9CI.SI",   "#fb923c"),
    "Wilmar Intl":      ("F34.SI",   "#86efac"),
    "Jardine C&C":      ("C07.SI",   "#f472b6"),
    "ST Engineering":   ("S63.SI",   "#2dd4bf"),
    "Keppel Corp":      ("BN4.SI",   "#94a3b8"),
    "Genting Singapore":("G13.SI",   "#22d3ee"),
    "Thai Beverage":    ("Y92.SI",   "#a78bfa"),
    "Venture Corp":     ("V03.SI",   "#4ade80"),
    "ComfortDelGro":    ("C52.SI",   "#f87171"),
    "SIA (Airlines)":   ("C6L.SI",   "#fbbf24"),
    "Sembcorp Ind":     ("U96.SI",   "#34d399"),
}
SGX_REITS = {
    "CapitaLand Int'l":  ("C38U.SI", "#22d3ee"),
    "Mapletree Pan-Asia":("N2IU.SI", "#4ade80"),
    "Mapletree Ind":     ("ME8U.SI", "#a78bfa"),
    "Ascendas REIT":     ("A17U.SI", "#f59e0b"),
    "Frasers Centrepoint":("J69U.SI","#fb923c"),
    "Suntec REIT":       ("T82U.SI", "#86efac"),
    "Keppel REIT":       ("K71U.SI", "#f472b6"),
    "Parkway Life REIT": ("C2PU.SI", "#2dd4bf"),
    "Frasers Log & Comm":("BUOU.SI", "#94a3b8"),
    "ESR-LOGOS REIT":    ("J91U.SI", "#f87171"),
}

# ── Crypto tickers ────────────────────────────────────────────────────────────
CRYPTO_TICKERS = {
    "Bitcoin":  ("BTC-USD",  "#f59e0b"),
    "Ethereum": ("ETH-USD",  "#a78bfa"),
    "Solana":   ("SOL-USD",  "#4ade80"),
    "BNB":      ("BNB-USD",  "#f59e0b"),
    "XRP":      ("XRP-USD",  "#22d3ee"),
}

# ── FRED PMI proxies (ISM Manufacturing = US PMI proxy) ──────────────────────
FRED_PMI = {
    "US Mfg PMI (ISM)":  "MANEMP",   # manufacturing employment proxy
    "US Services (NMI)": "NMFCI",    # non-mfg composite
}

# ── Market session schedule (UTC hours) ──────────────────────────────────────
MARKET_SESSIONS = {
    "SGX":       {"open": (1, 30),  "close": (9, 0),   "color": "#22d3ee",  "tz": "Asia/Singapore"},
    "Tokyo":     {"open": (0, 0),   "close": (6, 0),   "color": "#f59e0b",  "tz": "Asia/Tokyo"},
    "London":    {"open": (8, 0),   "close": (16, 30), "color": "#a78bfa",  "tz": "Europe/London"},
    "New York":  {"open": (13, 30), "close": (20, 0),  "color": "#f87171",  "tz": "America/New_York"},
    "Frankfurt": {"open": (8, 0),   "close": (16, 30), "color": "#86efac",  "tz": "Europe/Berlin"},
    "Hong Kong": {"open": (1, 30),  "close": (8, 0),   "color": "#fb923c",  "tz": "Asia/Hong_Kong"},
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



@st.cache_data(ttl=300, show_spinner=False)
def load_yield_curve(fred_api_key=""):
    """
    Fetch the full US Treasury yield curve: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y.
    PRIMARY: FRED DGS series (most reliable, business-day lag ~1 day).
    FALLBACK: yfinance Treasury proxies for real-time approximate values.
    Returns (curve_today, curve_1w) — dicts of {maturity_label: yield_pct}.
    Also returns curve_hist: dict of {label: pd.Series} for sparklines.
    """
    FRED_CURVE = {
        "1M":  "DGS1MO",
        "3M":  "DGS3MO",
        "6M":  "DGS6MO",
        "1Y":  "DGS1",
        "2Y":  "DGS2",
        "3Y":  "DGS3",
        "5Y":  "DGS5",
        "7Y":  "DGS7",
        "10Y": "DGS10",
        "20Y": "DGS20",
        "30Y": "DGS30",
    }
    # yfinance fallback tickers (fewer maturities but real-time)
    YF_CURVE = {
        "3M":  "^IRX",
        "5Y":  "^FVX",
        "10Y": "^TNX",
        "30Y": "^TYX",
    }
    today = date.today()
    start = today - timedelta(days=45)  # 45 days to get ≥ 6 business days for 1w compare
    import requests as _req
    curve_today = {}
    curve_1w    = {}
    curve_hist  = {}  # 30-day history for sparkline

    # ── Primary: FRED ─────────────────────────────────────────────────────────
    fred_ok = bool(fred_api_key)
    if fred_ok:
        for label, series_id in FRED_CURVE.items():
            try:
                url = (f"https://api.stlouisfed.org/fred/series/observations"
                       f"?series_id={series_id}"
                       f"&observation_start={start.strftime('%Y-%m-%d')}"
                       f"&api_key={fred_api_key}&file_type=json&sort_order=desc&limit=25")
                r = _req.get(url, timeout=8)
                if r.status_code != 200:
                    continue
                obs = [o for o in r.json().get("observations", []) if o.get("value", ".") != "."]
                if obs:
                    curve_today[label] = round(float(obs[0]["value"]), 3)
                if len(obs) >= 6:
                    curve_1w[label] = round(float(obs[5]["value"]), 3)
                # Build sparkline series (last 20 obs, chronological)
                if len(obs) >= 3:
                    hist_vals = [(o["date"], round(float(o["value"]), 3)) for o in reversed(obs[:20])]
                    idx  = pd.to_datetime([d for d, _ in hist_vals])
                    vals = [v for _, v in hist_vals]
                    curve_hist[label] = pd.Series(vals, index=idx)
            except Exception:
                pass

    # ── Fallback: yfinance for any missing maturities ─────────────────────────
    for label, ticker in YF_CURVE.items():
        if label in curve_today:
            continue  # already have it from FRED
        try:
            h = yf.Ticker(ticker).history(period="1mo")
            if h.empty:
                continue
            c = h["Close"].dropna()
            # ^IRX, ^FVX, ^TNX, ^TYX are quoted as percent already
            now  = round(float(c.iloc[-1]), 3)
            curve_today[label] = now
            if len(c) >= 6:
                curve_1w[label] = round(float(c.iloc[-6]), 3)
        except Exception:
            pass

    return curve_today, curve_1w, curve_hist


@st.cache_data(ttl=300, show_spinner=False)
def load_options_sentiment():
    """
    CBOE Put/Call ratios and VIX term structure.
    - Equity Put/Call: ^PCCE  (equity options only — most sentiment-pure)
    - Index  Put/Call: ^PCCR  (index options — hedging dominated)
    - Total  Put/Call: ^CPC   (combined)
    - VIX term: ^VIX (30d implied vol), ^VIX3M (93d), ^VXMT (6m, more stable)
    Contango  (VIX < VIX3M) = calm/normal expectations.
    Backwardation (VIX > VIX3M) = near-term stress — professional short-term alert.

    Reading guide:
      Equity P/C > 0.80 = high fear / potential contrarian buy
      Equity P/C < 0.55 = complacency / potential caution
      Total  P/C > 1.00 = institutional hedging surge
    """
    TICKERS = {
        "VIX":    "^VIX",
        "VIX3M":  "^VIX3M",
        "VIX6M":  "^VXMT",    # Mid-Term VIX, 6M implied vol — more reliable than ^VIXMO
        "PC_EQ":  "^PCCE",    # equity put/call — best sentiment gauge
        "PC_TOT": "^CPC",     # total put/call
        "PC_IDX": "^PCCR",    # index put/call
    }
    result = {}
    hist_30d = {}
    for label, ticker in TICKERS.items():
        try:
            h = yf.Ticker(ticker).history(period="3mo")
            if not h.empty:
                c = h["Close"].dropna()
                result[label] = round(float(c.iloc[-1]), 3)
                # Store 30-day history for charts
                if label in ("VIX", "VIX3M", "VIX6M", "PC_EQ", "PC_TOT"):
                    hist_30d[label] = c.tail(30)
        except Exception:
            pass
    return result, hist_30d


@st.cache_data(ttl=600, show_spinner=False)
def load_commodities():
    """
    Live commodity prices + key institutional ratios.
    Gold, Silver, Oil WTI, Oil Brent, Copper, Natural Gas, Wheat, Coffee.

    Key ratios watched by institutional macro traders:
    - Copper/Gold ratio: Leading global growth indicator. Rising = global demand expanding (risk-on).
      Copper is the most economically-sensitive metal; gold is a safe-haven.
      When copper rises vs gold, markets expect growth — it often leads equities by 6+ weeks.
    - Oil/Gold ratio: Energy demand vs safety demand. Rising = reflationary environment.
    - Gold/Silver ratio: Fear barometer. Above 80x = elevated uncertainty.
      In 2020 it hit 125x (peak fear); historically 40–60x in stable periods.
    """
    COMM = {
        "Gold":       ("GC=F",  "$/oz",    "#fbbf24"),
        "Silver":     ("SI=F",  "$/oz",    "#94a3b8"),
        "Oil WTI":    ("CL=F",  "$/bbl",   "#fb923c"),
        "Oil Brent":  ("BZ=F",  "$/bbl",   "#f59e0b"),
        "Copper":     ("HG=F",  "$/lb",    "#e879f9"),
        "Nat Gas":    ("NG=F",  "$/MMBtu", "#4ade80"),
        "Wheat":      ("ZW=F",  "c/bu",    "#86efac"),
        "Coffee":     ("KC=F",  "c/lb",    "#a78bfa"),
    }
    results  = {}
    hist_6mo = {}  # 6-month daily price history for charts
    for name, (ticker, unit, color) in COMM.items():
        try:
            h = yf.Ticker(ticker).history(period="6mo")
            if h.empty:
                continue
            c = h["Close"].dropna()
            c.index = pd.to_datetime(c.index)
            if c.index.tz is not None:
                c.index = c.index.tz_localize(None)
            now   = float(c.iloc[-1])
            prev  = float(c.iloc[-2]) if len(c) > 1 else now
            m1    = float(c.iloc[-22]) if len(c) > 22 else float(c.iloc[0])
            start_yr = c[c.index >= pd.Timestamp(f"{datetime.today().year}-01-01")]
            yr_start = float(start_yr.iloc[0]) if len(start_yr) > 0 else float(c.iloc[0])
            pct_1d = (now - prev) / prev * 100 if prev else 0
            pct_1m = (now - m1)   / m1   * 100 if m1   else 0
            pct_ytd= (now - yr_start) / yr_start * 100 if yr_start else 0
            results[name] = dict(
                price=round(now, 2), pct=round(pct_1d, 2),
                pct_1m=round(pct_1m, 2), pct_ytd=round(pct_ytd, 2),
                unit=unit, color=color, ticker=ticker
            )
            hist_6mo[name] = c  # store full history
        except Exception:
            pass
    return results, hist_6mo


@st.cache_data(ttl=600, show_spinner=False)
def load_global_macro_snapshot():
    """
    G10 central bank rates (via FRED), major FX pairs, and global equity indices.
    Provides the institutional 'morning briefing' world macro view.

    FRED series notes:
    - Fed:  FEDFUNDS (monthly, but most current)
    - ECB:  ECBDFR (ECB deposit facility rate)
    - BoE:  BOERUKQ → use IUDSOIA (SONIA overnight, proxy for BoE)
    - BoJ:  IRSTCI01JPM156N (short-term rate)
    - BoC:  CACOCR (Bank of Canada overnight)
    - RBA:  RBATCTR (RBA cash rate target)
    - RBNZ: RBNZOCR (OCR — correct series)
    - SNB:  IRSTCI01CHM156N (Swiss short rate proxy)
    """
    import requests as _req

    CB_RATES = {
        "🇺🇸 Fed (US)":     "FEDFUNDS",
        "🇪🇺 ECB":           "ECBDFR",
        "🇬🇧 BoE (UK)":      "IUDSOIA",
        "🇯🇵 BoJ (Japan)":   "IRSTCI01JPM156N",
        "🇨🇦 BoC (Canada)":  "CACOCR",
        "🇦🇺 RBA (Aus)":     "RBATCTR",
        "🇳🇿 RBNZ (NZ)":     "RBNZOCR",
        "🇨🇭 SNB (Swiss)":   "IRSTCI01CHM156N",
    }
    rates      = {}
    rates_prev = {}  # 3-month-ago rate for "direction" indicator

    for label, sid in CB_RATES.items():
        try:
            url = (f"https://api.stlouisfed.org/fred/series/observations"
                   f"?series_id={sid}&api_key={FRED_API_KEY}&file_type=json"
                   f"&sort_order=desc&limit=6")
            r = _req.get(url, timeout=7)
            if r.status_code == 200:
                obs = [o for o in r.json().get("observations", []) if o.get("value", ".") != "."]
                if obs:
                    rates[label] = round(float(obs[0]["value"]), 2)
                if len(obs) >= 4:
                    rates_prev[label] = round(float(obs[3]["value"]), 2)
        except Exception:
            pass

    # Major FX pairs — USD as base/quote
    FX = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "AUD/USD": "AUDUSD=X",
        "USD/CNY": "CNY=X",
        "USD/SGD": "SGD=X",
        "USD/CHF": "CHF=X",
        "USD/CAD": "CAD=X",
    }
    fx_data = {}
    for pair, ticker in FX.items():
        try:
            h = yf.Ticker(ticker).history(period="5d")
            if h.empty:
                continue
            c = h["Close"].dropna()
            now  = float(c.iloc[-1])
            prev = float(c.iloc[-2]) if len(c) > 1 else now
            w1   = float(c.iloc[-6]) if len(c) >= 6 else float(c.iloc[0])
            pct_1d = (now - prev) / prev * 100 if prev else 0
            pct_1w = (now - w1)   / w1   * 100 if w1   else 0
            fx_data[pair] = dict(price=round(now, 4), pct=round(pct_1d, 3), pct_1w=round(pct_1w, 3))
        except Exception:
            pass

    # Global equity indices
    GLOBAL_EQ = {
        "S&P 500":   "^GSPC",
        "NASDAQ":    "^IXIC",
        "FTSE 100":  "^FTSE",
        "DAX":       "^GDAXI",
        "Nikkei":    "^N225",
        "Hang Seng": "^HSI",
        "ASX 200":   "^AXJO",
        "Sensex":    "^BSESN",
    }
    eq_data = {}
    for name, ticker in GLOBAL_EQ.items():
        try:
            h = yf.Ticker(ticker).history(period="5d")
            if h.empty:
                continue
            c = h["Close"].dropna()
            now  = float(c.iloc[-1])
            prev = float(c.iloc[-2]) if len(c) > 1 else now
            w1   = float(c.iloc[-6]) if len(c) >= 6 else float(c.iloc[0])
            pct_1d = (now - prev) / prev * 100 if prev else 0
            pct_1w = (now - w1)   / w1   * 100 if w1   else 0
            eq_data[name] = dict(price=round(now, 2), pct=round(pct_1d, 2), pct_1w=round(pct_1w, 2))
        except Exception:
            pass

    return rates, rates_prev, fx_data, eq_data


@st.cache_data(ttl=3600, show_spinner=False)
def load_insider_sentiment(finnhub_key):
    """
    Finnhub /stock/insider-sentiment endpoint — SEC Form 4 filings aggregated.

    MSPR (Monthly Share Purchase Ratio):
      = (shares purchased) / (shares purchased + shares sold) × 100
      Range: −100 to +100
      Positive = insiders net buying (bullish) · Negative = net selling (bearish)
      Readings above +20 are considered strong insider conviction buys.

    We track 20 bellwether stocks across all 11 GICS sectors to get a
    representative picture of insider sentiment across the whole market.
    Form 4 filings are public within 2 business days of each transaction.
    Source: Finnhub / SEC EDGAR.
    """
    import requests as _req

    # 20 bellwethers across all 11 GICS sectors for representative coverage
    SYMBOLS_BY_SECTOR = {
        "Technology":    ["AAPL", "MSFT", "NVDA"],
        "Financials":    ["JPM",  "GS",   "BAC"],
        "Healthcare":    ["JNJ",  "UNH"],
        "Energy":        ["XOM",  "CVX"],
        "Consumer Disc": ["AMZN", "TSLA"],
        "Comm Services": ["META", "GOOGL"],
        "Industrials":   ["CAT",  "HON"],
        "Materials":     ["FCX"],
        "Utilities":     ["NEE"],
        "Real Estate":   ["PLD"],
        "Consumer Stap": ["WMT"],
    }
    # Flatten for API calls
    ALL_SYMBOLS = [sym for syms in SYMBOLS_BY_SECTOR.values() for sym in syms]
    SYMBOL_SECTOR = {sym: sec for sec, syms in SYMBOLS_BY_SECTOR.items() for sym in syms}

    today     = date.today()
    from_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    to_date   = today.strftime("%Y-%m-%d")

    results = []
    for sym in ALL_SYMBOLS:
        try:
            r = _req.get(
                "https://finnhub.io/api/v1/stock/insider-sentiment",
                params={"symbol": sym, "from": from_date, "to": to_date, "token": finnhub_key},
                timeout=8,
                headers={"User-Agent": "MacroSignal/12.0"},
            )
            if r.status_code != 200:
                continue
            data = r.json().get("data", [])
            if not data:
                continue
            # Sort chronologically and take up to last 3 months
            sorted_data = sorted(data, key=lambda x: (x.get("year", 0), x.get("month", 0)))
            latest = sorted_data[-1]
            # Build 3-month history for sparkline
            history_3m = [(d.get("year"), d.get("month"), d.get("mspr", 0)) for d in sorted_data[-3:]]

            mspr   = latest.get("mspr", 0)  # Monthly Share Purchase Ratio
            change = latest.get("change", 0)  # net share change (positive = net bought)
            results.append({
                "symbol":   sym,
                "sector":   SYMBOL_SECTOR.get(sym, "—"),
                "mspr":     round(mspr, 2) if mspr is not None else 0,
                "change":   change,
                "year":     latest.get("year"),
                "month":    latest.get("month"),
                "history":  history_3m,
            })
        except Exception:
            pass

    return results


@st.cache_data(ttl=1800, show_spinner=False)
def load_market_breadth():
    """
    Estimate S&P 500 market breadth by sampling 50 constituents.
    Computes % above 50d MA and % above 200d MA.
    Also fetches Advance/Decline via SPY vs SPXU proxy.
    Source: yfinance. Sampled for speed — not all 500 stocks.
    """
    # Representative sample across all 11 sectors
    SAMPLE = [
        "AAPL","MSFT","AMZN","GOOGL","META","NVDA","TSLA","V","MA","JPM",
        "BAC","GS","WFC","JNJ","UNH","PFE","MRK","XOM","CVX","COP",
        "CAT","HON","GE","MMM","UPS","WMT","HD","MCD","COST","NKE",
        "DIS","NFLX","CMCSA","T","VZ","AMT","PLD","NEE","DUK","SO",
        "LIN","APD","NEM","FCX","DD","SPY","QQQ","IWM","VNQ","AGG",
    ]
    above_50  = 0
    above_200 = 0
    valid     = 0
    for ticker in SAMPLE:
        try:
            h = yf.Ticker(ticker).history(period="1y")
            if h.empty or len(h)<200: continue
            close = h["Close"].dropna()
            now   = float(close.iloc[-1])
            ma50  = float(close.tail(50).mean())
            ma200 = float(close.tail(200).mean())
            if now > ma50:  above_50  += 1
            if now > ma200: above_200 += 1
            valid += 1
        except Exception:
            pass
    if valid == 0:
        return None
    return {
        "above_50":  round(above_50/valid*100),
        "above_200": round(above_200/valid*100),
        "sample_n":  valid,
    }

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


@st.cache_data(ttl=300, show_spinner=False)
def load_sgx_data():
    """
    Singapore-specific market data:
    - STI components and close
    - DBS/OCBC/UOB bank stocks
    - S-REIT prices with 1D/1M/YTD
    - SGX blue-chip prices
    All via yfinance .SI tickers.
    """
    results = {}
    all_tickers = {
        **{k: (v[0], v[1], "bank")   for k, v in SGX_BANKS.items()},
        **{k: (v[0], v[1], "blue")   for k, v in SGX_BLUE_CHIPS.items()},
        **{k: (v[0], v[1], "reit")   for k, v in SGX_REITS.items()},
    }
    for name, (ticker, color, cat) in all_tickers.items():
        try:
            h = yf.Ticker(ticker).history(period="6mo")
            if h.empty:
                continue
            c = h["Close"].dropna()
            c.index = pd.to_datetime(c.index)
            if c.index.tz is not None:
                c.index = c.index.tz_localize(None)
            now  = float(c.iloc[-1])
            prev = float(c.iloc[-2]) if len(c) > 1 else now
            m1   = float(c.iloc[-22]) if len(c) > 22 else float(c.iloc[0])
            yr_s = c[c.index >= pd.Timestamp(f"{datetime.today().year}-01-01")]
            ystart = float(yr_s.iloc[0]) if len(yr_s) > 0 else float(c.iloc[0])
            results[name] = dict(
                ticker=ticker, color=color, cat=cat,
                price=round(now, 3),
                pct_1d=round((now - prev) / prev * 100, 2) if prev else 0,
                pct_1m=round((now - m1)   / m1   * 100, 2) if m1   else 0,
                pct_ytd=round((now - ystart) / ystart * 100, 2) if ystart else 0,
                hist=c.tail(60),
            )
        except Exception:
            pass
    return results


@st.cache_data(ttl=300, show_spinner=False)
def load_crypto_data():
    """Live crypto prices with 30-day history for charts."""
    results = {}
    for name, (ticker, color) in CRYPTO_TICKERS.items():
        try:
            h = yf.Ticker(ticker).history(period="3mo")
            if h.empty:
                continue
            c = h["Close"].dropna()
            c.index = pd.to_datetime(c.index)
            if c.index.tz is not None:
                c.index = c.index.tz_localize(None)
            now  = float(c.iloc[-1])
            prev = float(c.iloc[-2]) if len(c) > 1 else now
            w1   = float(c.iloc[-6]) if len(c) >= 6 else float(c.iloc[0])
            m1   = float(c.iloc[-22]) if len(c) > 22 else float(c.iloc[0])
            yr_s = c[c.index >= pd.Timestamp(f"{datetime.today().year}-01-01")]
            ystart = float(yr_s.iloc[0]) if len(yr_s) > 0 else float(c.iloc[0])
            results[name] = dict(
                ticker=ticker, color=color,
                price=round(now, 2),
                pct_1d=round((now - prev) / prev * 100, 2) if prev else 0,
                pct_1w=round((now - w1)   / w1   * 100, 2) if w1   else 0,
                pct_1m=round((now - m1)   / m1   * 100, 2) if m1   else 0,
                pct_ytd=round((now - ystart) / ystart * 100, 2) if ystart else 0,
                hist=c.tail(30),
                mktcap_proxy=now,  # relative size proxy
            )
        except Exception:
            pass
    return results


@st.cache_data(ttl=600, show_spinner=False)
def load_global_pmi():
    """
    Global PMI data from FRED where available, plus yfinance proxies.
    Manufacturing PMI > 50 = expansion, < 50 = contraction.
    These are the single most-watched leading indicators for global growth.

    Sources:
    - US ISM Manufacturing: FRED NAPM
    - US ISM Services: FRED NMFCI (non-mfg)
    - Eurozone Mfg PMI: FRED PRMNFM01EZM661N
    - Japan Mfg PMI: proxy via Nikkei direction
    - China Caixin Mfg PMI: FRED (not available, use INDPRO proxy)
    We supplement with hardcoded recent values where FRED lacks live series.
    """
    import requests as _req
    PMI_SERIES = {
        "US Mfg (ISM)":    "NAPM",
        "US Services":     "NMFCI",
        "EU Mfg":          "PRMNFM01EZM661N",
        "US New Orders":   "NAPMNOI",
        "US Employment":   "NAPMEI",
        "US Prices Paid":  "NAPMPRI",
    }
    results = {}
    today = date.today()
    start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
    for label, sid in PMI_SERIES.items():
        try:
            url = (f"https://api.stlouisfed.org/fred/series/observations"
                   f"?series_id={sid}&observation_start={start}"
                   f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=6")
            r = _req.get(url, timeout=7)
            if r.status_code != 200:
                continue
            obs = [o for o in r.json().get("observations", []) if o.get("value", ".") != "."]
            if obs:
                now_v = round(float(obs[0]["value"]), 1)
                prev_v = round(float(obs[1]["value"]), 1) if len(obs) > 1 else None
                hist_v = [round(float(o["value"]), 1) for o in reversed(obs[:6])]
                results[label] = dict(
                    value=now_v,
                    prev=prev_v,
                    delta=round(now_v - prev_v, 1) if prev_v else None,
                    hist=hist_v,
                    expanding=now_v >= 50,
                )
        except Exception:
            pass
    return results


@st.cache_data(ttl=600, show_spinner=False)
def load_dxy_analysis():
    """
    DXY (US Dollar Index) with 6-month daily history and regime analysis.
    DXY > 105 = strong USD = headwind for EM, commodities, risk assets
    DXY < 98  = weak USD  = tailwind for gold, EM, risk assets
    Source: yfinance DX-Y.NYB
    """
    try:
        h = yf.Ticker("DX-Y.NYB").history(period="1y")
        if h.empty:
            return None
        c = h["Close"].dropna()
        c.index = pd.to_datetime(c.index)
        if c.index.tz is not None:
            c.index = c.index.tz_localize(None)
        now  = float(c.iloc[-1])
        prev = float(c.iloc[-2]) if len(c) > 1 else now
        m1   = float(c.iloc[-22]) if len(c) > 22 else float(c.iloc[0])
        m3   = float(c.iloc[-66]) if len(c) > 66 else float(c.iloc[0])
        m6   = float(c.iloc[-126]) if len(c) > 126 else float(c.iloc[0])
        hi52 = float(c.max()); lo52 = float(c.min())
        pct_pos = (now - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else 50
        return dict(
            price=round(now, 2),
            pct_1d=round((now - prev) / prev * 100, 2) if prev else 0,
            pct_1m=round((now - m1)   / m1   * 100, 2) if m1   else 0,
            pct_3m=round((now - m3)   / m3   * 100, 2) if m3   else 0,
            pct_6m=round((now - m6)   / m6   * 100, 2) if m6   else 0,
            hi52=round(hi52, 2), lo52=round(lo52, 2),
            pct_pos=round(pct_pos, 1),
            hist=c,  # full 1-year series for chart
        )
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_smart_money():
    """
    Smart Money / Institutional Flow Proxy:
    1. SPY/RSP ratio — when SPY outperforms equal-weight RSP, large caps dominate
       = institutional defensiveness (buying mega-caps as safety). Rising RSP/SPY
       = breadth expanding = retail+institutional risk-on.
    2. HYG/IEF ratio — high-yield bond ETF vs Treasury ETF. Rising = risk appetite.
    3. XLK/XLU ratio — Tech vs Utilities. The classic risk-on/risk-off ratio.
    4. GLD/SLV ratio — already in commodities, but as a fear barometer.
    Source: yfinance ETF tickers (all liquid, daily data).
    """
    PAIRS = {
        "SPY/RSP (Cap-Weight vs Equal-Weight)": ("SPY", "RSP",
            "Rising = mega-cap leadership = defensive. Falling = breadth expanding = risk-on."),
        "HYG/IEF (High-Yield vs Treasuries)":  ("HYG", "IEF",
            "Rising = investors prefer credit over safety = risk appetite increasing."),
        "XLK/XLU (Tech vs Utilities)":         ("XLK", "XLU",
            "Rising = growth over defensives = risk-on. The cleanest sector ratio."),
        "EEM/SPY (EM vs US Equities)":          ("EEM", "SPY",
            "Rising = global risk appetite. Falling = USD strength / EM outflow."),
    }
    results = {}
    for label, (a_ticker, b_ticker, interp) in PAIRS.items():
        try:
            ha = yf.Ticker(a_ticker).history(period="6mo")["Close"].dropna()
            hb = yf.Ticker(b_ticker).history(period="6mo")["Close"].dropna()
            if ha.empty or hb.empty:
                continue
            ha.index = pd.to_datetime(ha.index)
            hb.index = pd.to_datetime(hb.index)
            if ha.index.tz is not None: ha.index = ha.index.tz_localize(None)
            if hb.index.tz is not None: hb.index = hb.index.tz_localize(None)
            ha.index = ha.index.normalize()
            hb.index = hb.index.normalize()
            ha = ha[~ha.index.duplicated(keep="last")]
            hb = hb[~hb.index.duplicated(keep="last")]
            ratio = (ha / hb).dropna()
            if len(ratio) < 5:
                continue
            now_r  = float(ratio.iloc[-1])
            m1_r   = float(ratio.iloc[-22]) if len(ratio) > 22 else float(ratio.iloc[0])
            m3_r   = float(ratio.iloc[-66]) if len(ratio) > 66 else float(ratio.iloc[0])
            trend  = round((now_r / m1_r - 1) * 100, 2) if m1_r else 0
            trend3m= round((now_r / m3_r - 1) * 100, 2) if m3_r else 0
            results[label] = dict(
                ratio=round(now_r, 4),
                trend_1m=trend,
                trend_3m=trend3m,
                interp=interp,
                hist=ratio.tail(60),
                a_ticker=a_ticker, b_ticker=b_ticker,
            )
        except Exception:
            pass
    return results


@st.cache_data(ttl=300, show_spinner=False)
def load_vol_risk_premium():
    """
    Volatility Risk Premium (VRP) = Implied Vol (VIX) minus Realised Vol (30d).
    VRP > 5  = options expensive, IV compression trade (sell volatility)
    VRP < 0  = options cheap, market underpricing risk (buy protection)
    VRP 0–5  = fair value
    Realised vol = annualised std dev of daily SPX returns over last 30 days.
    """
    try:
        spx = yf.Ticker("^GSPC").history(period="3mo")["Close"].dropna()
        vix = yf.Ticker("^VIX").history(period="5d")["Close"].dropna()
        if spx.empty or vix.empty:
            return None
        rets = spx.pct_change().dropna()
        realised_30d = round(float(rets.tail(30).std() * np.sqrt(252) * 100), 2)
        implied = round(float(vix.iloc[-1]), 2)
        vrp = round(implied - realised_30d, 2)
        # Historical VRP (rolling)
        vrp_hist = []
        vix_hist = yf.Ticker("^VIX").history(period="6mo")["Close"].dropna()
        vix_hist.index = pd.to_datetime(vix_hist.index)
        if vix_hist.index.tz is not None:
            vix_hist.index = vix_hist.index.tz_localize(None)
        spx.index = pd.to_datetime(spx.index)
        if spx.index.tz is not None:
            spx.index = spx.index.tz_localize(None)
        spx_rets = spx.pct_change().dropna()
        for i in range(30, min(len(vix_hist), len(spx_rets))):
            try:
                rv = float(spx_rets.iloc[i-30:i].std() * np.sqrt(252) * 100)
                vdate = vix_hist.index[i] if i < len(vix_hist) else None
                if vdate is not None:
                    iv = float(vix_hist.loc[vdate]) if vdate in vix_hist.index else None
                    if iv is not None:
                        vrp_hist.append((vdate, round(iv - rv, 2)))
            except Exception:
                pass
        vrp_series = None
        if vrp_hist:
            idx  = pd.to_datetime([d for d, _ in vrp_hist])
            vals = [v for _, v in vrp_hist]
            vrp_series = pd.Series(vals, index=idx).tail(60)
        return dict(
            implied=implied, realised=realised_30d, vrp=vrp,
            vrp_hist=vrp_series,
        )
    except Exception:
        return None


def get_market_session_status():
    """
    Returns live open/closed status for each major market session in SGT.
    Handles daylight saving time correctly via pytz.
    """
    now_utc = datetime.now(pytz.utc)
    statuses = {}
    for market, info in MARKET_SESSIONS.items():
        try:
            local_tz  = pytz.timezone(info["tz"])
            local_now = now_utc.astimezone(local_tz)
            is_weekday = local_now.weekday() < 5
            open_h,  open_m  = info["open"]
            close_h, close_m = info["close"]
            open_minutes  = open_h  * 60 + open_m
            close_minutes = close_h * 60 + close_m
            current_minutes = local_now.hour * 60 + local_now.minute
            if is_weekday and open_minutes <= current_minutes < close_minutes:
                status = "OPEN"
                # Minutes until close
                mins_left = close_minutes - current_minutes
                time_str  = f"Closes in {mins_left // 60}h {mins_left % 60}m"
            else:
                status = "CLOSED"
                # Find next open
                if not is_weekday or current_minutes >= close_minutes:
                    # Next weekday
                    days_ahead = 1
                    if local_now.weekday() == 4 and current_minutes >= close_minutes:
                        days_ahead = 3  # Friday after close → Monday
                    elif local_now.weekday() == 5:
                        days_ahead = 2  # Saturday → Monday
                    elif local_now.weekday() == 6:
                        days_ahead = 1  # Sunday → Monday
                    next_open_dt = (local_now + timedelta(days=days_ahead)).replace(
                        hour=open_h, minute=open_m, second=0, microsecond=0)
                else:
                    next_open_dt = local_now.replace(
                        hour=open_h, minute=open_m, second=0, microsecond=0)
                mins_until = int((next_open_dt - local_now).total_seconds() / 60)
                if mins_until < 60:
                    time_str = f"Opens in {mins_until}m"
                elif mins_until < 1440:
                    time_str = f"Opens in {mins_until//60}h {mins_until%60}m"
                else:
                    time_str = f"Opens {next_open_dt.strftime('%a %H:%M')}"

            # Convert open/close to SGT for display
            sgt_open  = datetime.now(pytz.timezone(info["tz"])).replace(
                hour=open_h, minute=open_m, second=0).astimezone(SGT)
            sgt_close = datetime.now(pytz.timezone(info["tz"])).replace(
                hour=close_h, minute=close_m, second=0).astimezone(SGT)

            statuses[market] = dict(
                status=status,
                color=info["color"],
                time_str=time_str,
                sgt_open=sgt_open.strftime("%H:%M"),
                sgt_close=sgt_close.strftime("%H:%M"),
                local_time=local_now.strftime("%H:%M"),
                local_tz_abbr=local_now.strftime("%Z"),
            )
        except Exception:
            statuses[market] = dict(status="UNKNOWN", color="#4a6a8a",
                                     time_str="—", sgt_open="—", sgt_close="—",
                                     local_time="—", local_tz_abbr="—")
    return statuses


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
# SIDEBAR — Page Navigation + Settings
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="padding:14px 4px 10px">'
        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.15rem;font-weight:800;'
        f'color:#f0f8ff;letter-spacing:-.01em">MACRO/SIGNAL</div>'
        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;color:#2a4a6a;'
        f'text-transform:uppercase;letter-spacing:.15em;margin-top:2px">Institutional Macro Intelligence</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown('<hr style="border-top:1px solid #162236;margin:4px 0 12px">',
                unsafe_allow_html=True)

    # Page navigation
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.15em;color:#2a4a6a;margin-bottom:6px">Navigation</div>',
        unsafe_allow_html=True
    )
    PAGES = {
        "Overview":              "overview",
        "Markets & Sectors":     "markets",
        "Global Macro":          "global",
        "Charts & Analysis":     "charts",
        "Calendar & News":       "calendar",
        "Singapore Hub":         "singapore",
        "Crypto & Volatility":   "crypto_vol",
    }
    if "page" not in st.session_state:
        st.session_state.page = "overview"

    for page_label, page_key in PAGES.items():
        is_active = st.session_state.page == page_key
        btn_style = (
            "background:rgba(34,211,238,.12)!important;border:1px solid rgba(34,211,238,.35)!important;"
            "color:#22d3ee!important;font-weight:700!important;"
        ) if is_active else ""
        if st.button(
            page_label,
            key=f"nav_{page_key}",
            use_container_width=True,
        ):
            st.session_state.page = page_key
            st.rerun()

    st.markdown('<hr style="border-top:1px solid #162236;margin:12px 0">',
                unsafe_allow_html=True)

    # Chart settings
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.15em;color:#2a4a6a;margin-bottom:6px">Chart Settings</div>',
        unsafe_allow_html=True
    )
    PRESETS = ["1 Month","3 Months","6 Months","1 Year","2 Years","3 Years","5 Years","Custom"]
    preset  = st.selectbox("Date range", PRESETS, index=3)
    today   = date.today()
    OFFSETS = {"1 Month":30,"3 Months":91,"6 Months":182,
               "1 Year":365,"2 Years":730,"3 Years":1095,"5 Years":1825}
    if preset == "Custom":
        ca, cb = st.columns(2)
        with ca: cs = st.date_input("From", value=today-timedelta(days=365), min_value=date(2000,1,1), max_value=today)
        with cb: ce = st.date_input("To",   value=today, min_value=date(2000,1,1), max_value=today)
        if cs >= ce: st.error("Start must be before end."); st.stop()
        range_start = pd.Timestamp(cs); range_end = pd.Timestamp(ce)
        range_label = f"{cs.strftime('%d %b %y')} – {ce.strftime('%d %b %y')}"
    else:
        days        = OFFSETS[preset]
        range_start = pd.Timestamp(today - timedelta(days=days))
        range_end   = pd.Timestamp(today)
        range_label = preset

    live_interval = st.selectbox("Candle interval", ["1d","1wk","1mo"], index=0)
    live_type     = st.selectbox("Chart type", ["Candlestick","Line"], index=0)

    st.markdown('<hr style="border-top:1px solid #162236;margin:12px 0">',
                unsafe_allow_html=True)

    st.markdown('<div class="refresh-btn">', unsafe_allow_html=True)
    if st.button("⟳  Refresh All Data", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;color:#2a4a6a;'
        'margin-top:5px;text-align:center">Prices: 5 min · Macro: 60 min</div>',
        unsafe_allow_html=True
    )

    st.markdown('<hr style="border-top:1px solid #162236;margin:12px 0">',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.62rem;line-height:1.8;color:#2a4a6a">'
        'Data: FRED · yfinance · Finnhub<br>'
        'Clock: SGT (UTC+8)<br>'
        'Not financial advice.</div>',
        unsafe_allow_html=True
    )


# ── Key guard ────────────────────────────────────────────────────────────────
if not FRED_API_KEY:
    st.error("FRED API key missing. Add FRED_API_KEY to Streamlit secrets.")
    st.stop()

# ── Load all data ─────────────────────────────────────────────────────────────
with st.spinner("Loading live data feeds…"):
    raw_series, df              = load_fred(FRED_API_KEY)
    etfs                        = load_etfs()
    mkt                         = load_market_prices()
    hl_data                     = load_52w_highs()
    corr_df                     = load_correlations()
    cnn_fg                      = load_cnn_fear_greed()
    econ_cal                    = load_econ_calendar(FINNHUB_API_KEY, FRED_API_KEY)
    fh_news                     = load_finnhub_news(FINNHUB_API_KEY)
    fh_earnings                 = load_finnhub_earnings(FINNHUB_API_KEY)
    curve_today, curve_1w, curve_hist = load_yield_curve(FRED_API_KEY)
    opt_sent, opt_hist          = load_options_sentiment()
    commodities, comm_hist      = load_commodities()
    cb_rates, cb_rates_prev, fx_data, eq_data = load_global_macro_snapshot()
    insider_sent                = load_insider_sentiment(FINNHUB_API_KEY)
    breadth                     = load_market_breadth()
    # New v14 loaders
    sgx_data                    = load_sgx_data()
    crypto_data                 = load_crypto_data()
    global_pmi                  = load_global_pmi()
    dxy_data                    = load_dxy_analysis()
    smart_money                 = load_smart_money()
    vol_rp                      = load_vol_risk_premium()
    session_status              = get_market_session_status()

if not raw_series:
    st.error("Unable to load FRED data.")
    st.stop()

sig      = compute(raw_series)
dfc      = df[(df.index >= range_start) & (df.index <= range_end)]
fg_score = compute_fear_greed(sig)
rec_prob = recession_probability(sig)

if   fg_score >= 75: fg_label, fg_col = "EXTREME GREED", "#4ade80"
elif fg_score >= 55: fg_label, fg_col = "GREED",         "#86efac"
elif fg_score >= 45: fg_label, fg_col = "NEUTRAL",       "#94a3b8"
elif fg_score >= 25: fg_label, fg_col = "FEAR",          "#fb923c"
else:                fg_label, fg_col = "EXTREME FEAR",  "#f87171"

if   rec_prob >= 60: rp_col, rp_lbl = "#f87171", "HIGH"
elif rec_prob >= 35: rp_col, rp_lbl = "#fb923c", "ELEVATED"
elif rec_prob >= 20: rp_col, rp_lbl = "#f59e0b", "MODERATE"
else:                rp_col, rp_lbl = "#4ade80", "LOW"

# ── Shared UI helpers ─────────────────────────────────────────────────────────
def regime_banner():
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        st.markdown(
            f'<div class="regime-banner" style="border-left:3px solid {sig["col"]}">'
            f'<div class="regime-dot" style="background:{sig["col"]}"></div>'
            f'<div class="regime-name" style="color:{sig["col"]}">{sig["reg"]}</div>'
            f'<div class="regime-desc">{sig["desc"]}</div></div>',
            unsafe_allow_html=True)
    with rc2:
        real_rate = round(sig["fed"] - sig["cpi"], 2)
        rr_col    = "#4ade80" if real_rate > 0 else "#f87171"
        rr_lbl    = "Restrictive" if real_rate > 0 else "Accommodative"
        st.markdown(
            f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
            f'padding:10px 14px;display:flex;align-items:center;justify-content:space-between">'
            f'<div><div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#4a6a8a;'
            f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px">Real Rate (Fed−CPI)</div>'
            f'<div style="font-family:{MONO};font-size:1.25rem;font-weight:700;color:{rr_col}">'
            f'{real_rate:+.2f}%</div>'
            f'<div style="font-family:{MONO};font-size:.62rem;font-weight:700;color:{rr_col}">'
            f'{rr_lbl}</div></div>'
            f'<div style="text-align:right">'
            f'<div style="font-family:{MONO};font-size:.6rem;color:#4a6a8a;text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:2px">Recession Risk</div>'
            f'<div style="font-family:{MONO};font-size:1.25rem;font-weight:700;color:{rp_col}">'
            f'{rec_prob}%</div>'
            f'<div style="font-family:{MONO};font-size:.62rem;font-weight:700;color:{rp_col}">'
            f'{rp_lbl}</div></div></div>',
            unsafe_allow_html=True)

def footer():
    sgt_f = now_sgt()
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding-top:12px;'
        f'border-top:1px solid #162236;margin-top:1.8rem;flex-wrap:wrap;gap:6px">'
        f'<span style="font-family:{MONO};font-size:.6rem;color:#2a4a6a">'
        f'FRED · yfinance · Finnhub · {sgt_f.strftime("%d %b %Y %H:%M")} SGT</span>'
        f'<span style="font-family:{MONO};font-size:.6rem;color:#2a4a6a">'
        f'Educational only — not financial advice</span>'
        f'<span style="font-family:{MONO};font-size:.6rem;color:#2a4a6a">'
        f'MACRO/SIGNAL v13.0</span></div>',
        unsafe_allow_html=True)

# ─── mkt card helper (used on markets page) ───────────────────────────────────
def _mkt_card(name, accent):
    data  = mkt.get(name)
    price = fmt_price(name, data["price"]) if data else "—"
    pct   = data["pct"] if data else 0
    cls   = "mkt-up" if pct > 0 else "mkt-dn" if pct < 0 else "mkt-flat"
    sign  = "+" if pct > 0 else ""
    return (f'<div class="mkt-card" style="border-top:2px solid {accent}">'
            f'<div class="mkt-name">{name}</div>'
            f'<div class="mkt-price">{price}</div>'
            f'<div class="mkt-chg {cls}">{sign}{pct:.2f}%</div></div>')

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────────────────────────────────────
current_page = st.session_state.get("page", "overview")

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if current_page == "overview":
    page_header("Overview",
                "Regime · Conditions · Momentum · Gauges · KPIs · Risk · Signal",
                f'<span style="font-family:{MONO};font-size:.63rem;color:#a78bfa;margin-left:6px">'
                f'Conv {sig["conv"]}% · 19 indicators</span>')
    regime_banner()

    # ── Economic Conditions Traffic Light ─────────────────────────────────────
    sep("Economic Conditions")
    desc("Six macro conditions at a glance — each colour-coded for whether it supports (green), "
         "warrants caution (amber), or is stressed (red) for risk assets.")

    TL = [
        ("Monetary Policy",  f'{sig["fed"]:.2f}%',
         "#4ade80" if sig["fed"] < 3 else "#f59e0b" if sig["fed"] < 5 else "#f87171",
         "Easy" if sig["fed"] < 3 else "Neutral" if sig["fed"] < 5 else "Tight"),
        ("Inflation (CPI)",  f'{sig["cpi"]:.2f}%',
         "#4ade80" if sig["cpi"] < 2.5 else "#f59e0b" if sig["cpi"] < 4 else "#f87171",
         "Anchored" if sig["cpi"] < 2.5 else "Elevated" if sig["cpi"] < 4 else "Hot"),
        ("Labour Market",    f'{sig["unr"]:.2f}%',
         "#4ade80" if sig["unr"] < 4.5 else "#f59e0b" if sig["unr"] < 5.5 else "#f87171",
         "Tight" if sig["unr"] < 4.5 else "Softening" if sig["unr"] < 5.5 else "Loose"),
        ("Yield Curve",      f'{sig["cur"]:+.2f}%',
         "#4ade80" if sig["cur"] > 0.5 else "#f59e0b" if sig["cur"] > -0.3 else "#f87171",
         "Normal" if sig["cur"] > 0.5 else "Flat" if sig["cur"] > -0.3 else "Inverted ⚠"),
        ("Market Stress",    f'VIX {sig["vix"]:.1f}' if sig["vix"] else "N/A",
         "#4ade80" if sig["vix"] and sig["vix"] < 18 else "#f59e0b" if sig["vix"] and sig["vix"] < 28 else "#f87171",
         vix_label(sig["vix"])),
        ("Growth (GDP)",     f'{sig["rgdpg"]:.1f}%' if sig["rgdpg"] else "N/A",
         "#4ade80" if sig["rgdpg"] and sig["rgdpg"] > 2 else "#f59e0b" if sig["rgdpg"] and sig["rgdpg"] > 0 else "#f87171",
         "Expanding" if sig["rgdpg"] and sig["rgdpg"] > 2 else "Slowing" if sig["rgdpg"] and sig["rgdpg"] > 0 else "Contracting"),
    ]
    tl_cols = st.columns(6)
    for i, (tl_label, tl_val, tl_col, tl_read) in enumerate(TL):
        with tl_cols[i]:
            st.markdown(
                f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                f'padding:12px 13px;border-top:2px solid {tl_col}">'
                f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#6a90b0;'
                f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">{tl_label}</div>'
                f'<div style="font-family:{MONO};font-size:.98rem;font-weight:700;color:{tl_col}">'
                f'{tl_val}</div>'
                f'<div style="font-size:.7rem;color:{tl_col};margin-top:3px;font-weight:600">'
                f'{tl_read}</div></div>',
                unsafe_allow_html=True)

    # ── Macro Momentum ────────────────────────────────────────────────────────
    sep("Macro Momentum")
    desc("Direction of change across 8 key indicators versus their reading 3 months ago. "
         "Green arrow = improving. Red = worsening. Tells you which way the cycle is moving.")

    MOM_CHECKS = [
        ("Fed Rate",     "fed_rate",     False),
        ("CPI",          "cpi_yoy",      False),
        ("Core CPI",     "core_cpi_yoy", False),
        ("Unemployment", "unrate",       False),
        ("Yield Curve",  "curve_10_2",   True),
        ("GDP Growth",   "gdpc1_g",      True),
        ("HY Spread",    "hy_spread",    False),
        ("M2 Growth",    "m2_g",         True),
    ]
    improving_count = 0; deteriorating_count = 0
    mom_cards = []
    for m_label, m_key, higher_better in MOM_CHECKS:
        if m_key not in raw_series:
            mom_cards.append((m_label, None, None, None, "#4a6a8a"))
            continue
        s = raw_series[m_key].dropna()
        if len(s) < 4:
            mom_cards.append((m_label, None, None, None, "#4a6a8a"))
            continue
        now_v = float(s.iloc[-1]); old_v = float(s.iloc[-4])
        delta = now_v - old_v
        impr  = (delta > 0.02 and higher_better) or (delta < -0.02 and not higher_better)
        wors  = (delta < -0.02 and higher_better) or (delta > 0.02 and not higher_better)
        if impr:   mom_col = "#4ade80"; mom_icon = "↑"; improving_count += 1
        elif wors: mom_col = "#f87171"; mom_icon = "↓"; deteriorating_count += 1
        else:      mom_col = "#94a3b8"; mom_icon = "→"
        mom_cards.append((m_label, now_v, delta, mom_icon, mom_col))

    mom_cols = st.columns(8)
    for i, (ml, nv, dv, icon, mc) in enumerate(mom_cards):
        with mom_cols[i]:
            if nv is None:
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                    f'padding:10px 11px">'
                    f'<div style="font-family:{MONO};font-size:.58rem;color:#4a6a8a;text-transform:uppercase;'
                    f'letter-spacing:.09em;margin-bottom:4px">{ml}</div>'
                    f'<div style="color:#2a4a6a;font-family:{MONO};font-size:.8rem">—</div></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                    f'padding:10px 11px;border-left:2px solid {mc}">'
                    f'<div style="font-family:{MONO};font-size:.58rem;color:#6a90b0;text-transform:uppercase;'
                    f'letter-spacing:.09em;margin-bottom:4px">{ml}</div>'
                    f'<div style="font-family:{MONO};font-size:.9rem;font-weight:700;color:#dde8f5">'
                    f'{nv:.2f}</div>'
                    f'<div style="font-family:{MONO};font-size:.78rem;font-weight:700;color:{mc};margin-top:2px">'
                    f'{icon} {dv:+.2f}</div></div>',
                    unsafe_allow_html=True)

    mom_net = improving_count - deteriorating_count
    mom_net_col = "#4ade80" if mom_net > 2 else "#f87171" if mom_net < -2 else "#94a3b8"
    st.markdown(
        f'<div style="margin-top:8px;font-family:{MONO};font-size:.67rem;color:#4a6a8a">'
        f'Net momentum: <span style="color:{mom_net_col};font-weight:700">'
        f'{improving_count} improving · {deteriorating_count} worsening</span> vs 3 months ago'
        f'</div>', unsafe_allow_html=True)

    # ── Fear & Greed + Recession + 52W ───────────────────────────────────────
    sep("Sentiment & Risk Gauges")
    desc("Fear & Greed 0–100 (below 25 = extreme fear, historically a buy zone; above 75 = complacency). "
         "Recession Probability is rule-based — not a forecast, it reflects current indicator stress.")

    fg1, fg2, fg3 = st.columns([1, 1, 2], gap="large")
    with fg1:
        if cnn_fg and cnn_fg.get("value") is not None:
            display_fg    = cnn_fg["value"]
            display_label = cnn_fg["label"]
            fg_source     = "CNN Business"
        else:
            display_fg    = fg_score
            display_label = fg_label
            fg_source     = "Macro Composite"
        if   display_fg >= 75: display_col = "#4ade80"
        elif display_fg >= 55: display_col = "#86efac"
        elif display_fg >= 45: display_col = "#94a3b8"
        elif display_fg >= 25: display_col = "#fb923c"
        else:                  display_col = "#f87171"
        fig_fg = go.Figure(go.Indicator(
            mode="gauge+number", value=display_fg,
            number=dict(font=dict(size=34, color=display_col, family=MONO), suffix=""),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor="#162236",
                          tickfont=dict(size=10, color="#4a6a8a")),
                bar=dict(color=display_col, thickness=0.25),
                bgcolor="rgba(0,0,0,0)", borderwidth=0,
                steps=[
                    dict(range=[0, 25],   color="rgba(248,113,113,.15)"),
                    dict(range=[25, 45],  color="rgba(251,146,60,.10)"),
                    dict(range=[45, 55],  color="rgba(148,163,184,.06)"),
                    dict(range=[55, 75],  color="rgba(134,239,172,.10)"),
                    dict(range=[75, 100], color="rgba(74,222,128,.15)"),
                ],
                threshold=dict(line=dict(color=display_col, width=3), thickness=0.72, value=display_fg),
            ),
            title=dict(text=f"Fear & Greed — {fg_source}",
                       font=dict(size=11, color="#6a90b0", family=MONO)),
            domain=dict(x=[0, 1], y=[0, 1]),
        ))
        fig_fg.update_layout(height=220, paper_bgcolor=BG_SOLID, plot_bgcolor=BG_SOLID,
                             margin=dict(l=14, r=14, t=40, b=6), font=dict(family=MONO))
        st.plotly_chart(fig_fg, use_container_width=True)
        st.markdown(
            f'<div style="text-align:center;margin-top:-12px;font-family:{MONO};font-size:.8rem;'
            f'font-weight:700;color:{display_col};letter-spacing:.1em">{display_label}</div>',
            unsafe_allow_html=True)

    with fg2:
        st.markdown(
            f'<div class="risk-card">'
            f'<div class="risk-title">Recession Probability</div>'
            f'<div class="risk-val" style="color:{rp_col}">{rec_prob}%</div>'
            f'<div class="risk-label" style="color:{rp_col}">{rp_lbl} RISK</div>'
            f'<div class="rec-bar-wrap">'
            f'<div style="width:{rec_prob}%;height:12px;border-radius:5px;background:{rp_col}"></div></div>'
            f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
            f'font-size:.58rem;color:#4a6a8a;margin-top:3px">'
            f'<span>0%</span><span>50%</span><span>100%</span></div>'
            f'<div class="risk-sub" style="margin-top:10px">'
            f'Sahm 40% · Curve 25% · VIX 15% · HY 15% · CFNAI+GDP 10%'
            f'</div></div>', unsafe_allow_html=True)

    with fg3:
        st.markdown('<div class="chart-section-title">52-Week Hi/Lo Position</div>', unsafe_allow_html=True)
        if hl_data:
            hl_cols = st.columns(3)
            for i, nm in enumerate(list(LIVE_CHART_CONFIG.keys())[:6]):
                d = hl_data.get(nm)
                if not d:
                    continue
                with hl_cols[i % 3]:
                    bp = d["pct_pos"]; co = d["color"]
                    ps = f"${d['price']:,.2f}" if d["price"] < 10000 else f"{d['price']:,.0f}"
                    st.markdown(
                        f'<div class="hl-card">'
                        f'<div class="hl-name">{nm}</div>'
                        f'<div class="hl-price" style="color:{co}">{ps}</div>'
                        f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
                        f'font-size:.57rem;color:#4a6a8a;margin-top:5px">'
                        f'<span>Lo {d["lo52"]:,.1f}</span>'
                        f'<span style="color:{co};font-weight:700">{bp:.0f}%</span>'
                        f'<span>Hi {d["hi52"]:,.1f}</span></div>'
                        f'<div class="hl-bar-bg"><div class="hl-bar-fill" style="width:{bp:.0f}%"></div></div>'
                        f'</div>', unsafe_allow_html=True)

    # ── Key Macro KPIs ────────────────────────────────────────────────────────
    sep("Key Macro Indicators")
    desc("The backbone of the US macro picture. Delta shows change vs prior reading.")
    kpi_cols = st.columns(7)
    kpi(kpi_cols[0], "Fed Funds",    sig["fed"],   prev_val(raw_series, "fed_rate"),    "FRED FEDFUNDS")
    kpi(kpi_cols[1], "CPI YoY",      sig["cpi"],   prev_val(raw_series, "cpi_yoy"),     "CPI YoY %")
    kpi(kpi_cols[2], "Core CPI",     sig["core"],  prev_val(raw_series, "core_cpi_yoy"),"Excl food & energy")
    kpi(kpi_cols[3], "Unemployment", sig["unr"],   prev_val(raw_series, "unrate"),      "FRED UNRATE", inv=True)
    kpi(kpi_cols[4], "10Y−2Y Curve", sig["cur"],   prev_val(raw_series, "curve_10_2"),  "Yield curve spread")
    kpi(kpi_cols[5], "Real GDP YoY", sig["rgdpg"], prev_val(raw_series, "gdpc1_g"),     "BEA GDPC1")
    kpi(kpi_cols[6], "Sahm Rule",    sig["sahm"],  prev_val(raw_series, "sahm"),        "Triggers at 0.50", inv=True)

    # ── Risk Cards ────────────────────────────────────────────────────────────
    sep("Risk & Activity Indicators")
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        vv = sig["vix"]; vc = vix_color(vv); vl = vix_label(vv)
        vpv = prev_val(raw_series, "vix")
        vd = f"{vv - vpv:+.1f} vs prev" if vv and vpv else ""
        st.markdown(
            f'<div class="risk-card"><div class="risk-title">VIX — Volatility Index</div>'
            f'<div class="risk-val" style="color:{vc}">{f"{vv:.1f}" if vv else "N/A"}</div>'
            f'<div class="risk-label" style="color:{vc}">{vl}</div>'
            f'<div class="risk-sub">{vd}</div>'
            f'<div class="risk-sub">&lt;15 calm · 20–25 elevated · &gt;30 crisis</div>'
            f'</div>', unsafe_allow_html=True)
    with r2:
        hyv = sig["hy"]; igv = sig["ig"]
        hyc = spread_color(hyv, hy=True); igc = spread_color(igv, hy=False)
        hypv = prev_val(raw_series, "hy_spread"); igpv = prev_val(raw_series, "ig_spread")
        hyd = f"{hyv - hypv:+.2f}" if hyv and hypv else ""
        igd = f"{igv - igpv:+.2f}" if igv and igpv else ""
        st.markdown(
            f'<div class="risk-card"><div class="risk-title">Credit Spreads (ICE BofA OAS)</div>'
            f'<div class="spread-row" style="margin-top:4px"><span class="spread-name">High Yield</span>'
            f'<span class="spread-val" style="color:{hyc}">{f"{hyv:.2f}%" if hyv else "N/A"}'
            f'<span style="font-size:.63rem;color:#4a6a8a;margin-left:4px">{hyd}</span></span></div>'
            f'<div class="spread-row"><span class="spread-name">Investment Grade</span>'
            f'<span class="spread-val" style="color:{igc}">{f"{igv:.2f}%" if igv else "N/A"}'
            f'<span style="font-size:.63rem;color:#4a6a8a;margin-left:4px">{igd}</span></span></div>'
            f'<div class="risk-sub">HY &gt;6% = stress · IG &gt;1.5% = caution</div>'
            f'</div>', unsafe_allow_html=True)
    with r3:
        cv = sig["cfnai"]; cc = cfnai_color(cv); cl = cfnai_label(cv)
        cpv = prev_val(raw_series, "cfnai")
        cd = f"{cv - cpv:+.2f}" if cv is not None and cpv is not None else ""
        ipv = sig["ipyoy"]; ipc = "#4ade80" if ipv and ipv > 0 else "#f87171" if ipv and ipv < 0 else "#94a3b8"
        st.markdown(
            f'<div class="risk-card"><div class="risk-title">Manufacturing Activity</div>'
            f'<div class="spread-row" style="margin-top:4px"><span class="spread-name">CFNAI</span>'
            f'<span class="spread-val" style="color:{cc}">{f"{cv:.2f}" if cv is not None else "N/A"}'
            f'<span style="font-size:.63rem;color:#4a6a8a;margin-left:4px">{cd}</span></span></div>'
            f'<div class="risk-label" style="color:{cc};margin-top:4px">{cl}</div>'
            f'<div class="spread-row" style="margin-top:6px"><span class="spread-name">Indust. Prod YoY</span>'
            f'<span class="spread-val" style="color:{ipc}">'
            f'{f"{ipv:.1f}%" if ipv is not None else "N/A"}</span></div>'
            f'<div class="risk-sub">0 = trend · &lt;−0.7 = recession risk</div>'
            f'</div>', unsafe_allow_html=True)
    with r4:
        sv = sig["sahm"]; sc3 = sahm_color(sv)
        slbl = ("TRIGGERED ⚠" if sv is not None and sv >= 0.5
                else ("WATCH" if sv is not None and 0.3 <= sv < 0.5 else "Clear"))
        sfill = min(100, (sv / 1.0) * 100) if sv is not None else 0
        st.markdown(
            f'<div class="risk-card"><div class="risk-title">Sahm Rule Recession Indicator</div>'
            f'<div class="risk-val" style="color:{sc3}">{f"{sv:.2f}" if sv is not None else "N/A"}</div>'
            f'<div class="risk-label" style="color:{sc3}">{slbl}</div>'
            f'<div class="risk-sub">Triggers at 0.50 · 3m avg unemployment rise ≥0.5pp above 12m low</div>'
            f'<div style="margin-top:8px;background:#080f1c;border-radius:3px;height:6px;overflow:hidden;'
            f'border:1px solid #162236">'
            f'<div style="width:{sfill}%;height:6px;border-radius:3px;background:{sc3}"></div></div>'
            f'<div style="display:flex;justify-content:space-between;font-family:{MONO};font-size:.6rem;'
            f'color:#4a6a8a;margin-top:3px"><span>0</span>'
            f'<span style="color:#f59e0b;font-weight:700">0.5 ▲</span><span>1.0</span></div>'
            f'</div>', unsafe_allow_html=True)

    # ── Trade Signal Summary ──────────────────────────────────────────────────
    sep("Trade Signal Summary")
    desc("Distils all 19 macro indicators into one read. Each indicator votes +1 (risk-on), "
         "−1 (risk-off), or 0 (neutral). Score is the net percentage.")
    votes = []
    votes.append(+1 if sig["fed"] < 3   else (-1 if sig["fed"] > 5     else 0))
    votes.append(+1 if sig["cpi"] < 2.5 else (-1 if sig["cpi"] > 4     else 0))
    votes.append(+1 if sig["core"] < 2.5 else (-1 if sig["core"] > 3.5 else 0))
    gdp = sig["rgdpg"] if sig["rgdpg"] else sig["gdpg"]
    votes.append(+1 if gdp and gdp > 2   else (-1 if gdp and gdp < 0   else 0))
    votes.append(+1 if sig["unr"] < 4.5 else (-1 if sig["unr"] > 5.5  else 0))
    votes.append(+1 if sig["cur"] > 0.5 else (-1 if sig["cur"] < -0.3  else 0))
    votes.append(+1 if sig["vix"] < 18  else (-1 if sig["vix"] > 25    else 0))
    votes.append(+1 if sig["hy"] < 4    else (-1 if sig["hy"] > 6      else 0))
    votes.append(+1 if sig["ig"] < 1.0  else (-1 if sig["ig"] > 1.5    else 0))
    votes.append(+1 if sig["cfnai"] > 0 else (-1 if sig["cfnai"] < -0.7 else 0))
    votes.append(+1 if sig["retg"] and sig["retg"] > 2  else (-1 if sig["retg"] and sig["retg"] < 0 else 0))
    votes.append(+1 if sig["m2g"] and sig["m2g"] > 0   else (-1 if sig["m2g"] and sig["m2g"] < -2 else 0))
    votes.append(-2 if sig["sahm"] and sig["sahm"] >= 0.5 else (0 if sig["sahm"] and sig["sahm"] >= 0.3 else +1))

    total_votes  = sum(votes)
    max_possible = sum(abs(v) for v in votes) or 1
    score_pct    = round((total_votes / max_possible) * 100)
    ron_count    = sum(1 for v in votes if v > 0)
    roff_count   = sum(1 for v in votes if v < 0)
    neut_count   = sum(1 for v in votes if v == 0)

    if   score_pct >= 35:  ts_label, ts_col, ts_bg, ts_icon = "RISK-ON",  "#4ade80", "rgba(74,222,128,.09)",    "▲"
    elif score_pct <= -35: ts_label, ts_col, ts_bg, ts_icon = "RISK-OFF", "#f87171", "rgba(248,113,113,.09)",   "▼"
    else:                  ts_label, ts_col, ts_bg, ts_icon = "NEUTRAL",  "#94a3b8", "rgba(148,163,184,.06)",   "→"

    ts_action = (
        "Macro supports equity exposure. Favour cyclicals, growth, and commodities." if score_pct >= 35
        else "Macro warns of stress. Reduce risk, favour defensives, bonds, cash." if score_pct <= -35
        else "Mixed signals. Balanced positioning. Avoid concentrated bets."
    )
    bar_on   = int(ron_count  / len(votes) * 100)
    bar_off  = int(roff_count / len(votes) * 100)
    bar_neut = 100 - bar_on - bar_off

    st.markdown(
        f'<div style="background:{ts_bg};border:1px solid {ts_col}30;border-radius:8px;'
        f'padding:16px 20px;border-left:3px solid {ts_col}">'
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:9px">'
        f'<div style="font-family:{MONO};font-size:1.85rem;font-weight:800;color:{ts_col};line-height:1">'
        f'{ts_icon} {ts_label}</div>'
        f'<div style="font-family:{MONO};font-size:1rem;font-weight:700;color:{ts_col};opacity:.7">'
        f'{score_pct:+d}%</div></div>'
        f'<div style="font-size:.8rem;color:#c5d8f0;margin-bottom:11px">{ts_action}</div>'
        f'<div style="display:flex;height:6px;border-radius:3px;overflow:hidden;gap:1px;margin-bottom:7px">'
        f'<div style="width:{bar_on}%;background:#4ade80;border-radius:3px 0 0 3px"></div>'
        f'<div style="width:{bar_neut}%;background:#1e2e42"></div>'
        f'<div style="width:{bar_off}%;background:#f87171;border-radius:0 3px 3px 0"></div></div>'
        f'<div style="display:flex;gap:16px;font-family:{MONO};font-size:.65rem">'
        f'<span style="color:#4ade80">▲ {ron_count} risk-on</span>'
        f'<span style="color:#94a3b8">→ {neut_count} neutral</span>'
        f'<span style="color:#f87171">▼ {roff_count} risk-off</span></div>'
        f'<div style="margin-top:7px;font-size:.62rem;color:#2a4a6a;font-family:{MONO}">'
        f'{len(votes)} macro indicators · Not financial advice · Educational only</div>'
        f'</div>', unsafe_allow_html=True)

    footer()

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — MARKETS & SECTORS
# ═══════════════════════════════════════════════════════════════════════════════
elif current_page == "markets":
    page_header("Markets & Sectors",
                "Live prices · Sector rotation signals · ETF performance · Regime heatmap")
    regime_banner()

    # ── Live Prices ───────────────────────────────────────────────────────────
    sep("Live Market Prices")
    mkt_html = ('<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px">'
                + ''.join(_mkt_card(n, a) for n, a in MKT_ACCENTS.items())
                + '</div>')
    st.markdown(mkt_html, unsafe_allow_html=True)

    # ── Asia strip ────────────────────────────────────────────────────────────
    asia_html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:8px">'
    for aname, acfg in ASIA_CHART_CONFIG.items():
        try:
            ah = yf.Ticker(acfg["ticker"]).history(period="5d")
            if not ah.empty:
                ac = ah["Close"].dropna()
                ap = float(ac.iloc[-1]); av = float(ac.iloc[-2]) if len(ac) > 1 else ap
                apct = (ap - av) / av * 100 if av else 0
                acls = "mkt-up" if apct > 0 else "mkt-dn" if apct < 0 else "mkt-flat"
                asign = "+" if apct > 0 else ""
                asia_html += (f'<div class="mkt-card" style="border-top:2px solid {acfg["color"]}">'
                              f'<div class="mkt-name">{aname}</div>'
                              f'<div class="mkt-price">{ap:,.1f}</div>'
                              f'<div class="mkt-chg {acls}">{asign}{apct:.2f}%</div></div>')
        except Exception:
            pass
    asia_html += '</div>'
    st.markdown(asia_html, unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:{MONO};font-size:.6rem;color:#2a4a6a;margin-top:5px">'
                f'Asia-Pacific indices · Refreshed every 5 min</div>', unsafe_allow_html=True)

    # ── Sector Rotation ───────────────────────────────────────────────────────
    sep("Sector Rotation Signals")
    with st.expander("📖  How OW / UW signals are calculated", expanded=False):
        st.markdown(f"""
<div style="font-family:{MONO};font-size:.75rem;line-height:1.85;color:#c5d8f0">

**Score: −2 (Strong Underweight) → +2 (Strong Overweight)**

The model applies historical macro-sector relationships to 6 live FRED readings:

| Rule | Sectors Boosted | Sectors Reduced |
|---|---|---|
| High inflation CPI>5% | +2 Energy, +2 Materials | −2 Real Estate, −1 Tech |
| High rates Fed>5% | +2 Financials | −2 Utilities, −2 Real Estate |
| Low rates Fed<2% | +1 Real Estate, Utilities, Tech | — |
| Inverted curve <−0.5% | +2 Healthcare, +2 Staples | −2 Consumer Disc, −1 Tech |
| GDP contraction | +2 Healthcare, +2 Staples, +1 Util | −2 Tech, −2 Consumer Disc |
| Sahm Rule ≥0.50 | +2 Healthcare, +2 Staples | −2 Tech, −2 Consumer Disc |

Scores clamped to [−2, +2]. **Not financial advice.**
Current: Fed {sig['fed']:.2f}% · CPI {sig['cpi']:.2f}% · Curve {sig['cur']:+.2f}% · Sahm {sig['sahm']:.2f}
</div>""", unsafe_allow_html=True)

    sorted_all = sorted(sig["sc"].items(), key=lambda x: x[1], reverse=True)
    top_ow  = [(SLABELS[k], v) for k, v in sorted_all if v > 0][:3]
    top_uw  = [(SLABELS[k], v) for k, v in reversed(sorted_all) if v < 0][:3]
    PTXT_SHORT = {2: "Strong OW", 1: "OW", 0: "Neutral", -1: "UW", -2: "Strong UW"}

    ow_uw_html = (
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">'
        + f'<div style="background:rgba(74,222,128,.06);border:1px solid rgba(74,222,128,.18);'
          f'border-radius:7px;padding:10px 13px">'
        + f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#4ade80;'
          f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">▲ Top Overweights</div>'
        + ''.join(
            f'<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:.77rem">'
            f'<span style="color:#dde8f5">{nm}</span>'
            f'<span style="color:#4ade80;font-family:{MONO};font-weight:700">{PTXT_SHORT[v]}</span></div>'
            for nm, v in top_ow)
        + '</div>'
        + f'<div style="background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.18);'
          f'border-radius:7px;padding:10px 13px">'
        + f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#f87171;'
          f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">▼ Top Underweights</div>'
        + ''.join(
            f'<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:.77rem">'
            f'<span style="color:#dde8f5">{nm}</span>'
            f'<span style="color:#f87171;font-family:{MONO};font-weight:700">{PTXT_SHORT[v]}</span></div>'
            for nm, v in top_uw)
        + '</div></div>'
    )
    st.markdown(ow_uw_html, unsafe_allow_html=True)

    left, right = st.columns([1, 1.1], gap="large")
    with left:
        sorted_sc = sorted(sig["sc"].items(), key=lambda x: x[1])
        fig_bar = go.Figure(go.Bar(
            x=[v for _, v in sorted_sc],
            y=[SLABELS[k] for k, _ in sorted_sc],
            orientation="h",
            marker=dict(color=[BCLR[v] for _, v in sorted_sc],
                        line=dict(color="rgba(255,255,255,.03)", width=1)),
            text=[PTXT[v] for _, v in sorted_sc], textposition="outside",
            textfont=dict(family=MONO, size=9.5, color="#8ab4d8"),
            hovertemplate="<b>%{y}</b><br>Score: %{x}<extra></extra>",
            cliponaxis=False))
        fig_bar.add_vline(x=0, line_color="rgba(148,163,184,.18)", line_width=1)
        theme(fig_bar, h=350, fullscreen_bg=True)
        fig_bar.update_layout(
            xaxis=dict(range=[-3.2, 3.2],
                       tickvals=[-2, -1, 0, 1, 2],
                       ticktext=["Strong UW", "UW", "Neutral", "OW", "Strong OW"],
                       gridcolor=GRID, tickfont=dict(size=9.5, color="#8ab4d8")),
            yaxis=dict(tickfont=dict(size=11, family=MONO, color="#dde8f5")),
            margin=dict(l=6, r=105, t=10, b=22))
        st.plotly_chart(fig_bar, use_container_width=True)

    with right:
        if etfs:
            rows_html = ""
            for e in etfs:
                sc = sig["sc"].get(e["key"], 0)
                rows_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.7)'>"
                    f"<td style='padding:6px 7px'>"
                    f"<span style='color:#dde8f5;font-size:.79rem;font-weight:600'>{e['label']}</span>"
                    f"<span style='color:#4a6a8a;font-size:.65rem;margin-left:5px'>{e['ticker']}</span></td>"
                    f"<td style='padding:6px 7px;text-align:right;color:#22d3ee;font-family:{MONO};"
                    f"font-size:.79rem;font-weight:700'>${e['price']}</td>"
                    f"<td style='padding:6px 7px;text-align:right'>{pct_html(e['d1'])}</td>"
                    f"<td style='padding:6px 7px;text-align:right'>{pct_html(e['m1'])}</td>"
                    f"<td style='padding:6px 7px;text-align:right'>{pct_html(e['ytd'])}</td>"
                    f"<td style='padding:6px 7px'>{pill(sc)}</td></tr>"
                )
            st.markdown(
                f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                "<thead><tr style='border-bottom:1px solid #162236'>"
                + "".join(
                    f"<th style='padding:6px 7px;color:#6a90b0;font-size:.63rem;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:.07em;text-align:{align}'>{h}</th>"
                    for h, align in zip(["SECTOR", "PRICE", "1D", "1M", "YTD", "SIGNAL"],
                                        ["left", "right", "right", "right", "right", "left"]))
                + f"</tr></thead><tbody>{rows_html}</tbody></table>",
                unsafe_allow_html=True)
        else:
            st.info("ETF data loading — click ⟳ Refresh to retry.", icon="ℹ️")

    # ── Heatmap + Scorecard ───────────────────────────────────────────────────
    sep("Regime Heatmap & Macro Scorecard")
    hm_col, sc_col = st.columns([1.3, 1], gap="large")
    with hm_col:
        st.markdown('<div class="chart-section-title">Sector Heatmap</div>', unsafe_allow_html=True)
        cells = "".join(
            f'<div class="hm-cell" style="background:{HMBG[v]};border:1px solid {HMCL[v]}35">'
            f'<div class="hm-name" style="color:{HMCL[v]}">{SLABELS[k]}</div>'
            f'<div class="hm-sig" style="color:{HMCL[v]}">{PTXT[v]}</div></div>'
            for k, v in sig["sc"].items())
        st.markdown(f'<div class="hm-grid">{cells}</div>', unsafe_allow_html=True)
    with sc_col:
        st.markdown('<div class="chart-section-title">Macro Scorecard</div>', unsafe_allow_html=True)
        sc_data = [
            ("Fed Funds",     "fed_rate",     "fed",   "Tight" if sig["fed"] > 4 else "Easy" if sig["fed"] < 2 else "Neutral"),
            ("CPI YoY",       "cpi_yoy",      "cpi",   "Hot" if sig["cpi"] > 4 else "Elevated" if sig["cpi"] > 2.5 else "Anchored"),
            ("Core CPI",      "core_cpi_yoy", "core",  "Sticky" if sig["core"] > 3 else "Softening"),
            ("Unemployment",  "unrate",       "unr",   "Tight" if sig["unr"] < 4.5 else "Loose"),
            ("Real GDP",      "gdpc1_g",      "rgdpg", "Expanding" if sig["rgdpg"] and sig["rgdpg"] > 2 else "Slowing"),
            ("Nominal GDP",   "gdp_g",        "gdpg",  "Expanding" if sig["gdpg"] and sig["gdpg"] > 2 else "Slowing"),
            ("Yield Curve",   "curve_10_2",   "cur",   "Inverted ⚠" if sig["cur"] < 0 else "Normal"),
            ("VIX",           "vix",          "vix",   vix_label(sig["vix"])),
            ("HY Spread",     "hy_spread",    "hy",    "Stressed ⚠" if sig["hy"] and sig["hy"] > 6 else "Normal"),
            ("IG Spread",     "ig_spread",    "ig",    "Elevated ⚠" if sig["ig"] and sig["ig"] > 1.5 else "Normal"),
            ("CFNAI",         "cfnai",        "cfnai", cfnai_label(sig["cfnai"])),
            ("Indust. Prod",  "ipman_yoy",    "ipyoy", "Expanding" if sig["ipyoy"] and sig["ipyoy"] > 0 else "Contracting"),
            ("Sahm Rule",     "sahm",         "sahm",  "Triggered ⚠" if sig["sahm"] and sig["sahm"] >= 0.5 else "Watch" if sig["sahm"] and sig["sahm"] >= 0.3 else "Clear"),
            ("M2 Growth",     "m2_g",         "m2g",   "Contracting ⚠" if sig["m2g"] and sig["m2g"] < 0 else "Expanding"),
            ("Retail Sales",  "retail_g",     "retg",  "Strong" if sig["retg"] and sig["retg"] > 4 else "Resilient"),
        ]
        rows = "".join(
            f'<div class="sc-row"><span class="sc-label">{lbl}</span>'
            f'<span class="sc-val">{fmt(sig.get(sk))}</span>'
            f'<span style="color:{trend_arrow(raw_series,ck)[1]};font-size:.88rem;text-align:center;'
            f'font-weight:700">{trend_arrow(raw_series,ck)[0]}</span>'
            f'<span class="sc-read">{rd}</span></div>'
            for lbl, ck, sk, rd in sc_data)
        st.markdown(f'<div class="scorecard-wrap">{rows}</div>', unsafe_allow_html=True)

    footer()

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — GLOBAL MACRO
# ═══════════════════════════════════════════════════════════════════════════════
elif current_page == "global":
    page_header("Global Macro",
                "G10 central banks · FX · Global indices · Yield curve · Commodities · Options · Insider")
    regime_banner()

    # ── G10 / FX / Global Equities ────────────────────────────────────────────
    sep("G10 Central Banks · FX · Global Equity Indices")
    desc("The institutional morning briefing — central bank rates with direction vs 3 months ago, "
         "FX pairs with 1-day and 1-week change, and global equity index snapshot.")

    gm1, gm2, gm3 = st.columns(3, gap="large")
    with gm1:
        st.markdown('<div class="chart-section-title">G10 Central Bank Policy Rates</div>',
                    unsafe_allow_html=True)
        if cb_rates:
            cb_html = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                       "<tbody>")
            for label, rate in sorted(cb_rates.items(), key=lambda x: -x[1]):
                rc = ("#f87171" if rate > 5 else "#f59e0b" if rate > 3
                      else "#4ade80" if rate < 1 else "#dde8f5")
                prev_r = cb_rates_prev.get(label)
                if prev_r is not None:
                    diff = rate - prev_r
                    di = ('<span style="color:#f87171;font-size:.72rem">▲</span>' if diff > 0.01
                          else '<span style="color:#4ade80;font-size:.72rem">▼</span>' if diff < -0.01
                          else '<span style="color:#4a6a8a;font-size:.72rem">→</span>')
                else:
                    di = ""
                cb_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                    f"<td style='padding:8px 7px;color:#dde8f5;font-size:.8rem;font-weight:600'>{label}</td>"
                    f"<td style='padding:8px 7px;text-align:right;font-family:{MONO};font-size:.86rem;"
                    f"font-weight:700;color:{rc}'>{rate:.2f}%</td>"
                    f"<td style='padding:8px 7px;text-align:center;width:18px'>{di}</td></tr>")
            cb_html += "</tbody></table>"
            st.markdown(cb_html, unsafe_allow_html=True)
            st.caption("▲ hiked · ▼ cut vs 3 months ago")
        else:
            st.caption("Central bank data loading…")

    with gm2:
        st.markdown('<div class="chart-section-title">Major FX Pairs</div>',
                    unsafe_allow_html=True)
        if fx_data:
            fx_html = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                       f"<thead><tr style='border-bottom:1px solid #162236'>"
                       + "".join(
                           f"<th style='padding:5px 6px;color:#6a90b0;font-size:.58rem;"
                           f"text-transform:uppercase;text-align:{a}'>{h}</th>"
                           for h, a in [("Pair","left"),("Price","right"),("1D","right"),("1W","right")])
                       + "</tr></thead><tbody>")
            for pair, d in fx_data.items():
                pc = d["pct"]; pw = d.get("pct_1w", 0)
                c1 = "#4ade80" if pc > 0 else "#f87171" if pc < 0 else "#94a3b8"
                c2 = "#4ade80" if pw > 0 else "#f87171" if pw < 0 else "#94a3b8"
                fx_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                    f"<td style='padding:7px 6px;color:#dde8f5;font-size:.8rem;font-weight:600'>{pair}</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.82rem;"
                    f"font-weight:700;color:#22d3ee'>{d['price']:.4f}</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.73rem;"
                    f"font-weight:700;color:{c1}'>{'+'if pc>0 else''}{pc:.2f}%</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.73rem;"
                    f"font-weight:700;color:{c2}'>{'+'if pw>0 else''}{pw:.2f}%</td></tr>")
            fx_html += "</tbody></table>"
            st.markdown(fx_html, unsafe_allow_html=True)
        else:
            st.caption("FX data loading…")

    with gm3:
        st.markdown('<div class="chart-section-title">Global Equity Indices</div>',
                    unsafe_allow_html=True)
        if eq_data:
            eq_html = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                       f"<thead><tr style='border-bottom:1px solid #162236'>"
                       + "".join(
                           f"<th style='padding:5px 6px;color:#6a90b0;font-size:.58rem;"
                           f"text-transform:uppercase;text-align:{a}'>{h}</th>"
                           for h, a in [("Index","left"),("Level","right"),("1D","right"),("1W","right")])
                       + "</tr></thead><tbody>")
            for name, d in eq_data.items():
                pc = d["pct"]; pw = d.get("pct_1w", 0)
                c1 = "#4ade80" if pc > 0 else "#f87171" if pc < 0 else "#94a3b8"
                c2 = "#4ade80" if pw > 0 else "#f87171" if pw < 0 else "#94a3b8"
                eq_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                    f"<td style='padding:7px 6px;color:#dde8f5;font-size:.78rem;font-weight:600'>{name}</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.78rem;"
                    f"font-weight:700;color:#22d3ee'>{d['price']:,.1f}</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.73rem;"
                    f"font-weight:700;color:{c1}'>{'+'if pc>0 else''}{pc:.2f}%</td>"
                    f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.73rem;"
                    f"font-weight:700;color:{c2}'>{'+'if pw>0 else''}{pw:.2f}%</td></tr>")
            eq_html += "</tbody></table>"
            st.markdown(eq_html, unsafe_allow_html=True)
        else:
            st.caption("Global indices loading…")

    # ── Insider Sentiment ─────────────────────────────────────────────────────
    sep("Insider Sentiment — SEC Form 4")
    desc("<strong>MSPR</strong> (Monthly Share Purchase Ratio) — positive = net buying. "
         "Above +20 = strong insider conviction. 20 bellwethers across all 11 GICS sectors. "
         "Source: Finnhub / SEC EDGAR · 90-day window.")

    if insider_sent:
        ins_sorted = sorted(insider_sent, key=lambda x: x.get("mspr", 0), reverse=True)
        net_buyers_ins  = [d for d in ins_sorted if d.get("mspr", 0) > 0]
        net_sellers_ins = [d for d in ins_sorted if d.get("mspr", 0) < 0]
        neut_ins        = [d for d in ins_sorted if d.get("mspr", 0) == 0]
        scored_ins = [d.get("mspr", 0) for d in insider_sent if d.get("mspr", 0) != 0]
        avg_mspr   = round(sum(scored_ins) / len(scored_ins), 2) if scored_ins else 0
        ac = ("#4ade80" if avg_mspr > 10 else "#86efac" if avg_mspr > 0
              else "#f87171" if avg_mspr < -10 else "#fca5a5" if avg_mspr < 0 else "#f59e0b")
        al = ("STRONG NET BUYING" if avg_mspr > 20 else "NET BUYING" if avg_mspr > 0
              else "STRONG NET SELLING" if avg_mspr < -20 else "NET SELLING" if avg_mspr < 0 else "Mixed")

        ia, ib = st.columns([1, 2.5], gap="large")
        with ia:
            bp = round(len(net_buyers_ins) / len(insider_sent) * 100) if insider_sent else 0
            st.markdown(
                f'<div class="risk-card">'
                f'<div class="risk-title">Aggregate Signal (20 Bellwethers)</div>'
                f'<div class="risk-val" style="color:{ac}">{avg_mspr:+.1f}</div>'
                f'<div class="risk-label" style="color:{ac};margin-bottom:9px">{al}</div>'
                f'<div style="background:#080f1c;border-radius:3px;height:5px;overflow:hidden;'
                f'border:1px solid #162236;margin-bottom:4px">'
                f'<div style="width:{bp}%;height:5px;border-radius:3px;background:{ac}"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
                f'font-size:.6rem;color:#4a6a8a;margin-bottom:9px">'
                f'<span style="color:#4ade80">▲ {len(net_buyers_ins)}</span>'
                f'<span style="color:#94a3b8">→ {len(neut_ins)}</span>'
                f'<span style="color:#f87171">▼ {len(net_sellers_ins)}</span></div>'
                f'<div class="risk-sub">MSPR >+20 = strong buy<br>Source: Finnhub/EDGAR</div>'
                f'</div>', unsafe_allow_html=True)
        with ib:
            ins_html = (
                f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                "<thead><tr style='border-bottom:1px solid #162236'>"
                + "".join(
                    f"<th style='padding:6px 5px;color:#6a90b0;font-size:.58rem;"
                    f"text-transform:uppercase;text-align:{a}'>{h}</th>"
                    for h, a in [("Symbol","left"),("Sector","left"),("MSPR","right"),
                                  ("Net Shares","right"),("Period","center"),("Signal","center")])
                + "</tr></thead><tbody>")
            for d in ins_sorted:
                mspr = d.get("mspr", 0); chg = d.get("change", 0)
                mc   = ("#4ade80" if mspr > 10 else "#86efac" if mspr > 0
                        else "#f87171" if mspr < -10 else "#fca5a5" if mspr < 0 else "#94a3b8")
                ml   = ("Strong Buy" if mspr > 20 else "Buy" if mspr > 0
                        else "Strong Sell" if mspr < -20 else "Sell" if mspr < 0 else "Neutral")
                mo   = d.get("month", 0); yr = d.get("year", 0)
                per  = f"{yr}-{mo:02d}" if yr else "—"
                cs   = f"{int(chg):+,}" if chg else "—"
                sec  = d.get("sector", "—")[:11]
                ins_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                    f"<td style='padding:6px 5px;color:#22d3ee;font-weight:700;font-size:.78rem'>"
                    f"{d['symbol']}</td>"
                    f"<td style='padding:6px 5px;color:#6a90b0;font-size:.68rem'>{sec}</td>"
                    f"<td style='padding:6px 5px;text-align:right;color:{mc};font-weight:700;"
                    f"font-size:.78rem'>{mspr:+.1f}</td>"
                    f"<td style='padding:6px 5px;text-align:right;color:{mc};font-size:.73rem'>"
                    f"{cs}</td>"
                    f"<td style='padding:6px 5px;text-align:center;color:#6a90b0;font-size:.68rem'>"
                    f"{per}</td>"
                    f"<td style='padding:6px 5px;text-align:center;color:{mc};font-weight:700;"
                    f"font-size:.68rem'>{ml}</td></tr>")
            ins_html += "</tbody></table>"
            st.markdown(ins_html, unsafe_allow_html=True)
            st.caption(">+20 Strong Buy · 0–20 Buy · 0 to −20 Sell · <−20 Strong Sell")
    else:
        st.info("Insider data loading. Refresh to retry.", )

    # ── Live Yield Curve ──────────────────────────────────────────────────────
    sep("Live US Treasury Yield Curve")
    desc("Full curve 1M→30Y from FRED. Grey dashed = 1 week ago. "
         "Inverted curve (short > long) has preceded every US recession since 1955.")

    MATURITY_ORDER = ["1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","20Y","30Y"]
    MATURITY_YEARS = {"1M":1/12,"3M":.25,"6M":.5,"1Y":1,"2Y":2,"3Y":3,
                      "5Y":5,"7Y":7,"10Y":10,"20Y":20,"30Y":30}

    if curve_today:
        x_vals  = [m for m in MATURITY_ORDER if m in curve_today]
        y_today = [curve_today[m] for m in x_vals]
        y_1w    = [curve_1w.get(m) for m in x_vals]
        x_years = [MATURITY_YEARS[m] for m in x_vals]

        yc_l, yc_r = st.columns([2, 1], gap="large")
        with yc_l:
            fig_yc = go.Figure()
            x1wv = [x_years[i] for i, v in enumerate(y_1w) if v is not None]
            y1wv = [v for v in y_1w if v is not None]
            if x1wv:
                fig_yc.add_trace(go.Scatter(x=x1wv, y=y1wv, name="1 Week Ago",
                    line=dict(color="rgba(148,163,184,.38)", width=1.5, dash="dash"), mode="lines"))
            fig_yc.add_trace(go.Scatter(x=x_years, y=y_today, name="Today",
                line=dict(color="#22d3ee", width=2.5), mode="lines+markers",
                marker=dict(size=7, color="#22d3ee", line=dict(color="#060b14", width=1.5)),
                fill="tozeroy", fillcolor="rgba(34,211,238,.05)",
                hovertemplate="<b>%{customdata}</b><br>%{y:.3f}%<extra></extra>",
                customdata=x_vals))
            fig_yc.add_hline(y=0, line_color="rgba(248,113,113,.3)", line_width=1, line_dash="dot")
            fig_yc.update_xaxes(tickvals=x_years, ticktext=x_vals, title_text="Maturity",
                                 gridcolor=GRID, zeroline=False,
                                 tickfont=dict(size=12, color="#ffffff", family=MONO))
            fig_yc.update_yaxes(title_text="Yield (%)", ticksuffix="%")
            theme(fig_yc, h=320, title="US Treasury Yield Curve — Live", fullscreen_bg=True)
            st.plotly_chart(fig_yc, use_container_width=True)

        with yc_r:
            st.markdown('<div class="chart-section-title">Key Spreads</div>', unsafe_allow_html=True)
            spread_pairs_yc = [
                ("10Y − 2Y",  "10Y", "2Y",  "Most-quoted inversion signal"),
                ("10Y − 3M",  "10Y", "3M",  "Fed's preferred recession predictor"),
                ("30Y − 2Y",  "30Y", "2Y",  "Long-end structural expectations"),
                ("5Y − 2Y",   "5Y",  "2Y",  "Near-term growth outlook"),
                ("10Y − 5Y",  "10Y", "5Y",  "Mid-curve shape"),
            ]
            sp_html = ('<div style="background:#0c1a2e;border:1px solid #162236;'
                       'border-radius:8px;padding:12px 13px">')
            for sp_label, long_m, short_m, tip in spread_pairs_yc:
                lv = curve_today.get(long_m); sv = curve_today.get(short_m)
                if lv is not None and sv is not None:
                    sv_val = round(lv - sv, 3)
                    sc = "#4ade80" if sv_val > 0 else "#f87171"
                    sl = "Normal" if sv_val > 0 else "⚠ INVERTED"
                    lv1 = curve_1w.get(long_m); sv1 = curve_1w.get(short_m)
                    if lv1 is not None and sv1 is not None:
                        chg_yc = sv_val - (lv1 - sv1)
                        cs = f"{chg_yc:+.3f}%"
                        cc = "#4ade80" if chg_yc > 0 else "#f87171"
                    else:
                        cs = "—"; cc = "#4a6a8a"
                    sp_html += (
                        f'<div style="padding:8px 0;border-bottom:1px solid rgba(22,34,54,.6)">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<span style="color:#dde8f5;font-size:.78rem;font-weight:600">{sp_label}</span>'
                        f'<span style="color:{sc};font-family:{MONO};font-size:.88rem;font-weight:700">'
                        f'{sv_val:+.3f}%</span></div>'
                        f'<div style="display:flex;justify-content:space-between;margin-top:2px">'
                        f'<span style="color:{sc};font-size:.63rem;font-weight:700">{sl}</span>'
                        f'<span style="color:{cc};font-family:{MONO};font-size:.63rem">1W: {cs}</span>'
                        f'</div></div>')
                else:
                    sp_html += (f'<div style="padding:8px 0;border-bottom:1px solid rgba(22,34,54,.6)">'
                                f'<span style="color:#dde8f5;font-size:.78rem">{sp_label}</span>'
                                f'<span style="color:#4a6a8a;font-size:.75rem;float:right">Awaiting data</span>'
                                f'</div>')
            sp_html += '</div>'
            st.markdown(sp_html, unsafe_allow_html=True)
    else:
        st.warning("Yield curve data loading from FRED. Refresh to retry.", )

    # ── Commodities ───────────────────────────────────────────────────────────
    sep("Commodity Dashboard & Institutional Ratios")
    desc("<strong>Copper/Gold</strong> = #1 growth proxy (rising = global expansion). "
         "<strong>Gold/Silver > 80x</strong> = elevated fear. "
         "<strong>Oil/Gold</strong> = reflationary regime indicator.")

    if commodities:
        comm_price_cols = st.columns(4)
        for i, (cname, d) in enumerate(commodities.items()):
            with comm_price_cols[i % 4]:
                pc = d["pct"]; pcc = "#4ade80" if pc > 0 else "#f87171" if pc < 0 else "#94a3b8"
                m1c = "#4ade80" if d.get("pct_1m", 0) > 0 else "#f87171"
                ytdc = "#4ade80" if d.get("pct_ytd", 0) > 0 else "#f87171"
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                    f'padding:11px 12px;margin-bottom:7px;border-top:2px solid {d["color"]}">'
                    f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#6a90b0;'
                    f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">{cname}</div>'
                    f'<div style="font-family:{MONO};font-size:1.05rem;font-weight:700;color:#f0f8ff">'
                    f'{d["price"]:,.2f}<span style="font-size:.62rem;color:#4a6a8a;margin-left:3px">'
                    f'{d["unit"]}</span></div>'
                    f'<div style="display:flex;gap:7px;margin-top:3px;font-family:{MONO};font-size:.64rem">'
                    f'<span style="color:{pcc};font-weight:700">1D {"+" if pc>0 else ""}{pc:.1f}%</span>'
                    f'<span style="color:{m1c}">1M {"+" if d.get("pct_1m",0)>0 else ""}{d.get("pct_1m",0):.1f}%</span>'
                    f'<span style="color:{ytdc}">YTD {"+" if d.get("pct_ytd",0)>0 else ""}{d.get("pct_ytd",0):.1f}%</span>'
                    f'</div></div>', unsafe_allow_html=True)

        # Ratios
        gp = commodities.get("Gold",     {}).get("price")
        sp = commodities.get("Silver",   {}).get("price")
        cp = commodities.get("Copper",   {}).get("price")
        op = commodities.get("Oil WTI",  {}).get("price")
        bp = commodities.get("Oil Brent",{}).get("price")
        ratios_comm = []
        if cp and gp and gp > 0:
            r = round(cp / gp * 1000, 4)
            ratios_comm.append(("Copper / Gold ×1000", f"{r:.4f}",
                                 "#4ade80" if r > 0.30 else "#f87171",
                                 "Risk-On / Growth" if r > 0.30 else "Risk-Off / Slowdown"))
        if gp and sp and sp > 0:
            r = round(gp / sp, 1)
            ratios_comm.append(("Gold / Silver Ratio", f"{r:.1f}x",
                                 "#f87171" if r > 90 else "#fb923c" if r > 80 else "#4ade80",
                                 "Extreme Fear" if r > 90 else "Elevated Fear" if r > 80 else "Normal"))
        if op and gp and gp > 0:
            r = round(op / gp * 100, 2)
            ratios_comm.append(("Oil / Gold ×100", f"{r:.2f}",
                                 "#fb923c" if r > 6 else "#4ade80" if r > 3 else "#f87171",
                                 "Reflationary" if r > 6 else "Balanced" if r > 3 else "Deflationary"))
        if bp and op and op > 0:
            r = round(bp - op, 2)
            ratios_comm.append(("Brent − WTI Spread", f"${r:+.2f}",
                                 "#f59e0b" if r > 3 else "#4ade80",
                                 "Wide / Geo Premium" if r > 3 else "Normal Premium"))
        if ratios_comm:
            rc_cols = st.columns(len(ratios_comm))
            for i, (rl, rv, rcol, ri) in enumerate(ratios_comm):
                with rc_cols[i]:
                    st.markdown(
                        f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                        f'padding:13px;border-top:2px solid {rcol}">'
                        f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#6a90b0;'
                        f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">{rl}</div>'
                        f'<div style="font-family:{MONO};font-size:1.35rem;font-weight:700;color:{rcol}">'
                        f'{rv}</div>'
                        f'<div style="font-size:.7rem;color:{rcol};font-weight:600;margin-top:3px">'
                        f'{ri}</div></div>', unsafe_allow_html=True)
    else:
        st.warning("Commodity data loading. Refresh to retry.", )

    # ── Options & Breadth ─────────────────────────────────────────────────────
    sep("Options Sentiment & Market Breadth")
    desc("Put/Call > 0.85 = fear (contrarian buy). < 0.55 = complacency. "
         "VIX backwardation (VIX > VIX3M) = acute short-term stress. "
         "Breadth > 75% above 50d MA = healthy broad advance.")

    op1, op2, op3 = st.columns(3, gap="large")
    with op1:
        st.markdown('<div class="chart-section-title">VIX Term Structure</div>',
                    unsafe_allow_html=True)
        vix_v = opt_sent.get("VIX"); vix3m_v = opt_sent.get("VIX3M"); vix6m_v = opt_sent.get("VIX6M")
        if vix_v:
            backw = vix3m_v and vix_v > vix3m_v
            struct_lbl = "⚠ BACKWARDATION — Near-term stress" if backw else "✓ CONTANGO — Calm"
            struct_col = "#f87171" if backw else "#4ade80"
            vix_pts = {"30d (VIX)": vix_v}
            if vix3m_v: vix_pts["93d (VIX3M)"] = vix3m_v
            if vix6m_v: vix_pts["6M (VXMT)"]   = vix6m_v
            fig_ts = go.Figure()
            fig_ts.add_trace(go.Bar(
                x=list(vix_pts.keys()), y=list(vix_pts.values()),
                marker=dict(color=[vix_color(v) for v in vix_pts.values()],
                            line=dict(color="rgba(0,0,0,0)")),
                text=[f"{v:.2f}" for v in vix_pts.values()],
                textposition="outside",
                textfont=dict(size=13, color="#ffffff", family=MONO)))
            fig_ts.add_hline(y=20, line_dash="dash", line_color="rgba(200,220,240,.38)",
                             annotation_text="20", annotation_font_size=10)
            fig_ts.add_hline(y=30, line_dash="dash", line_color="rgba(248,113,113,.38)",
                             annotation_text="30", annotation_font_size=10)
            theme(fig_ts, h=230, title="VIX Term Structure", fullscreen_bg=True)
            fig_ts.update_layout(yaxis=dict(range=[0, max(list(vix_pts.values())) * 1.3]))
            st.plotly_chart(fig_ts, use_container_width=True)
            st.markdown(
                f'<div style="background:rgba({"248,113,113" if backw else "74,222,128"},.07);'
                f'border:1px solid rgba({"248,113,113" if backw else "74,222,128"},.2);'
                f'border-radius:6px;padding:8px 12px;font-family:{MONO};font-size:.73rem;'
                f'font-weight:700;color:{struct_col}">{struct_lbl}</div>',
                unsafe_allow_html=True)
        else:
            st.caption("VIX data loading…")

    with op2:
        st.markdown('<div class="chart-section-title">CBOE Put/Call Ratios</div>',
                    unsafe_allow_html=True)
        pc_eq = opt_sent.get("PC_EQ"); pc_tot = opt_sent.get("PC_TOT"); pc_idx = opt_sent.get("PC_IDX")

        def pc_label_fn(v, eq=True):
            if v is None: return "N/A", "#4a6a8a"
            if eq:
                if v > 0.85: return "High Fear — Contrarian Bullish", "#4ade80"
                if v > 0.70: return "Elevated Caution", "#86efac"
                if v > 0.55: return "Neutral / Balanced", "#94a3b8"
                if v > 0.45: return "Mild Complacency", "#fca5a5"
                return "Extreme Complacency — Warning", "#f87171"
            else:
                if v > 1.10: return "Heavy Hedging — Inst. Fear", "#4ade80"
                if v > 0.90: return "Elevated Protection", "#86efac"
                if v > 0.70: return "Neutral", "#94a3b8"
                return "Low Hedging — Complacency", "#f87171"

        pc_html_str = ('<div style="background:#0c1a2e;border:1px solid #162236;'
                       'border-radius:8px;padding:13px">')
        for rl, val, is_eq in [("Equity P/C (^PCCE)", pc_eq,  True),
                                ("Total P/C (^CPC)",   pc_tot, False),
                                ("Index P/C (^PCCR)",  pc_idx, False)]:
            lbl, col = pc_label_fn(val, is_eq)
            val_s = f"{val:.3f}" if val is not None else "—"
            pc_html_str += (
                f'<div style="padding:9px 0;border-bottom:1px solid rgba(22,34,54,.7)">'
                f'<div style="display:flex;justify-content:space-between">'
                f'<span style="color:#dde8f5;font-size:.78rem;font-weight:600">{rl}</span>'
                f'<span style="color:#22d3ee;font-family:{MONO};font-size:1.02rem;font-weight:700">'
                f'{val_s}</span></div>'
                f'<div style="color:{col};font-family:{MONO};font-size:.67rem;font-weight:700;'
                f'margin-top:3px">{lbl}</div></div>')
        pc_html_str += '</div>'
        st.markdown(pc_html_str, unsafe_allow_html=True)

    with op3:
        st.markdown('<div class="chart-section-title">S&P 500 Market Breadth</div>',
                    unsafe_allow_html=True)
        if breadth:
            a50  = breadth.get("above_50",  0)
            a200 = breadth.get("above_200", 0)
            n    = breadth.get("sample_n",  0)

            def bl_fn(pct):
                if pct >= 75: return "Broad Advance", "#4ade80"
                if pct >= 55: return "Majority Participating", "#86efac"
                if pct >= 45: return "Mixed", "#94a3b8"
                if pct >= 30: return "Narrowing ⚠", "#fb923c"
                return "Extreme Narrowing ⚠", "#f87171"

            b50l, b50c   = bl_fn(a50)
            b200l, b200c = bl_fn(a200)
            st.markdown(
                f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:15px">'
                f'<div style="margin-bottom:13px">'
                f'<div style="font-family:{MONO};font-size:.6rem;color:#6a90b0;text-transform:uppercase;'
                f'margin-bottom:3px">% Above 50-Day MA</div>'
                f'<div style="font-family:{MONO};font-size:1.55rem;font-weight:700;color:{b50c}">{a50}%</div>'
                f'<div style="background:#080f1c;border-radius:3px;height:5px;margin:4px 0">'
                f'<div style="width:{a50}%;height:5px;border-radius:3px;background:{b50c}"></div></div>'
                f'<div style="font-size:.65rem;color:{b50c};font-weight:600">{b50l}</div></div>'
                f'<div>'
                f'<div style="font-family:{MONO};font-size:.6rem;color:#6a90b0;text-transform:uppercase;'
                f'margin-bottom:3px">% Above 200-Day MA</div>'
                f'<div style="font-family:{MONO};font-size:1.55rem;font-weight:700;color:{b200c}">{a200}%</div>'
                f'<div style="background:#080f1c;border-radius:3px;height:5px;margin:4px 0">'
                f'<div style="width:{a200}%;height:5px;border-radius:3px;background:{b200c}"></div></div>'
                f'<div style="font-size:.65rem;color:{b200c};font-weight:600">{b200l}</div></div>'
                f'<div style="font-family:{MONO};font-size:.58rem;color:#4a6a8a;margin-top:9px">'
                f'Sample: {n} S&P 500 stocks</div></div>',
                unsafe_allow_html=True)
        else:
            st.info("Breadth loading (samples 50 stocks). Refresh to retry.", )

    footer()

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — CHARTS & ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif current_page == "charts":
    page_header("Charts & Analysis",
                f"Macro chart range: {range_label} · All charts support fullscreen ⛶")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Rates & Inflation",
        "Yield Curve",
        "Labour & GDP",
        "Liquidity",
        "VIX · Spreads",
        "Live US Markets",
        "Asia Markets",
        "Correlations",
    ])

    with tab1:
        desc("<strong>Fed Funds Rate vs Inflation:</strong> when the Fed rate is above CPI, policy is "
             "restrictive. Below CPI = still stimulative. 2% dashed line = Fed's official target. "
             "<strong>PCE</strong> is the Fed's preferred inflation gauge.")
        st.markdown('<div class="chart-section-title">Policy Rate vs Inflation</div>',
                    unsafe_allow_html=True)
        fig1a = go.Figure()
        for ck, nm, col, lw, dash, fill, fc in [
            ("fed_rate",     "Fed Rate",  C["blue"],   2,   "solid", "tozeroy", "rgba(34,211,238,.05)"),
            ("cpi_yoy",      "CPI YoY",   C["red"],    2,   "solid", None,      None),
            ("core_cpi_yoy", "Core CPI",  C["orange"], 1.5, "dot",   None,      None),
        ]:
            if ck in dfc.columns:
                s = dfc[ck].dropna()
                if not s.empty:
                    kw = dict(line=dict(color=col, width=lw, dash=dash))
                    if fill: kw["fill"] = fill
                    if fc:   kw["fillcolor"] = fc
                    fig1a.add_trace(go.Scatter(x=s.index, y=s.values, name=nm, **kw))
        fig1a.add_hline(y=2, line_dash="dash", line_color="rgba(148,163,184,.3)",
                        annotation_text="2% target", annotation_font_size=11)
        theme(fig1a, h=380, title="Fed Funds Rate vs CPI & Core CPI", fullscreen_bg=True)
        st.plotly_chart(fig1a, use_container_width=True)

        st.markdown('<div class="chart-section-title">PCE Inflation & 10Y Treasury Yield</div>',
                    unsafe_allow_html=True)
        fig1b = go.Figure()
        for ck, nm, col in [("pce_yoy", "PCE YoY", C["purple"]), ("t10y", "10Y Yield", C["teal"])]:
            if ck in dfc.columns:
                s = dfc[ck].dropna()
                if not s.empty:
                    fig1b.add_trace(go.Scatter(x=s.index, y=s.values, name=nm,
                                               line=dict(color=col, width=2)))
        theme(fig1b, h=300, title="PCE Inflation & 10Y Treasury Yield", fullscreen_bg=True)
        st.plotly_chart(fig1b, use_container_width=True)

    with tab2:
        desc("<strong>The Yield Curve</strong> — normal = upward sloping, inverted = recession warning. "
             "The 10Y−2Y spread has inverted before every US recession since 1955, typically 6–18 months prior. "
             "The 10Y−3M is considered by the Fed to be the most reliable recession predictor.")
        for ck, ttl in [("curve_10_2", "10Y – 2Y Spread"),
                        ("curve_10_3m", "10Y – 3M Spread")]:
            st.markdown(f'<div class="chart-section-title">{ttl}</div>', unsafe_allow_html=True)
            if ck in dfc.columns:
                s = dfc[ck].dropna()
                if not s.empty:
                    f = go.Figure()
                    f.add_trace(go.Scatter(x=s.index, y=s.clip(lower=0).values, name="Normal",
                        fill="tozeroy", fillcolor="rgba(74,222,128,.10)",
                        line=dict(color=C["green"], width=2)))
                    f.add_trace(go.Scatter(x=s.index, y=s.clip(upper=0).values, name="Inverted",
                        fill="tozeroy", fillcolor="rgba(248,113,113,.12)",
                        line=dict(color=C["red"], width=2)))
                    f.add_hline(y=0, line_color="rgba(148,163,184,.4)", line_width=1.5,
                                annotation_text="Inversion line", annotation_font_size=11)
                    theme(f, h=320, title=ttl + " (%)", fullscreen_bg=True)
                    st.plotly_chart(f, use_container_width=True)

    with tab3:
        desc("<strong>Labour market & GDP</strong> — rising unemployment + falling GDP = classic recession. "
             "<strong>Housing Starts</strong> leads the cycle by 6–12 months.")
        col_a, col_b = st.columns(2)
        with col_a:
            for ck, ttl, col in [("unrate",   "US Unemployment Rate (%)",   C["purple"]),
                                  ("retail_g", "Retail Sales Growth YoY (%)", C["teal"]),
                                  ("housing",  "Housing Starts (Thousands)",  C["pink"])]:
                st.markdown(f'<div class="chart-section-title">{ttl}</div>', unsafe_allow_html=True)
                src = "housing" if ck == "housing" else ck
                if src in dfc.columns:
                    s = dfc[src].dropna()
                    if not s.empty:
                        f = go.Figure()
                        f.add_trace(go.Scatter(x=s.index, y=s.values, name=ttl,
                            line=dict(color=col, width=2), fill="tozeroy",
                            fillcolor=f"rgba({','.join(str(int(col.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},.07)"))
                        if ck == "retail_g":
                            f.add_hline(y=0, line_color="rgba(148,163,184,.3)")
                        theme(f, h=270, title=ttl, fullscreen_bg=True)
                        st.plotly_chart(f, use_container_width=True)
        with col_b:
            for ck, ttl, bar in [("gdpc1_g", "Real GDP Growth YoY %", True),
                                  ("gdp_g",   "Nominal GDP Growth YoY %", True)]:
                st.markdown(f'<div class="chart-section-title">{ttl}</div>', unsafe_allow_html=True)
                if ck in dfc.columns:
                    s = dfc[ck].dropna()
                    if not s.empty:
                        f = go.Figure()
                        f.add_trace(go.Bar(x=s.index, y=s.values, name=ttl,
                            marker_color=["#4ade80" if v >= 0 else "#f87171" for v in s.values],
                            opacity=.85))
                        f.add_hline(y=0, line_color="rgba(148,163,184,.3)")
                        theme(f, h=270, title=ttl, fullscreen_bg=True)
                        st.plotly_chart(f, use_container_width=True)

    with tab4:
        desc("<strong>M2 Money Supply</strong> — when M2 grows rapidly, more money chases assets (bullish). "
             "Negative M2 YoY has historically preceded market stress. "
             "The Fed rate vs yield curve overlay shows how monetary policy shapes the curve.")
        st.markdown('<div class="chart-section-title">M2 Money Supply Growth YoY</div>',
                    unsafe_allow_html=True)
        if "m2_g" in dfc.columns:
            s = dfc["m2_g"].dropna()
            if not s.empty:
                f = go.Figure()
                f.add_trace(go.Scatter(x=s.index, y=s.values, name="M2 YoY",
                    line=dict(color=C["yellow"], width=2), fill="tozeroy",
                    fillcolor="rgba(245,158,11,.06)"))
                f.add_hline(y=0, line_color="rgba(148,163,184,.3)")
                theme(f, h=320, title="M2 Money Supply Growth YoY (%)", fullscreen_bg=True)
                st.plotly_chart(f, use_container_width=True)

        st.markdown('<div class="chart-section-title">Fed Rate vs Yield Curve Spread</div>',
                    unsafe_allow_html=True)
        f2 = go.Figure()
        if "curve_10_2" in dfc.columns:
            s = dfc["curve_10_2"].dropna()
            if not s.empty:
                f2.add_trace(go.Scatter(x=s.index, y=s.values, name="10Y–2Y Spread",
                    line=dict(color=C["teal"], width=2)))
        if "fed_rate" in dfc.columns:
            s = dfc["fed_rate"].dropna()
            if not s.empty:
                f2.add_trace(go.Scatter(x=s.index, y=s.values, name="Fed Rate",
                    line=dict(color=C["blue"], width=2, dash="dot")))
        f2.add_hline(y=0, line_color="rgba(148,163,184,.3)")
        theme(f2, h=300, title="Fed Funds Rate vs 10Y–2Y Yield Spread (%)", fullscreen_bg=True)
        st.plotly_chart(f2, use_container_width=True)

    with tab5:
        desc("<strong>VIX</strong> spikes during crashes, collapses in calm markets. "
             "<strong>Credit Spreads</strong> widen when investors fear corporate defaults. "
             "<strong>CFNAI</strong> below −0.7 = recession risk. "
             "<strong>Sahm Rule</strong> at 0.50 = recession likely underway.")
        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown('<div class="chart-section-title">VIX — 2-Year History</div>',
                        unsafe_allow_html=True)
            vix_hist = load_live_chart("^VIX", period="2y", interval="1d")
            if vix_hist is not None and not vix_hist.empty:
                fv = go.Figure()
                fv.add_trace(go.Scatter(x=vix_hist.index, y=vix_hist["Close"], name="VIX",
                    line=dict(color=C["orange"], width=2.5), fill="tozeroy",
                    fillcolor="rgba(251,146,60,.08)"))
                for y_level, label, col_vix in [(15, "15 low", "#4ade80"),
                                                (20, "20 elevated", "#e0eeff"),
                                                (30, "30 crisis", "#f87171")]:
                    fv.add_hline(y=y_level, line_dash="dash",
                                 line_color=f"rgba({','.join(str(int(col_vix.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},.5)",
                                 line_width=1.5, annotation_text=label, annotation_font_size=11)
                theme(fv, h=330, title="VIX — CBOE Volatility Index", fullscreen_bg=True)
                fv.update_layout(xaxis_rangeslider_visible=False)
                st.plotly_chart(fv, use_container_width=True)

            st.markdown('<div class="chart-section-title">CFNAI</div>', unsafe_allow_html=True)
            if "cfnai" in dfc.columns:
                s = dfc["cfnai"].dropna()
                if not s.empty:
                    f = go.Figure()
                    f.add_hrect(y0=-0.7, y1=float(s.min()) - 0.05,
                                fillcolor="rgba(248,113,113,.06)", line_width=0)
                    f.add_trace(go.Scatter(x=s.index, y=s.values, name="CFNAI",
                        line=dict(color=C["teal"], width=2), fill="tozeroy",
                        fillcolor="rgba(45,212,191,.06)"))
                    f.add_hline(y=0, line_color="rgba(148,163,184,.3)", line_width=1.5)
                    f.add_hline(y=-0.7, line_dash="dash", line_color="rgba(248,113,113,.5)",
                                annotation_text="−0.7 recession risk", annotation_font_size=11)
                    theme(f, h=290, title="Chicago Fed National Activity Index", fullscreen_bg=True)
                    st.plotly_chart(f, use_container_width=True)

        with col_y:
            st.markdown('<div class="chart-section-title">Credit Spreads — HY & IG</div>',
                        unsafe_allow_html=True)
            f = go.Figure()
            if "hy_spread" in dfc.columns:
                s = dfc["hy_spread"].dropna()
                if not s.empty:
                    f.add_trace(go.Scatter(x=s.index, y=s.values, name="HY Spread",
                        line=dict(color=C["red"], width=2)))
            if "ig_spread" in dfc.columns:
                s = dfc["ig_spread"].dropna()
                if not s.empty:
                    f.add_trace(go.Scatter(x=s.index, y=s.values, name="IG Spread",
                        line=dict(color=C["teal"], width=2, dash="dot")))
            theme(f, h=310, title="Credit Spreads — HY & IG (ICE BofA OAS, %)", fullscreen_bg=True)
            st.plotly_chart(f, use_container_width=True)

            st.markdown('<div class="chart-section-title">Sahm Rule</div>', unsafe_allow_html=True)
            if "sahm" in dfc.columns:
                s = dfc["sahm"].dropna()
                if not s.empty:
                    f = go.Figure()
                    maxv = max(float(s.max()) + 0.05, 0.6)
                    f.add_hrect(y0=0.5, y1=maxv, fillcolor="rgba(248,113,113,.06)", line_width=0,
                                annotation_text="Recession zone", annotation_font_size=11,
                                annotation_font_color="#f87171")
                    f.add_trace(go.Scatter(x=s.index, y=s.values, name="Sahm Rule",
                        line=dict(color=C["yellow"], width=2.5), fill="tozeroy",
                        fillcolor="rgba(245,158,11,.07)"))
                    f.add_hline(y=0.5, line_dash="dash", line_color="#f87171", line_width=2,
                                annotation_text="0.5 trigger", annotation_font_size=11)
                    theme(f, h=310, title="Sahm Rule Recession Indicator", fullscreen_bg=True)
                    st.plotly_chart(f, use_container_width=True)

    with tab6:
        desc("Live candlestick charts. Green candle = closed higher than open; red = lower. "
             "Volume bars show how many contracts traded — high volume on a big move = more significant. "
             "Use the date range picker below.")
        st.markdown('<div class="chart-section-title">Date Range</div>', unsafe_allow_html=True)
        lr1, lr2, lr3, lr4 = st.columns([1, 1, 1, 2])
        with lr1:
            live_start = st.date_input("From", value=date.today() - timedelta(days=182),
                                       min_value=date(2000, 1, 1), max_value=date.today(), key="live_from")
        with lr2:
            live_end = st.date_input("To", value=date.today(),
                                     min_value=date(2000, 1, 1), max_value=date.today(), key="live_to")
        with lr3:
            st.markdown("<br>", unsafe_allow_html=True)
            use_custom_range = st.checkbox("Use custom", value=False)
        with lr4:
            if not use_custom_range:
                quick = st.selectbox("Quick preset",
                                     ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                                     index=3, key="live_quick")
        if live_start >= live_end and use_custom_range:
            st.error("Start date must be before end date.")
        else:
            c1, c2 = st.columns(2)
            for col_idx, (pname, pcfg) in enumerate(LIVE_CHART_CONFIG.items()):
                with (c1 if col_idx % 2 == 0 else c2):
                    st.markdown(f'<div class="chart-section-title">{pname}</div>',
                                unsafe_allow_html=True)
                    if use_custom_range:
                        hist = load_live_chart_dates(
                            pcfg["ticker"],
                            live_start.strftime("%Y-%m-%d"),
                            live_end.strftime("%Y-%m-%d"),
                            interval=live_interval)
                    else:
                        hist = load_live_chart(pcfg["ticker"], period=quick, interval=live_interval)
                    make_live_chart(pname, pcfg, hist)

    with tab7:
        desc("Asia-Pacific indices open before US markets — they give early clues about global risk sentiment. "
             "Strong Asian sessions often (but not always) carry over to Europe and the US.")
        ar1, ar2, ar3, ar4 = st.columns([1, 1, 1, 2])
        with ar1:
            asia_start = st.date_input("From", value=date.today() - timedelta(days=182),
                                       min_value=date(2000, 1, 1), max_value=date.today(), key="asia_from")
        with ar2:
            asia_end = st.date_input("To", value=date.today(),
                                     min_value=date(2000, 1, 1), max_value=date.today(), key="asia_to")
        with ar3:
            st.markdown("<br>", unsafe_allow_html=True)
            asia_custom = st.checkbox("Use custom", value=False, key="asia_custom")
        with ar4:
            if not asia_custom:
                asia_quick = st.selectbox("Quick preset",
                                          ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                          index=3, key="asia_quick")
        ac1, ac2 = st.columns(2)
        for col_idx, (aname, acfg) in enumerate(ASIA_CHART_CONFIG.items()):
            with (ac1 if col_idx % 2 == 0 else ac2):
                st.markdown(f'<div class="chart-section-title">{aname}</div>',
                            unsafe_allow_html=True)
                if asia_custom and asia_start < asia_end:
                    ah = load_live_chart_dates(acfg["ticker"],
                                               asia_start.strftime("%Y-%m-%d"),
                                               asia_end.strftime("%Y-%m-%d"),
                                               interval=live_interval)
                else:
                    ah = load_live_chart(
                        acfg["ticker"],
                        period=asia_quick if not asia_custom else "6mo",
                        interval=live_interval)
                make_live_chart(aname, acfg, ah)

    with tab8:
        desc("+1 = perfect lockstep. −1 = perfect opposite (true diversification). "
             "0 = no relationship. In a crash, normally-diversifying assets often become correlated. "
             "This matrix uses 6 months of daily returns.")
        if corr_df is not None and not corr_df.empty and len(corr_df.columns) >= 2:
            labels = list(corr_df.columns)
            z = corr_df.values.tolist()
            text = [[f"{v:.2f}" for v in row] for row in z]
            fig_corr = go.Figure(go.Heatmap(
                z=z, x=labels, y=labels,
                text=text, texttemplate="%{text}",
                textfont=dict(size=14, color="white", family=MONO),
                colorscale=[[0.0, "#f87171"],[0.4, "rgba(30,50,90,1)"],
                             [0.5, "rgba(20,35,65,1)"],[0.6, "rgba(30,50,90,1)"],
                             [1.0, "#4ade80"]],
                zmid=0, zmin=-1, zmax=1,
                colorbar=dict(title=dict(text="Corr", font=dict(size=12, color="#8ab4d8", family=MONO)),
                              tickfont=dict(size=12, color="#ffffff", family=MONO),
                              thickness=14),
                hovertemplate="<b>%{y} vs %{x}</b><br>Corr: %{z:.2f}<extra></extra>",
            ))
            theme(fig_corr, h=500, title="6-Month Return Correlations (Daily)", fullscreen_bg=True)
            fig_corr.update_layout(margin=dict(l=60, r=80, t=60, b=60))
            fig_corr.update_xaxes(tickfont=dict(size=14, color="#ffffff", family=MONO), tickangle=0)
            fig_corr.update_yaxes(tickfont=dict(size=14, color="#ffffff", family=MONO))
            st.plotly_chart(fig_corr, use_container_width=True)

            st.markdown('<div class="chart-section-title">Key Pairs (|r| ≥ 0.5)</div>',
                        unsafe_allow_html=True)
            insights = []
            for i, a in enumerate(labels):
                for j, b in enumerate(labels):
                    if j <= i: continue
                    v = corr_df.loc[a, b]
                    if abs(v) >= 0.5:
                        direction = ("strongly positive ↑↑" if v >= 0.7
                                     else "positive ↑" if v >= 0.5
                                     else "negative ↓" if v <= -0.5
                                     else "strongly negative ↓↓")
                        color = "#4ade80" if v > 0 else "#f87171"
                        insights.append((a, b, v, direction, color))
            if insights:
                ihtml = ""
                for a, b, v, direction, color in sorted(insights, key=lambda x: -abs(x[2])):
                    ihtml += (f'<div class="spread-row">'
                              f'<span class="spread-name"><b style="color:#dde8f5">{a}</b>'
                              f' vs <b style="color:#dde8f5">{b}</b></span>'
                              f'<span class="spread-val" style="color:{color}">'
                              f'{v:+.2f} — {direction}</span></div>')
                st.markdown(f'<div class="scorecard-wrap">{ihtml}</div>', unsafe_allow_html=True)
            else:
                st.info("No pairs exceed |0.5| — good diversification this period!")
        else:
            st.warning("Correlation data unavailable. Click ⟳ Refresh to retry.")
            if st.button("Retry Correlation"):
                st.cache_data.clear(); st.rerun()

    footer()

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — CALENDAR & NEWS
# ═══════════════════════════════════════════════════════════════════════════════
elif current_page == "calendar":
    page_header("Calendar & News",
                "Economic releases · Earnings calendar · Market headlines · Fed Watch")
    regime_banner()

    # ── Economic Calendar ─────────────────────────────────────────────────────
    sep("Upcoming Economic Releases")
    desc("Live calendar from <strong>Finnhub</strong> — confirmed dates with previous readings, "
         "consensus estimates, and actual results once published. "
         "<strong>High impact</strong> releases move equities, bonds and FX sharply. "
         f'<a href="https://www.marketwatch.com/economy-politics/calendar" target="_blank" '
         f'style="color:#22d3ee">Full calendar on MarketWatch ↗</a>')

    IMPACT_CLR = {"HIGH": "#f87171", "MEDIUM": "#f59e0b", "LOW": "#94a3b8"}
    IMPACT_BG  = {"HIGH": "rgba(248,113,113,.10)", "MEDIUM": "rgba(245,158,11,.08)",
                  "LOW":  "rgba(148,163,184,.06)"}

    if econ_cal:
        # Next 3 high-impact countdown cards
        high_evs = [e for e in econ_cal if e["impact"] == "HIGH"]
        next3    = high_evs[:3] if len(high_evs) >= 3 else econ_cal[:3]
        strip_html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px">'
        for ev in next3:
            ic  = IMPACT_CLR.get(ev["impact"], "#94a3b8")
            ibg = IMPACT_BG.get(ev["impact"], "rgba(148,163,184,.06)")
            da  = ev["days_away"]
            if   da == 0: cd = '<span style="color:#f87171;font-weight:800;font-size:.82rem">TODAY</span>'
            elif da == 1: cd = '<span style="color:#fb923c;font-weight:800;font-size:.82rem">TOMORROW</span>'
            else:         cd = f'<span style="color:#22d3ee;font-weight:700">In {da} days</span>'
            unit = ev.get("unit", "")
            def _fv(v): return f"{v:+.2f}{unit}" if isinstance(v, (int, float)) else "—"
            extras = ""
            if any(ev.get(k) is not None for k in ("prev", "estimate", "actual")):
                act_col = "#4ade80" if ev.get("actual") is not None else "#4a6a8a"
                extras = (
                    f'<div style="display:flex;gap:10px;margin-top:8px;font-family:{MONO};font-size:.65rem">'
                    f'<span style="color:#4a6a8a">Prev <span style="color:#8ab4d8">{_fv(ev.get("prev"))}</span></span>'
                    f'<span style="color:#4a6a8a">Est <span style="color:#f59e0b">{_fv(ev.get("estimate"))}</span></span>'
                    f'<span style="color:#4a6a8a">Act <span style="color:{act_col}">{_fv(ev.get("actual"))}</span></span>'
                    f'</div>')
            time_lbl = f' · {ev["time_str"]} ET' if ev.get("time_str") else ""
            strip_html += (
                f'<div style="background:{ibg};border:1px solid {ic}44;border-radius:8px;'
                f'padding:14px 16px;border-left:3px solid {ic}">'
                f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:{ic};'
                f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">'
                f'{ev["impact"]} · {ev["source"]}</div>'
                f'<div style="font-size:.88rem;font-weight:700;color:#f0f8ff;margin-bottom:4px">'
                f'{ev["name"]}</div>'
                f'<div style="font-family:{MONO};font-size:.7rem;color:#8ab4d8">'
                f'{ev["date"].strftime("%a, %d %b %Y")}{time_lbl}</div>'
                f'<div style="margin-top:5px;font-size:.73rem">{cd}</div>'
                f'{extras}</div>')
        strip_html += '</div>'
        st.markdown(strip_html, unsafe_allow_html=True)

        st.markdown('<div class="chart-section-title">Full Release Schedule</div>',
                    unsafe_allow_html=True)
        tbl_html = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                    "<thead><tr style='border-bottom:1px solid #162236'>")
        for h, align in [("Date","left"),("Time ET","center"),("Release","left"),
                          ("Impact","center"),("Prev","right"),("Estimate","right"),("Actual","right")]:
            tbl_html += (f"<th style='padding:8px 7px;color:#6a90b0;font-size:.62rem;font-weight:700;"
                         f"text-transform:uppercase;letter-spacing:.08em;text-align:{align}'>{h}</th>")
        tbl_html += "</tr></thead><tbody>"
        for ev in econ_cal:
            ic = IMPACT_CLR.get(ev["impact"], "#94a3b8")
            bbg = IMPACT_BG.get(ev["impact"], "rgba(148,163,184,.06)")
            da = ev["days_away"]
            dc = "#f87171" if da <= 1 else "#22d3ee" if da <= 7 else "#8ab4d8"
            unit = ev.get("unit", "")
            def _fval(v, col="#dde8f5"):
                if v is None: return f'<span style="color:#3a5070">—</span>'
                return (f'<span style="color:{col};font-weight:600">{v:+.2f}{unit}</span>'
                        if isinstance(v, (int, float))
                        else f'<span style="color:{col}">{v}</span>')
            act_col = "#4ade80" if ev.get("actual") is not None else "#dde8f5"
            tbl_html += (
                f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                f"<td style='padding:8px 7px;color:{dc};font-weight:600;font-size:.8rem'>"
                f"{ev['date'].strftime('%a %d %b')}</td>"
                f"<td style='padding:8px 7px;text-align:center;color:#4a6a8a;font-size:.7rem'>"
                f"{ev.get('time_str') or '—'}</td>"
                f"<td style='padding:8px 7px;color:#f0f8ff;font-size:.82rem'>{ev['name']}</td>"
                f"<td style='padding:8px 7px;text-align:center'>"
                f"<span style='background:{bbg};color:{ic};border:1px solid {ic}44;border-radius:3px;"
                f"padding:2px 7px;font-size:.6rem;font-weight:700;text-transform:uppercase'>"
                f"{ev['impact']}</span></td>"
                f"<td style='padding:8px 7px;text-align:right;font-size:.75rem'>"
                f"{_fval(ev.get('prev'), '#8ab4d8')}</td>"
                f"<td style='padding:8px 7px;text-align:right;font-size:.75rem'>"
                f"{_fval(ev.get('estimate'), '#f59e0b')}</td>"
                f"<td style='padding:8px 7px;text-align:right;font-size:.75rem'>"
                f"{_fval(ev.get('actual'), act_col)}</td></tr>")
        tbl_html += "</tbody></table>"
        st.markdown(tbl_html, unsafe_allow_html=True)
        cal_source = econ_cal[0]["source"] if econ_cal else "unavailable"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'margin-top:8px;font-family:{MONO};font-size:.62rem;color:#4a6a8a">'
            f'<span>Source: <strong style="color:#8ab4d8">{cal_source}</strong> · '
            f'Refreshed hourly · {now_sgt().strftime("%d %b %Y %H:%M")} SGT</span>'
            f'<a href="https://www.marketwatch.com/economy-politics/calendar" target="_blank" '
            f'style="color:#22d3ee;text-decoration:none;padding:3px 10px;border:1px solid '
            f'rgba(34,211,238,.3);border-radius:4px">📅 MarketWatch ↗</a></div>',
            unsafe_allow_html=True)
    else:
        st.warning("Calendar loading. Finnhub is primary, FRED is fallback. Refresh to retry.", )

    # ── News + Earnings ───────────────────────────────────────────────────────
    sep("Market Headlines & Upcoming Earnings")

    news_col, earn_col = st.columns([3, 2], gap="large")
    with news_col:
        st.markdown('<div class="chart-section-title">Latest Macro & Market Headlines (Finnhub)</div>',
                    unsafe_allow_html=True)
        if fh_news:
            for item in fh_news[:9]:
                age_str = (f"{item['age_hrs']:.0f}h ago" if item['age_hrs'] < 24
                           else f"{item['age_hrs']/24:.0f}d ago")
                url = item.get("url", "#")
                st.markdown(
                    f'<div style="padding:10px 0;border-bottom:1px solid rgba(22,34,54,.6)">'
                    f'<a href="{url}" target="_blank" style="color:#dde8f5;text-decoration:none;'
                    f'font-size:.82rem;font-weight:600;line-height:1.45;display:block">'
                    f'{item["headline"]}</a>'
                    f'<div style="font-family:{MONO};font-size:.62rem;color:#4a6a8a;margin-top:3px">'
                    f'{item.get("source","")} · {age_str}</div></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("Headlines unavailable — Finnhub may be rate-limited. Refresh to retry.")

    with earn_col:
        st.markdown('<div class="chart-section-title">Upcoming S&P 500 Earnings (Next 14 Days)</div>',
                    unsafe_allow_html=True)
        if fh_earnings:
            earn_html = (
                f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                "<thead><tr style='border-bottom:1px solid #162236'>"
                + "".join(
                    f"<th style='padding:6px 5px;color:#6a90b0;font-size:.6rem;text-transform:uppercase;"
                    f"letter-spacing:.07em;text-align:{align}'>{h}</th>"
                    for h, align in [("Symbol","left"),("Date","left"),("When","center"),("EPS Est","right")])
                + "</tr></thead><tbody>")
            for e in fh_earnings[:14]:
                da    = e["days_away"]
                dc    = "#f87171" if da == 0 else "#fb923c" if da == 1 else "#22d3ee" if da <= 5 else "#8ab4d8"
                day_s = "Today" if da == 0 else "Tomorrow" if da == 1 else f"In {da}d"
                hour_s = " BMO" if e.get("hour") == "bmo" else " AMC" if e.get("hour") == "amc" else ""
                eps_s = f"${e['eps_est']:.2f}" if e.get("eps_est") is not None else "—"
                earn_html += (
                    f"<tr style='border-bottom:1px solid rgba(22,34,54,.5)'>"
                    f"<td style='padding:6px 5px;color:#22d3ee;font-weight:700;font-size:.8rem'>"
                    f"{e['symbol']}</td>"
                    f"<td style='padding:6px 5px;color:#8ab4d8;font-size:.73rem'>"
                    f"{e['date'].strftime('%d %b')}</td>"
                    f"<td style='padding:6px 5px;text-align:center;font-size:.7rem'>"
                    f"<span style='color:{dc};font-weight:600'>{day_s}</span>"
                    f"<span style='color:#4a6a8a;font-size:.62rem'>{hour_s}</span></td>"
                    f"<td style='padding:6px 5px;text-align:right;color:#f59e0b;font-size:.77rem'>"
                    f"{eps_s}</td></tr>")
            earn_html += "</tbody></table>"
            st.markdown(earn_html, unsafe_allow_html=True)
            st.caption("BMO = Before Market Open · AMC = After Market Close")
        else:
            st.caption("No major earnings in next 14 days, or Finnhub unavailable.")

    # ── Fed Watch ─────────────────────────────────────────────────────────────
    sep("Fed Watch")
    fw1, fw2 = st.columns([1, 2], gap="large")
    with fw1:
        fomc_event = next((e for e in econ_cal if "FOMC" in e["name"]
                           and "Minute" not in e["name"]), None)
        real_rate  = round(sig["fed"] - sig["cpi"], 2)
        real_col   = "#4ade80" if real_rate > 0 else "#f87171"
        real_lbl   = "Restrictive" if real_rate > 0 else "Accommodative"
        fomc_html  = ""
        if fomc_event:
            da = fomc_event["days_away"]
            day_col = "#f87171" if da <= 3 else "#f59e0b" if da <= 14 else "#22d3ee"
            fomc_html = (
                f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid #162236">'
                f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#6a90b0;'
                f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">Next FOMC Decision</div>'
                f'<div style="font-size:.9rem;font-weight:700;color:#f0f8ff">'
                f'{fomc_event["date"].strftime("%a %d %b %Y")}</div>'
                f'<div style="font-family:{MONO};font-size:.75rem;color:{day_col};font-weight:700;'
                f'margin-top:2px">In {da} days</div></div>')
        st.markdown(
            f'<div class="risk-card"><div class="risk-title">Fed Watch</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'<div><div style="font-size:.7rem;color:#6a90b0;margin-bottom:2px">Fed Funds Rate</div>'
            f'<div style="font-family:{MONO};font-size:1.5rem;font-weight:700;color:#22d3ee">'
            f'{sig["fed"]:.2f}%</div></div>'
            f'<div style="text-align:right">'
            f'<div style="font-size:.7rem;color:#6a90b0;margin-bottom:2px">Real Rate (Fed−CPI)</div>'
            f'<div style="font-family:{MONO};font-size:1.5rem;font-weight:700;color:{real_col}">'
            f'{real_rate:+.2f}%</div>'
            f'<div style="font-family:{MONO};font-size:.67rem;color:{real_col};font-weight:700">'
            f'{real_lbl}</div></div></div>'
            f'<div class="risk-sub" style="margin-top:8px">Real rate = Fed Funds minus CPI. '
            f'Positive = policy is truly tight.</div>'
            f'{fomc_html}</div>',
            unsafe_allow_html=True)

    with fw2:
        desc("The real rate (Fed Funds minus CPI) is the single most important policy metric. "
             "When it's positive, money is genuinely expensive — the Fed is actively slowing the economy. "
             "When negative despite rate hikes, inflation is still running hotter than borrowing costs.")
        # Mini rate chart
        if "fed_rate" in dfc.columns and "cpi_yoy" in dfc.columns:
            ff = go.Figure()
            s_fed = dfc["fed_rate"].dropna()
            s_cpi = dfc["cpi_yoy"].dropna()
            if not s_fed.empty:
                ff.add_trace(go.Scatter(x=s_fed.index, y=s_fed.values, name="Fed Rate",
                    line=dict(color=C["blue"], width=2)))
            if not s_cpi.empty:
                ff.add_trace(go.Scatter(x=s_cpi.index, y=s_cpi.values, name="CPI YoY",
                    line=dict(color=C["red"], width=2, dash="dot")))
            ff.add_hline(y=2, line_dash="dash", line_color="rgba(148,163,184,.25)",
                         annotation_text="2% target", annotation_font_size=10)
            theme(ff, h=240, title="Fed Rate vs CPI", fullscreen_bg=True)
            st.plotly_chart(ff, use_container_width=True)

    footer()

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — SINGAPORE HUB
# ═══════════════════════════════════════════════════════════════════════════════
elif current_page == "singapore":
    page_header("Singapore Hub",
                "Session clock · STI · SGX banks & blue chips · S-REITs · SGD · DXY · Global PMI · Smart Money")

    # ── Custom time range for all SG charts ────────────────────────────────
    with st.expander("Chart Time Range Settings", expanded=False):
        sg_tr1, sg_tr2, sg_tr3 = st.columns([1, 1, 2])
        with sg_tr1:
            sg_preset = st.selectbox(
                "Quick preset",
                ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "3 Years", "Custom"],
                index=2, key="sg_time_preset"
            )
        with sg_tr2:
            sg_interval = st.selectbox(
                "Interval",
                ["1d", "1wk", "1mo"],
                index=0, key="sg_interval"
            )
        _sg_offsets = {"1 Month": 30, "3 Months": 91, "6 Months": 182,
                       "1 Year": 365, "2 Years": 730, "3 Years": 1095}
        if sg_preset == "Custom":
            _sc1, _sc2 = st.columns(2)
            with _sc1:
                sg_from = st.date_input("From", value=date.today()-timedelta(days=182),
                                         min_value=date(2010,1,1), max_value=date.today(), key="sg_from")
            with _sc2:
                sg_to   = st.date_input("To",   value=date.today(),
                                         min_value=date(2010,1,1), max_value=date.today(), key="sg_to")
            sg_period_str = None
            sg_start_str  = sg_from.strftime("%Y-%m-%d")
            sg_end_str    = sg_to.strftime("%Y-%m-%d")
            sg_label      = f"{sg_from.strftime('%d %b %y')} – {sg_to.strftime('%d %b %y')}"
        else:
            sg_period_str = {30:"1mo", 91:"3mo", 182:"6mo", 365:"1y", 730:"2y", 1095:"3y"}[_sg_offsets[sg_preset]]
            sg_start_str  = None
            sg_end_str    = None
            sg_label      = sg_preset

    def _sg_hist(ticker, period=None, start=None, end=None, interval="1d"):
        """Fetch OHLCV for a SG ticker with custom range support."""
        try:
            if start and end:
                h = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=True)
            else:
                h = yf.Ticker(ticker).history(period=period or "6mo", interval=interval, auto_adjust=True)
            if h.empty:
                return None
            h.index = pd.to_datetime(h.index)
            if h.index.tz is not None:
                h.index = h.index.tz_localize(None)
            return h
        except Exception:
            return None

    def _mini_chart(hist, color, h=200, title=None, show_volume=False):
        """Render a clean mini Plotly chart from a history DataFrame."""
        if hist is None or hist.empty:
            st.caption("Data unavailable")
            return
        closes = hist["Close"].dropna()
        if closes.empty:
            st.caption("No data")
            return
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=closes.index, y=closes.values,
            name=title or "Price",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[j:j+2],16)) for j in (0,2,4))},.06)"
        ))
        if show_volume and "Volume" in hist.columns:
            vols = hist["Volume"].dropna()
            if vols.sum() > 0:
                vcolors = ["rgba(74,222,128,.3)" if c >= o else "rgba(248,113,113,.3)"
                           for c, o in zip(hist["Close"], hist["Open"])]
                fig.add_trace(go.Bar(x=vols.index, y=vols.values,
                                     marker_color=vcolors, yaxis="y2",
                                     showlegend=False, name="Volume"))
                fig.update_layout(yaxis2=dict(overlaying="y", side="right",
                                              showgrid=False, showticklabels=False))
        theme(fig, h=h, title=title, fullscreen_bg=True)
        fig.update_layout(margin=dict(l=8, r=8, t=36 if title else 10, b=16), showlegend=False,
                          xaxis_rangeslider_visible=False)
        fig.update_xaxes(tickfont=dict(size=11, color="#6a90b0"))
        fig.update_yaxes(tickfont=dict(size=11, color="#6a90b0"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f'<div style="font-family:{MONO};font-size:.7rem;color:#4a7090;margin-bottom:6px">'
        f'Charts showing: <strong style="color:#22d3ee">{sg_label}</strong> · Interval: <strong style="color:#22d3ee">{sg_interval}</strong>'
        f'</div>', unsafe_allow_html=True)

    # ── Market Session Clock ──────────────────────────────────────────────
    sep("Live Market Session Clock")
    desc("Which exchanges are open <strong>right now</strong> in SGT (UTC+8). "
         "The <strong>London–NY overlap (21:30–00:30 SGT)</strong> is peak global liquidity. "
         "SGX morning session 9:00–12:30 SGT, afternoon 14:00–17:00 SGT.")

    sgt_now_str = now_sgt().strftime("%H:%M:%S SGT · %a %d %b %Y")
    st.markdown(
        f'<div style="font-family:{MONO};font-size:.78rem;color:#22d3ee;margin-bottom:10px;font-weight:700">'
        f'{sgt_now_str}</div>', unsafe_allow_html=True)

    sess_cols = st.columns(len(session_status))
    for i, (market, info) in enumerate(session_status.items()):
        with sess_cols[i]:
            is_open = info["status"] == "OPEN"
            col_rgb = ','.join(str(int(info['color'].lstrip('#')[j:j+2], 16)) for j in (0,2,4))
            bg_col  = f"rgba({col_rgb},.10)" if is_open else "#0c1a2e"
            bd_col  = info["color"] if is_open else "#162236"
            pulse   = (
                f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                f'background:{info["color"]};animation:blink 1.5s infinite;margin-right:5px"></span>'
                if is_open else
                f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                f'background:#2a4a6a;margin-right:5px"></span>'
            )
            st.markdown(
                f'<div style="background:{bg_col};border:1px solid {bd_col};border-radius:8px;'
                f'padding:12px 13px;border-top:2px solid {bd_col}">'
                f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#6a90b0;'
                f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">{market}</div>'
                f'<div style="display:flex;align-items:center;margin-bottom:4px">'
                f'{pulse}<span style="font-family:{MONO};font-size:.8rem;font-weight:700;'
                f'color:{info["color"] if is_open else "#4a6a8a"}">{'OPEN' if is_open else 'CLOSED'}</span></div>'
                f'<div style="font-family:{MONO};font-size:.62rem;color:#4a6a8a;margin-bottom:2px">'
                f'Local: {info["local_time"]} {info["local_tz_abbr"]}</div>'
                f'<div style="font-family:{MONO};font-size:.62rem;color:#6a90b0">'
                f'SGT: {info["sgt_open"]}–{info["sgt_close"]}</div>'
                f'<div style="font-family:{MONO};font-size:.63rem;color:{info["color"]};'
                f'margin-top:4px;font-weight:600">{info["time_str"]}</div>'
                f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-family:{MONO};font-size:.61rem;color:#2a4a6a;margin-top:6px">'
        f'Peak liquidity windows: '
        f'<span style="color:#22d3ee">SGX 9:00–17:00</span> · '
        f'<span style="color:#a78bfa">London open ~15:00</span> · '
        f'<span style="color:#f87171">NY open ~21:30</span> · '
        f'<span style="color:#f59e0b">London-NY overlap 21:30–00:30 SGT</span></div>',
        unsafe_allow_html=True)

    # ── STI + SGD ──────────────────────────────────────────────────────────
    sep("STI Index & SGD Currency")
    sti_col_c2, sgd_col2, mas_col2 = st.columns(3, gap="large")

    with sti_col_c2:
        st.markdown('<div class="chart-section-title">Straits Times Index</div>', unsafe_allow_html=True)
        sti_h = _sg_hist("^STI", period=sg_period_str, start=sg_start_str,
                         end=sg_end_str, interval=sg_interval)
        if sti_h is not None and not sti_h.empty:
            c_sti = sti_h["Close"].dropna()
            now_sti  = float(c_sti.iloc[-1])
            prev_sti = float(c_sti.iloc[-2]) if len(c_sti) > 1 else now_sti
            pct_sti  = round((now_sti - prev_sti) / prev_sti * 100, 2) if prev_sti else 0
            ytd_s    = c_sti[c_sti.index >= pd.Timestamp(f"{datetime.today().year}-01-01")]
            ytd_sti  = round((now_sti / float(ytd_s.iloc[0]) - 1) * 100, 2) if len(ytd_s) > 0 else 0
            hi52 = float(c_sti.max()); lo52 = float(c_sti.min())
            pp = (now_sti - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else 50
            sc = "#4ade80" if pct_sti >= 0 else "#f87171"
            m1_sti = float(c_sti.iloc[-22]) if len(c_sti) > 22 else float(c_sti.iloc[0])
            pct_1m = round((now_sti - m1_sti) / m1_sti * 100, 2) if m1_sti else 0
            st.markdown(
                f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                f'padding:14px;border-top:2px solid #22d3ee">'
                f'<div style="font-family:{MONO};font-size:1.5rem;font-weight:700;color:#f0f8ff">{now_sti:,.2f}</div>'
                f'<div style="display:flex;gap:12px;margin-top:5px;font-family:{MONO};font-size:.7rem">'
                f'<span style="color:{sc};font-weight:700">1D {"+" if pct_sti>=0 else ""}{pct_sti:.2f}%</span>'
                f'<span style="color:{"#4ade80" if pct_1m>=0 else "#f87171"}">1M {"+" if pct_1m>=0 else ""}{pct_1m:.2f}%</span>'
                f'<span style="color:{"#4ade80" if ytd_sti>=0 else "#f87171"}">YTD {"+" if ytd_sti>=0 else ""}{ytd_sti:.2f}%</span></div>'
                f'<div style="background:#080f1c;border-radius:3px;height:5px;margin:8px 0">'
                f'<div style="width:{pp:.0f}%;height:5px;border-radius:3px;background:linear-gradient(90deg,#f87171,#f59e0b,#4ade80)"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-family:{MONO};font-size:.58rem;color:#4a6a8a">'
                f'<span>Lo {lo52:,.1f}</span><span style="color:#22d3ee">{pp:.0f}%ile</span><span>Hi {hi52:,.1f}</span></div>'
                f'</div>', unsafe_allow_html=True)
            _mini_chart(sti_h, "#22d3ee", h=220, title=f"STI — {sg_label}", show_volume=True)
        else:
            st.caption("STI data loading…")

    with sgd_col2:
        st.markdown('<div class="chart-section-title">SGD Currency Pairs</div>', unsafe_allow_html=True)
        SGD_PAIRS2 = {"USD/SGD":"SGD=X","EUR/SGD":"EURSGD=X","GBP/SGD":"GBPSGD=X",
                      "JPY/SGD":"JPYSGD=X","AUD/SGD":"AUDSGD=X","CNY/SGD":"CNYSGD=X"}
        sgd_h2 = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                  f"<thead><tr style='border-bottom:1px solid #162236'>"
                  + "".join(f"<th style='padding:5px 6px;color:#6a90b0;font-size:.58rem;text-transform:uppercase;text-align:{a}'>{h}</th>"
                            for h,a in [("Pair","left"),("Rate","right"),("1D","right"),("1W","right")])
                  + "</tr></thead><tbody>")
        for pair, ticker in SGD_PAIRS2.items():
            try:
                h = yf.Ticker(ticker).history(period="5d")
                if h.empty: continue
                c=h["Close"].dropna(); now=float(c.iloc[-1]); prev=float(c.iloc[-2]) if len(c)>1 else now
                w1=float(c.iloc[-6]) if len(c)>=6 else float(c.iloc[0])
                p1d=round((now-prev)/prev*100,3) if prev else 0
                p1w=round((now-w1)/w1*100,3) if w1 else 0
                c1="#4ade80" if p1d>0 else "#f87171" if p1d<0 else "#94a3b8"
                c2="#4ade80" if p1w>0 else "#f87171" if p1w<0 else "#94a3b8"
                sgd_h2 += (f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                           f"<td style='padding:7px 6px;color:#dde8f5;font-size:.8rem;font-weight:600'>{pair}</td>"
                           f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.82rem;font-weight:700;color:#22d3ee'>{now:.4f}</td>"
                           f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.72rem;font-weight:700;color:{c1}'>{'+'if p1d>0 else''}{p1d:.2f}%</td>"
                           f"<td style='padding:7px 6px;text-align:right;font-family:{MONO};font-size:.72rem;font-weight:700;color:{c2}'>{'+'if p1w>0 else''}{p1w:.2f}%</td></tr>")
            except Exception: pass
        sgd_h2 += "</tbody></table>"
        st.markdown(sgd_h2, unsafe_allow_html=True)
        # SGD chart
        sgd_hist = _sg_hist("SGD=X", period=sg_period_str, start=sg_start_str,
                             end=sg_end_str, interval=sg_interval)
        _mini_chart(sgd_hist, "#22d3ee", h=160, title=f"USD/SGD — {sg_label}")
        st.caption("MAS manages SGD via NEER basket. Strong SGD = tightening. USD/SGD >1.38 = stress signal.")

    with mas_col2:
        st.markdown('<div class="chart-section-title">Singapore Macro Context</div>', unsafe_allow_html=True)
        sg_items = [
            ("MAS Policy Tool",      "SGD NEER slope/width",   "MAS adjusts exchange rate band, not interest rates."),
            ("GDP Sensitivity",      "Trade & electronics",    "Highly exposed to global semicon cycle and US/China demand."),
            ("Inflation Driver",     "Imported inflation",     "Core CPI excludes accommodation & private transport."),
            ("Key Risk",             "USD/CNY direction",      "SGD tracks CNY closely. China slowdown = SGD pressure."),
            ("REIT Sensitivity",     "Rate-sensitive",         "S-REITs fall when rates rise. MAS easing = REIT bullish."),
            ("Banks NIM",            "Rate-sensitive profits", "DBS/OCBC/UOB NIMs expand with higher USD/SGD rates."),
            ("Trade Dependency",     "~170% GDP",              "Singapore is one of the world's most open economies."),
            ("Next MAS Review",      "Oct / Apr",              "MAS reviews monetary policy twice a year. Watch NEER slope."),
        ]
        mas_h2 = f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:12px">'
        for title_sg, val_sg, note_sg in sg_items:
            mas_h2 += (f'<div style="padding:7px 0;border-bottom:1px solid rgba(22,34,54,.7)">'
                       f'<div style="display:flex;justify-content:space-between"><span style="color:#dde8f5;font-size:.77rem;font-weight:600">{title_sg}</span>'
                       f'<span style="color:#22d3ee;font-family:{MONO};font-size:.7rem;font-weight:700">{val_sg}</span></div>'
                       f'<div style="color:#4a6a8a;font-size:.63rem;margin-top:1px">{note_sg}</div></div>')
        mas_h2 += '</div>'
        st.markdown(mas_h2, unsafe_allow_html=True)

    # ── Singapore Banks ────────────────────────────────────────────────────
    sep("Singapore Banks — DBS · OCBC · UOB")
    desc("The three local banks make up ~50% of the STI. They are rate-sensitive — "
         "higher rates expand NIMs (net interest margins). "
         "DBS is most international; OCBC has insurance income via Great Eastern; UOB leads ASEAN expansion.")

    if sgx_data:
        bank_d = {k: v for k, v in sgx_data.items() if v["cat"] == "bank"}
        if bank_d:
            bc = st.columns(3)
            for i, (name, d) in enumerate(bank_d.items()):
                with bc[i]:
                    pc = d["pct_1d"]; pcc = "#4ade80" if pc >= 0 else "#f87171"
                    st.markdown(
                        f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                        f'padding:13px;border-top:2px solid {d["color"]}">'
                        f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#6a90b0;'
                        f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">{name}</div>'
                        f'<div style="font-family:{MONO};font-size:1.35rem;font-weight:700;color:#f0f8ff">S${d["price"]:.2f}</div>'
                        f'<div style="display:flex;gap:9px;margin-top:4px;font-family:{MONO};font-size:.68rem">'
                        f'<span style="color:{pcc};font-weight:700">1D {"+" if pc>=0 else ""}{pc:.2f}%</span>'
                        f'<span style="color:{"#4ade80" if d["pct_1m"]>=0 else "#f87171"}">1M {"+" if d["pct_1m"]>=0 else ""}{d["pct_1m"]:.2f}%</span>'
                        f'<span style="color:{"#4ade80" if d["pct_ytd"]>=0 else "#f87171"}">YTD {"+" if d["pct_ytd"]>=0 else ""}{d["pct_ytd"]:.2f}%</span></div>'
                        f'</div>', unsafe_allow_html=True)
                    # Use custom range chart
                    bank_hist = _sg_hist(d["ticker"], period=sg_period_str,
                                         start=sg_start_str, end=sg_end_str, interval=sg_interval)
                    _mini_chart(bank_hist, d["color"], h=160)

    # ── STI Blue Chips ─────────────────────────────────────────────────────
    sep("STI Blue Chip Stocks")
    desc("Major non-bank STI constituents spanning industrials, telecoms, property, aviation and gaming. "
         "These stocks drive the index alongside the three banks. "
         "Use these to gauge breadth — when blue chips are up but banks down, it signals sector rotation within the STI.")

    if sgx_data:
        blue_d = {k: v for k, v in sgx_data.items() if v["cat"] == "blue"}
        if blue_d:
            # Price table
            bl_html = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                       "<thead><tr style='border-bottom:2px solid #162236'>"
                       + "".join(f"<th style='padding:7px 8px;color:#6a90b0;font-size:.62rem;text-transform:uppercase;text-align:{a}'>{h}</th>"
                                 for h, a in [("Stock","left"),("Ticker","left"),("Price","right"),("1D","right"),("1M","right"),("YTD","right")])
                       + "</tr></thead><tbody>")
            for name, d in blue_d.items():
                pc=d["pct_1d"]; pcc="#4ade80" if pc>=0 else "#f87171"
                m1c="#4ade80" if d["pct_1m"]>=0 else "#f87171"
                ytdc="#4ade80" if d["pct_ytd"]>=0 else "#f87171"
                bl_html += (f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                            f"<td style='padding:7px 8px'><span style='color:#f0f8ff;font-size:.82rem;font-weight:600'>{name}</span></td>"
                            f"<td style='padding:7px 8px'><span style='color:#4a6a8a;font-size:.7rem;font-family:{MONO}'>{d['ticker']}</span></td>"
                            f"<td style='padding:7px 8px;text-align:right;color:#22d3ee;font-family:{MONO};font-size:.8rem;font-weight:700'>S${d['price']:.3f}</td>"
                            f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{pcc}'>{'+'if pc>=0 else''}{pc:.2f}%</td>"
                            f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{m1c}'>{'+'if d['pct_1m']>=0 else''}{d['pct_1m']:.2f}%</td>"
                            f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{ytdc}'>{'+'if d['pct_ytd']>=0 else''}{d['pct_ytd']:.2f}%</td></tr>")
            bl_html += "</tbody></table>"
            st.markdown(bl_html, unsafe_allow_html=True)

            # Mini charts for top 4 blue chips
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-section-title">Blue Chip Price Charts</div>', unsafe_allow_html=True)
            bl_items = list(blue_d.items())
            for row_start in range(0, min(len(bl_items), 8), 4):
                bc4 = st.columns(4)
                for j, (name, d) in enumerate(bl_items[row_start:row_start+4]):
                    with bc4[j]:
                        bh = _sg_hist(d["ticker"], period=sg_period_str,
                                       start=sg_start_str, end=sg_end_str, interval=sg_interval)
                        pc = d["pct_1d"]
                        st.markdown(
                            f'<div style="font-family:{MONO};font-size:.62rem;color:#6a90b0;margin-bottom:2px">'
                            f'{name} · <span style="color:{"#4ade80" if pc>=0 else "#f87171"};font-weight:700">'
                            f'{"+" if pc>=0 else ""}{pc:.2f}%</span></div>', unsafe_allow_html=True)
                        _mini_chart(bh, d["color"], h=140)

    # ── S-REITs ────────────────────────────────────────────────────────────
    sep("S-REITs — Singapore Real Estate Investment Trusts")
    desc("S-REITs are the most popular income asset class for Singapore retail investors. "
         "They distribute ≥90% of taxable income as dividends — typical yields 4–8%. "
         "<strong>Rate sensitivity</strong>: REITs fall when rates rise (higher discount rate = lower valuations). "
         "MAS easing is directly bullish for S-REITs. Watch DPU (Distribution Per Unit) growth and occupancy rates.")

    if sgx_data:
        reit_d = {k: v for k, v in sgx_data.items() if v["cat"] == "reit"}
        if reit_d:
            rh = (f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}'>"
                  "<thead><tr style='border-bottom:2px solid #162236'>"
                  + "".join(f"<th style='padding:7px 8px;color:#6a90b0;font-size:.62rem;text-transform:uppercase;text-align:{a}'>{h}</th>"
                            for h, a in [("REIT","left"),("Price","right"),("1D","right"),("1M","right"),("YTD","right")])
                  + "</tr></thead><tbody>")
            for name, d in reit_d.items():
                pc=d["pct_1d"]; pcc="#4ade80" if pc>=0 else "#f87171"
                m1c="#4ade80" if d["pct_1m"]>=0 else "#f87171"
                ytdc="#4ade80" if d["pct_ytd"]>=0 else "#f87171"
                rh += (f"<tr style='border-bottom:1px solid rgba(22,34,54,.6)'>"
                       f"<td style='padding:7px 8px'><span style='color:#f0f8ff;font-size:.82rem;font-weight:600'>{name}</span>"
                       f"<span style='color:#4a6a8a;font-size:.64rem;margin-left:6px;font-family:{MONO}'>{d['ticker']}</span></td>"
                       f"<td style='padding:7px 8px;text-align:right;color:#22d3ee;font-family:{MONO};font-size:.8rem;font-weight:700'>S${d['price']:.3f}</td>"
                       f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{pcc}'>{'+'if pc>=0 else''}{pc:.2f}%</td>"
                       f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{m1c}'>{'+'if d['pct_1m']>=0 else''}{d['pct_1m']:.2f}%</td>"
                       f"<td style='padding:7px 8px;text-align:right;font-family:{MONO};font-size:.75rem;font-weight:700;color:{ytdc}'>{'+'if d['pct_ytd']>=0 else''}{d['pct_ytd']:.2f}%</td></tr>")
            rh += "</tbody></table>"
            st.markdown(rh, unsafe_allow_html=True)
            st.caption("S-REITs: rate-sensitive · Watch MAS policy direction · DPU growth · Occupancy rates")

            # REIT charts
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-section-title">REIT Price Charts</div>', unsafe_allow_html=True)
            reit_items = list(reit_d.items())
            for row_start in range(0, min(len(reit_items), 8), 4):
                rc4 = st.columns(4)
                for j, (name, d) in enumerate(reit_items[row_start:row_start+4]):
                    with rc4[j]:
                        rh2 = _sg_hist(d["ticker"], period=sg_period_str,
                                        start=sg_start_str, end=sg_end_str, interval=sg_interval)
                        st.markdown(
                            f'<div style="font-family:{MONO};font-size:.62rem;color:#6a90b0;margin-bottom:2px">{name}</div>',
                            unsafe_allow_html=True)
                        _mini_chart(rh2, d["color"], h=140)

    # ── DXY ───────────────────────────────────────────────────────────────
    sep("DXY Dollar Strength Monitor")
    desc("DXY >105 = strong USD = headwind for EM, commodities, Asian equities. "
         "For Singapore: a strong USD tightens financial conditions and affects USD-denominated corporate debt. "
         "MAS keeps SGD broadly tracking a basket where USD is the dominant component.")

    if dxy_data:
        dx1, dx2 = st.columns([1, 2], gap="large")
        with dx1:
            dxy_c = ("#f87171" if dxy_data["price"] > 105 else "#f59e0b" if dxy_data["price"] > 100
                     else "#4ade80" if dxy_data["price"] < 97 else "#94a3b8")
            dxy_r = ("Strong USD — Headwind for EM/Asia" if dxy_data["price"] > 105
                     else "Elevated — Watch exposure" if dxy_data["price"] > 100
                     else "Neutral" if dxy_data["price"] > 97
                     else "Weak USD — Tailwind for EM/gold")
            st.markdown(
                f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                f'padding:16px;border-top:2px solid {dxy_c}">'
                f'<div style="font-family:{MONO};font-size:.62rem;color:#6a90b0;text-transform:uppercase;'
                f'letter-spacing:.1em;margin-bottom:7px">DXY Index</div>'
                f'<div style="font-family:{MONO};font-size:1.9rem;font-weight:700;color:{dxy_c}">{dxy_data["price"]:.2f}</div>'
                f'<div style="display:flex;gap:10px;margin-top:6px;font-family:{MONO};font-size:.68rem">'
                f'<span style="color:{"#4ade80" if dxy_data["pct_1d"]>=0 else "#f87171"};font-weight:700">'
                f'1D {"+" if dxy_data["pct_1d"]>=0 else ""}{dxy_data["pct_1d"]:.2f}%</span>'
                f'<span style="color:{"#4ade80" if dxy_data["pct_1m"]>=0 else "#f87171"}">'
                f'1M {"+" if dxy_data["pct_1m"]>=0 else ""}{dxy_data["pct_1m"]:.2f}%</span>'
                f'<span style="color:{"#4ade80" if dxy_data["pct_3m"]>=0 else "#f87171"}">'
                f'3M {"+" if dxy_data["pct_3m"]>=0 else ""}{dxy_data["pct_3m"]:.2f}%</span></div>'
                f'<div style="background:#080f1c;border-radius:3px;height:5px;margin:8px 0">'
                f'<div style="width:{dxy_data["pct_pos"]:.0f}%;height:5px;border-radius:3px;'
                f'background:linear-gradient(90deg,#4ade80,#f59e0b,#f87171)"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-family:{MONO};'
                f'font-size:.58rem;color:#4a6a8a;margin-bottom:8px">'
                f'<span>52W Lo {dxy_data["lo52"]:.2f}</span>'
                f'<span style="color:{dxy_c}">{dxy_data["pct_pos"]:.0f}%ile</span>'
                f'<span>52W Hi {dxy_data["hi52"]:.2f}</span></div>'
                f'<div style="font-size:.7rem;color:{dxy_c};font-weight:600">{dxy_r}</div>'
                f'<div style="margin-top:10px;font-family:{MONO};font-size:.6rem;line-height:1.8;color:#4a6a8a">'
                f'Gold: {"Down pressure" if dxy_data["price"]>102 else "Tailwind"} · '
                f'EM Equities: {"Headwind" if dxy_data["price"]>102 else "Tailwind"} · '
                f'STI: {"Moderate headwind" if dxy_data["price"]>104 else "Neutral"}'
                f'</div></div>', unsafe_allow_html=True)
        with dx2:
            dxy_hist = _sg_hist("DX-Y.NYB", period=sg_period_str,
                                 start=sg_start_str, end=sg_end_str, interval=sg_interval)
            _mini_chart(dxy_hist, "#22d3ee", h=320, title=f"DXY — {sg_label}")

    # ── Global PMI ─────────────────────────────────────────────────────────
    sep("Global PMI Dashboard")
    desc("<strong>PMI > 50 = expansion</strong>, < 50 = contraction. "
         "This is the most-watched leading indicator globally, leading GDP by 1–2 quarters. "
         "For Singapore, US and China PMI are critical — they directly drive semiconductor and NODX demand.")

    if global_pmi:
        pmi_c = st.columns(min(len(global_pmi), 4))
        for i, (label, d) in enumerate(global_pmi.items()):
            with pmi_c[i % 4]:
                pmi_color = ("#4ade80" if d["value"] >= 52 else "#86efac" if d["value"] >= 50
                             else "#fb923c" if d["value"] >= 48 else "#f87171")
                pmi_lbl = ("Expanding" if d["value"] >= 52 else "Marginal Growth" if d["value"] >= 50
                           else "Contraction" if d["value"] >= 48 else "Sharp Contraction")
                dc = d.get("delta"); dc_c = "#4ade80" if dc and dc > 0 else "#f87171" if dc and dc < 0 else "#94a3b8"
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                    f'padding:13px;border-top:2px solid {pmi_color}">'
                    f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#6a90b0;'
                    f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px">{label}</div>'
                    f'<div style="font-family:{MONO};font-size:1.55rem;font-weight:700;color:{pmi_color}">{d["value"]:.1f}</div>'
                    f'<div style="display:flex;justify-content:space-between;margin-top:4px">'
                    f'<span style="font-size:.7rem;color:{pmi_color};font-weight:600">{pmi_lbl}</span>'
                    f'<span style="font-family:{MONO};font-size:.68rem;color:{dc_c};font-weight:600">'
                    f'{"+" if dc and dc>0 else ""}{dc:.1f} vs prev</span></div>'
                    f'<div style="font-family:{MONO};font-size:.58rem;color:#4a6a8a;margin-top:4px">50 = expansion threshold</div>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.info("PMI data loading from FRED. Refresh to retry.")

    # ── Smart Money & Institutional Flow ─────────────────────────────────
    sep("Smart Money & Institutional Flow Indicators")
    desc("These ETF ratios track whether institutional capital is moving toward or away from risk. "
         "<strong>SPY/RSP</strong>: mega-cap vs equal-weight — when mega-caps dominate, it's often defensive. "
         "<strong>HYG/IEF</strong>: credit risk vs safe haven — rising = institutional risk appetite. "
         "These are standard tools used by quant hedge funds and institutional PMs daily.")

    if smart_money:
        sm_c = st.columns(2)
        for i, (label, d) in enumerate(smart_money.items()):
            with sm_c[i % 2]:
                t1m = d["trend_1m"]; t3m = d["trend_3m"]
                is_rop = (label.startswith("HYG") or label.startswith("XLK") or label.startswith("EEM"))
                sig_sm = ("Risk-On" if (t1m > 1 and is_rop) or (t1m < -1 and not is_rop)
                          else "Risk-Off" if (t1m < -1 and is_rop) or (t1m > 1 and not is_rop)
                          else "Neutral")
                sc_sm = "#4ade80" if "On" in sig_sm else "#f87171" if "Off" in sig_sm else "#94a3b8"
                tc1 = "#4ade80" if t1m > 1 else "#f87171" if t1m < -1 else "#94a3b8"
                tc3 = "#4ade80" if t3m > 2 else "#f87171" if t3m < -2 else "#94a3b8"
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:13px;margin-bottom:7px">'
                    f'<div style="font-family:{MONO};font-size:.6rem;font-weight:700;color:#6a90b0;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px">{label}</div>'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">'
                    f'<span style="font-family:{MONO};font-size:.82rem;font-weight:700;color:#22d3ee">Ratio: {d["ratio"]:.4f}</span>'
                    f'<span style="font-family:{MONO};font-size:.72rem;font-weight:700;color:{sc_sm}">{sig_sm}</span></div>'
                    f'<div style="display:flex;gap:12px;font-family:{MONO};font-size:.66rem">'
                    f'<span style="color:{tc1}">1M: {"+" if t1m>=0 else ""}{t1m:.2f}%</span>'
                    f'<span style="color:{tc3}">3M: {"+" if t3m>=0 else ""}{t3m:.2f}%</span></div>'
                    f'<div style="font-size:.65rem;color:#4a6a8a;margin-top:5px">{d["interp"]}</div>'
                    f'</div>', unsafe_allow_html=True)
                if d.get("hist") is not None and len(d["hist"]) > 5:
                    sm_hist_df = pd.DataFrame({"Close": d["hist"]})
                    _mini_chart(sm_hist_df, sc_sm, h=140)

    footer()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 7 — Crypto & Volatility
# ─────────────────────────────────────────────────────────────────────────────
elif current_page == "crypto_vol":
    page_header("Crypto & Volatility",
                "Bitcoin · Ethereum · Altcoins · Volatility Risk Premium · Options sentiment")

    # ── Custom time range ─────────────────────────────────────────────────
    with st.expander("Chart Time Range Settings", expanded=False):
        cv_tr1, cv_tr2 = st.columns(2)
        with cv_tr1:
            cv_preset = st.selectbox(
                "Quick preset",
                ["7 Days", "1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "Custom"],
                index=2, key="cv_time_preset"
            )
        with cv_tr2:
            cv_interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0, key="cv_interval")
        _cv_offsets = {"7 Days": "7d", "1 Month": "1mo", "3 Months": "3mo",
                       "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y"}
        if cv_preset == "Custom":
            _cv1, _cv2 = st.columns(2)
            with _cv1:
                cv_from = st.date_input("From", value=date.today()-timedelta(days=91),
                                         min_value=date(2015,1,1), max_value=date.today(), key="cv_from")
            with _cv2:
                cv_to   = st.date_input("To",   value=date.today(),
                                         min_value=date(2015,1,1), max_value=date.today(), key="cv_to")
            cv_period = None
            cv_start_str = cv_from.strftime("%Y-%m-%d")
            cv_end_str   = cv_to.strftime("%Y-%m-%d")
            cv_label     = f"{cv_from.strftime('%d %b %y')} – {cv_to.strftime('%d %b %y')}"
        else:
            cv_period    = _cv_offsets[cv_preset]
            cv_start_str = None
            cv_end_str   = None
            cv_label     = cv_preset

    def _cv_hist(ticker, period=None, start=None, end=None, interval="1d"):
        try:
            if start and end:
                h = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=True)
            else:
                h = yf.Ticker(ticker).history(period=period or "3mo", interval=interval, auto_adjust=True)
            if h.empty: return None
            h.index = pd.to_datetime(h.index)
            if h.index.tz is not None: h.index = h.index.tz_localize(None)
            return h
        except Exception: return None

    st.markdown(
        f'<div style="font-family:{MONO};font-size:.7rem;color:#4a7090;margin-bottom:6px">'
        f'Charts showing: <strong style="color:#22d3ee">{cv_label}</strong> · Interval: <strong style="color:#22d3ee">{cv_interval}</strong>'
        f'</div>', unsafe_allow_html=True)

    # ── Crypto Dashboard ──────────────────────────────────────────────────
    sep("Crypto Market Dashboard")
    desc("Crypto markets are increasingly correlated with global risk appetite and liquidity cycles. "
         "Bitcoin acts as a macro risk asset — it tends to sell with equities in risk-off environments "
         "and rallies with liquidity expansions. "
         "<strong>Singapore context:</strong> MAS has progressive crypto regulations. "
         "Coinbase, Crypto.com and others hold MAS Major Payment Institution licences.")

    if crypto_data:
        cc = st.columns(5)
        for i, (name, d) in enumerate(crypto_data.items()):
            with cc[i]:
                pc = d["pct_1d"]; pcc = "#4ade80" if pc >= 0 else "#f87171"
                p_fmt = f"${d['price']:,.0f}" if d["price"] > 100 else f"${d['price']:.4f}"
                st.markdown(
                    f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;'
                    f'padding:12px;border-top:2px solid {d["color"]}">'
                    f'<div style="font-family:{MONO};font-size:.58rem;font-weight:700;color:#6a90b0;'
                    f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">{name}</div>'
                    f'<div style="font-family:{MONO};font-size:1rem;font-weight:700;color:#f0f8ff">{p_fmt}</div>'
                    f'<div style="display:flex;gap:6px;margin-top:3px;font-family:{MONO};font-size:.63rem">'
                    f'<span style="color:{pcc};font-weight:700">1D {"+" if pc>=0 else ""}{pc:.1f}%</span>'
                    f'<span style="color:{"#4ade80" if d["pct_1w"]>=0 else "#f87171"}">1W {"+" if d["pct_1w"]>=0 else ""}{d["pct_1w"]:.1f}%</span>'
                    f'<span style="color:{"#4ade80" if d["pct_ytd"]>=0 else "#f87171"}">YTD {"+" if d["pct_ytd"]>=0 else ""}{d["pct_ytd"]:.1f}%</span>'
                    f'</div></div>', unsafe_allow_html=True)

        # Individual crypto charts with custom range
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="chart-section-title">Crypto Price Charts</div>', unsafe_allow_html=True)
        cr_items = list(CRYPTO_TICKERS.items())
        for row_start in range(0, len(cr_items), 3):
            cr3 = st.columns(3)
            for j, (name, (ticker, color)) in enumerate(cr_items[row_start:row_start+3]):
                with cr3[j]:
                    cr_h = _cv_hist(ticker, period=cv_period,
                                     start=cv_start_str, end=cv_end_str, interval=cv_interval)
                    st.markdown(
                        f'<div style="font-family:{MONO};font-size:.65rem;color:#8ab4d8;font-weight:700;margin-bottom:4px">{name}</div>',
                        unsafe_allow_html=True)
                    if cr_h is not None:
                        closes = cr_h["Close"].dropna()
                        fig_cr2 = go.Figure()
                        fig_cr2.add_trace(go.Scatter(
                            x=closes.index, y=closes.values, name=name,
                            line=dict(color=color, width=2),
                            fill="tozeroy",
                            fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[j2:j2+2],16)) for j2 in (0,2,4))},.07)"
                        ))
                        theme(fig_cr2, h=240, title=f"{name} — {cv_label}", fullscreen_bg=True)
                        fig_cr2.update_layout(margin=dict(l=8,r=8,t=36,b=16), showlegend=False,
                                              xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig_cr2, use_container_width=True)
                    else:
                        st.caption("Data unavailable")

        # Normalised performance chart
        st.markdown('<div class="chart-section-title">Normalised Performance Comparison (Base 100)</div>', unsafe_allow_html=True)
        fig_norm = go.Figure()
        for name, (ticker, color) in cr_items:
            cr_h = _cv_hist(ticker, period=cv_period, start=cv_start_str, end=cv_end_str, interval=cv_interval)
            if cr_h is not None:
                closes = cr_h["Close"].dropna()
                if len(closes) > 2:
                    base = float(closes.iloc[0])
                    if base > 0:
                        norm = closes / base * 100
                        fig_norm.add_trace(go.Scatter(x=norm.index, y=norm.values, name=name,
                                                       line=dict(color=color, width=2)))
        fig_norm.add_hline(y=100, line_dash="dash", line_color="rgba(148,163,184,.3)", line_width=1,
                           annotation_text="Base 100", annotation_font_size=10)
        theme(fig_norm, h=380, title=f"Crypto Normalised Performance — {cv_label}", fullscreen_bg=True)
        st.plotly_chart(fig_norm, use_container_width=True)

    else:
        st.info("Crypto data loading. Refresh to retry.")

    # ── Volatility Risk Premium ────────────────────────────────────────────
    sep("Volatility Risk Premium (VRP)")
    desc("<strong>VRP = VIX (implied vol) minus 30-day realised vol</strong>. "
         "When options are expensive (VRP > 5), systematic vol sellers earn positive carry. "
         "When options are cheap (VRP < 0), the market is underpricing risk — consider buying protection. "
         "This is a professional-grade signal used by volatility arbitrage funds globally.")

    if vol_rp:
        vrpa, vrpb = st.columns([1, 2], gap="large")
        with vrpa:
            vc = ("#f87171" if vol_rp["vrp"] > 5 else "#f59e0b" if vol_rp["vrp"] > 2
                  else "#4ade80" if vol_rp["vrp"] > -1 else "#a78bfa")
            vl = ("Options Expensive — Vol Sellers Rewarded" if vol_rp["vrp"] > 5
                  else "Slight Premium — Normal Carry" if vol_rp["vrp"] > 2
                  else "Fair Value" if vol_rp["vrp"] > -1
                  else "Options Cheap — Buy Protection")
            st.markdown(
                f'<div style="background:#0c1a2e;border:1px solid #162236;border-radius:8px;padding:16px;border-top:2px solid {vc}">'
                f'<div style="font-family:{MONO};font-size:.62rem;color:#6a90b0;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px">Volatility Risk Premium</div>'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:10px">'
                f'<div><div style="font-family:{MONO};font-size:.6rem;color:#6a90b0;margin-bottom:2px">Implied (VIX)</div>'
                f'<div style="font-family:{MONO};font-size:1.25rem;font-weight:700;color:#fb923c">{vol_rp["implied"]:.1f}</div></div>'
                f'<div style="font-family:{MONO};font-size:1.4rem;font-weight:700;color:#4a6a8a;align-self:center">-</div>'
                f'<div><div style="font-family:{MONO};font-size:.6rem;color:#6a90b0;margin-bottom:2px">Realised (30d)</div>'
                f'<div style="font-family:{MONO};font-size:1.25rem;font-weight:700;color:#22d3ee">{vol_rp["realised"]:.1f}</div></div>'
                f'<div style="font-family:{MONO};font-size:1.4rem;font-weight:700;color:#4a6a8a;align-self:center">=</div>'
                f'<div><div style="font-family:{MONO};font-size:.6rem;color:#6a90b0;margin-bottom:2px">VRP</div>'
                f'<div style="font-family:{MONO};font-size:1.25rem;font-weight:700;color:{vc}">{vol_rp["vrp"]:+.1f}</div></div>'
                f'</div>'
                f'<div style="font-size:.7rem;color:{vc};font-weight:600;margin-bottom:5px">{vl}</div>'
                f'<div style="font-family:{MONO};font-size:.6rem;color:#4a6a8a">VRP >5 = sell vol · VRP <0 = buy protection</div>'
                f'</div>', unsafe_allow_html=True)
        with vrpb:
            if vol_rp.get("vrp_hist") is not None and len(vol_rp["vrp_hist"]) > 5:
                fig_vrp = go.Figure()
                vh = vol_rp["vrp_hist"]
                colors_v = ["#f87171" if v > 5 else "#f59e0b" if v > 2 else "#4ade80" if v > 0 else "#a78bfa"
                            for v in vh.values]
                fig_vrp.add_trace(go.Bar(x=vh.index, y=vh.values, name="VRP",
                                         marker=dict(color=colors_v, line=dict(width=0)),
                                         hovertemplate="VRP: %{y:+.2f}<extra></extra>"))
                fig_vrp.add_hline(y=5, line_dash="dash", line_color="rgba(248,113,113,.5)",
                                   annotation_text="Expensive >5", annotation_font_size=10)
                fig_vrp.add_hline(y=0, line_color="rgba(148,163,184,.3)", line_width=1)
                fig_vrp.add_hline(y=-2, line_dash="dash", line_color="rgba(167,139,250,.5)",
                                   annotation_text="Cheap <-2", annotation_font_size=10)
                theme(fig_vrp, h=320, title="Volatility Risk Premium — 60 Day History", fullscreen_bg=True)
                st.plotly_chart(fig_vrp, use_container_width=True)

    footer()
