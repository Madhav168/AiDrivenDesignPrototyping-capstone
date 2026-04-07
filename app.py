import os
import json
import re
import base64
import requests
import streamlit as st
from dotenv import load_dotenv
import subprocess
import time

# ── Environment ─────────────────────────────────────────────────────────────
load_dotenv()
OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_KEY  = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen3-vl")

# Graphviz is no longer required as we use Mermaid.js for portability.

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ADDP — AI Driven Design Prototyping",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════════════════════
#  GLOBAL STYLES
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Design tokens ─────────────────────────────── */
:root {
    --bg:          #080810;
    --surf:        #0f0f1a;
    --card:        #13131f;
    --card-alt:    #181826;
    --border:      #222236;
    --border-h:    #383858;
    --gold:        #e8a838;
    --gold-h:      #f5c060;
    --gold-dim:    rgba(232,168,56,.09);
    --gold-glow:   rgba(232,168,56,.28);
    --gold-trace:  rgba(232,168,56,.04);
    --indigo:      #6366f1;
    --indigo-dim:  rgba(99,102,241,.09);
    --green:       #10b981;
    --red:         #f43f5e;
    --txt:         #ededf5;
    --txt-dim:     #9898b0;
    --muted:       #55556e;
    --sub:         #222235;
    --radius-sm:   10px;
    --radius-md:   14px;
    --radius-lg:   20px;
    --shadow-gold: 0 0 0 1px rgba(232,168,56,.12), 0 8px 40px rgba(232,168,56,.08);
}

/* ── Reset & base ──────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* Hide Streamlit's auto-generated header anchors */
a.header-anchor { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }

.stApp {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--txt) !important;
    overflow-x: hidden !important;
}

/* Subtle noise overlay via pseudo element */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
    opacity: 0.022;
    pointer-events: none;
    z-index: 0;
}

/* ── Hide Streamlit chrome ─────────────────────── */
header[data-testid="stHeader"],
footer, #MainMenu, .stDeployButton,
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ════════════════════════════════════════════════
   NAVBAR
════════════════════════════════════════════════ */
.nav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    height: 62px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 64px;
    background: rgba(8,8,16,.88);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border-bottom: 1px solid rgba(255,255,255,.04);
}
.nav::after {
    content:'';
    position:absolute; bottom:0; left:0; right:0;
    height:1px;
    background: linear-gradient(90deg,transparent,rgba(232,168,56,.3),transparent);
}
.nav-logo { display:flex; align-items:center; gap:12px; }
.nav-mark {
    width:36px; height:36px;
    background: linear-gradient(135deg,#e8a838 0%,#f97316 100%);
    border-radius:10px;
    display:grid; place-items:center;
    font-family:'Syne',sans-serif;
    font-size:.95rem; font-weight:800; color:#080810;
    letter-spacing:-.02em;
    box-shadow: 0 0 20px rgba(232,168,56,.22);
}
.nav-name {
    font-family:'Syne',sans-serif;
    font-size:1.05rem; font-weight:800;
    letter-spacing:-.5px; color:var(--txt);
    line-height:1.1;
}
.nav-tagline { font-size:.6rem; color:var(--muted); letter-spacing:.04em; }

.nav-links {
    position: absolute; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 36px;
}

.nav-link {
    font-size: .84rem; font-weight: 600; color: var(--muted);
    text-decoration: none !important; transition: all .3s cubic-bezier(.16,1,.3,1);
    cursor: pointer; letter-spacing: .02em;
    position: relative;
    padding: 4px 0;
}

.nav-link:hover { color: var(--txt); }
.nav-link.active { color: var(--gold); }

/* Premium Dot Indicator */
.nav-link::after {
    content: ''; position: absolute; bottom: -2px; left: 50%; transform: translateX(-50%);
    width: 0; height: 3px; border-radius: 10px;
    background: var(--gold); transition: width .3s ease;
    box-shadow: 0 0 8px var(--gold-glow);
}
.nav-link.active::after { width: 12px; }
.nav-link:hover::after { width: 6px; }

.nav-right {
    display: flex; align-items: center; gap: 24px;
}

.nav-btn {
    padding: 9px 24px; border-radius: 100px;
    background: linear-gradient(135deg, var(--gold) 0%, #f97316 100%);
    color: #080810 !important; font-size: .78rem; font-weight: 800;
    text-decoration: none !important; transition: all .25s ease;
    text-transform: uppercase; letter-spacing: .05em;
    box-shadow: 0 4px 16px rgba(232,168,56,.25);
    white-space: nowrap;
}

.nav-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(232,168,56,.4);
    filter: brightness(1.1);
}

.srv-pill {
    width:5px; height:5px; border-radius:50%; background:var(--gold);
    animation:pulse-glow 2.4s ease-in-out infinite;
}
.srv-pill {
    display:inline-flex; align-items:center; gap:8px;
    padding:6px 15px; border-radius:100px;
    font-size:.7rem; font-weight:600;
    white-space:nowrap; transition: all .2s ease;
    margin-right: 18px;
}
.srv-on  { background:rgba(16,185,129,.09); border:1px solid rgba(16,185,129,.28); color:var(--green); }
/* ── Sections ── */
.section-wrap {
    padding: 100px 0;
    max-width: 1200px;
    margin: 0 auto;
}

.sec-label {
    display: inline-block; padding: 6px 14px; border-radius: 4px;
    background: rgba(232,168,56,.08); color: var(--gold);
    font-size: .65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .12em; margin-bottom: 20px;
}

.hero-h1 {
    font-family: 'Syne', sans-serif; font-size: 6.8rem; font-weight: 800;
    line-height: 1.02; letter-spacing: -4px; margin-bottom: 24px;
    color: var(--txt);
}

/* About Grid */
.about-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 60px;
    align-items: start;
}

.about-text { color: var(--muted); line-height: 1.8; font-size: 1rem; }
.about-text b { color: var(--txt); }

.feature-cards {
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}

.f-card {
    background: var(--card); border: 1px solid var(--border);
    padding: 32px; border-radius: 12px; transition: all .3s ease;
}
.f-card:hover { border-color: var(--gold); transform: translateY(-4px); }
.f-card-icon { font-size: 1.5rem; margin-bottom: 16px; color: var(--gold); }
.f-card-h { font-weight: 700; margin-bottom: 12px; font-size: 1.1rem; }
.f-card-p { font-size: .85rem; color: var(--muted); }

/* Team Section */
.team-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 24px; margin-top: 40px;
}

.team-card {
    background: var(--card); border: 1px solid var(--border);
    padding: 40px 30px; border-radius: 16px; text-align: center;
    transition: all .3s ease; position: relative; overflow: hidden;
}

.team-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--gold); transform: scaleX(0); transition: transform .3s ease;
}

.team-card:hover { transform: translateY(-8px); border-color: var(--border-h); }
.team-card:hover::before { transform: scaleX(1); }

.team-avatar {
    width: 80px; height: 80px; border-radius: 50%; background: var(--border);
    margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; font-weight: 800; color: var(--gold);
    border: 2px solid var(--border);
}

.team-name { font-weight: 700; font-size: 1.1rem; margin-bottom: 6px; }
.team-id { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.team-role { font-size: .85rem; color: var(--gold); margin-top: 12px; font-weight: 600; opacity: .8; }

.guide-badge {
    display: inline-block; margin-top: 50px; padding: 20px 40px;
    background: rgba(99,102,241,.06); border: 1px solid rgba(99,102,241,.15);
    border-radius: 100px;
}

/* ════════════════════════════════════════════════
   HERO
════════════════════════════════════════════════ */
.hero-wrap {
    position:relative; overflow:hidden;
    padding: 130px 24px 80px;
    display:flex; flex-direction:column; align-items:center;
    text-align:center;
}

/* Animated orb blobs */
.orb-stage {
    position:absolute; inset:0; pointer-events:none; overflow:hidden;
}
.orb {
    position:absolute; border-radius:50%;
    filter: blur(120px); will-change: transform;
}
.orb-a {
    width:700px; height:700px;
    background:radial-gradient(circle at center, rgba(232,168,56,.18) 0%, transparent 70%);
    top:-250px; left:-180px;
    animation: orb-drift-a 14s ease-in-out infinite;
}
.orb-b {
    width:550px; height:550px;
    background:radial-gradient(circle at center, rgba(99,102,241,.14) 0%, transparent 70%);
    top:-100px; right:-150px;
    animation: orb-drift-b 18s ease-in-out infinite;
}
.orb-c {
    width:400px; height:400px;
    background:radial-gradient(circle at center, rgba(249,115,22,.1) 0%, transparent 70%);
    bottom:-100px; left:40%;
    animation: orb-drift-c 22s ease-in-out infinite;
}

/* Grid overlay */
.hero-grid {
    position:absolute; inset:0; pointer-events:none;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 72px 72px;
    mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black, transparent);
    -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black, transparent);
}

/* Hero content */
.hero-content {
    position:relative; z-index:2;
    max-width:900px; margin:0 auto;
    display:flex; flex-direction:column; align-items:center; gap:0;
    animation: hero-rise 1s cubic-bezier(.16,1,.3,1) both;
}
.hero-badge {
    display:inline-flex; align-items:center; gap:8px;
    padding:6px 18px; border-radius:100px; margin-bottom:32px;
    background:var(--gold-dim); border:1px solid rgba(232,168,56,.18);
    font-size:.68rem; font-weight:700; color:var(--gold);
    text-transform:uppercase; letter-spacing:.12em;
}
.hero-badge-dot {
    width:4px; height:4px; border-radius:50%; background:var(--gold);
    animation:pulse-glow 2s ease-in-out infinite;
}
.hero-h1 {
    font-family:'Syne',sans-serif;
    font-size: clamp(3rem, 6vw, 5.2rem);
    font-weight:800; line-height:1.03;
    letter-spacing:-2.5px;
    color:var(--txt);
    margin-bottom:24px;
}
.hero-grad {
    background: linear-gradient(115deg, #e8a838 0%, #f97316 40%, #a78bfa 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
}
.hero-underline { position:relative; display:inline-block; }
.hero-underline::after {
    content:''; position:absolute; bottom:-4px; left:0; right:0; height:2px;
    background: linear-gradient(90deg, var(--gold), transparent);
    border-radius:2px;
    animation: underline-draw 1.2s 0.8s cubic-bezier(.16,1,.3,1) both;
    transform-origin: left;
}
.hero-sub {
    font-size:1.05rem; line-height:1.82; color:var(--txt-dim);
    max-width:680px; margin-bottom:52px; font-weight:400;
}
.hero-stats {
    display:flex; align-items:center; gap:0; margin-top:8px;
}
.stat {
    padding:0 32px; text-align:center;
    border-right:1px solid var(--border);
}
.stat:first-child { padding-left:0; }
.stat:last-child  { padding-right:0; border-right:none; }
.stat-n {
    display: block; font-size: 1.35rem; font-weight: 700;
    color: var(--txt); margin-bottom: 2px;
}
.stat-l { font-size: .62rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-weight: 500; }

/* ════════════════════════════════════════════════
   DIVIDER
════════════════════════════════════════════════ */
.section-divider {
    width:100%; height:1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin:0;
}

/* ════════════════════════════════════════════════
   MODE TOGGLE (radio → pill switcher)
════════════════════════════════════════════════ */
.mode-wrap {
    display:flex; justify-content:center; padding:40px 0 12px;
}

div[data-testid="stRadio"] {
    display:flex !important; justify-content:center !important;
    width:100% !important; margin:0 auto !important;
}
div[data-testid="stRadio"] > label { display:none !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display:inline-flex !important; flex-direction:row !important;
    gap:4px !important;
    background:var(--surf) !important;
    border:1px solid var(--border) !important;
    border-radius:100px !important;
    padding:5px !important;
    justify-content:center !important; width:fit-content !important;
    margin:0 auto !important;
    box-shadow: 0 0 0 1px rgba(255,255,255,.03) inset;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    display:flex !important; align-items:center !important; justify-content:center !important;
    padding:10px 28px !important; border-radius:100px !important; cursor:pointer !important;
    transition: all .25s cubic-bezier(.16,1,.3,1) !important;
    font-family:'DM Sans',sans-serif !important;
    font-size:.875rem !important; font-weight:500 !important;
    color:var(--muted) !important; white-space:nowrap !important;
    margin:0 !important; text-align:center !important;
    letter-spacing:.01em !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input[type=radio]:checked) {
    background: linear-gradient(135deg, var(--gold) 0%, #f97316 100%) !important;
    color:#080810 !important; font-weight:700 !important;
    box-shadow: 0 4px 20px var(--gold-glow) !important;
}
div[data-testid="stRadio"] label > div:first-child { display:none !important; }
div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
    margin:0 !important; text-align:center !important; width:100% !important;
}

/* ════════════════════════════════════════════════
   CARDS / BORDERED CONTAINERS
════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
    transition: border-color .3s ease, box-shadow .3s ease, transform .3s ease !important;
    position:relative;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-h) !important;
    box-shadow: 0 0 0 1px rgba(232,168,56,.06), 0 20px 60px rgba(0,0,0,.4) !important;
}

/* ════════════════════════════════════════════════
   SCROLL REVEAL CLASSES (applied by JS)
════════════════════════════════════════════════ */
.reveal-init {
    opacity: 0 !important;
    transform: translateY(36px) !important;
}
.reveal-done {
    opacity: 1 !important;
    transform: translateY(0) !important;
    transition: opacity .75s cubic-bezier(.16,1,.3,1),
                transform .75s cubic-bezier(.16,1,.3,1) !important;
}
.reveal-init.reveal-done {
    opacity:1 !important; transform:translateY(0) !important;
}

/* ════════════════════════════════════════════════
   STREAMLIT FORM COMPONENTS
════════════════════════════════════════════════ */

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surf) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius-md) !important;
    transition: all .25s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(232,168,56,.35) !important;
    background: rgba(232,168,56,.015) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--gold) 0%, #f0952a 100%) !important;
    color: #080810 !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    height: 48px !important; width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .875rem !important; font-weight: 700 !important;
    letter-spacing: .02em !important;
    transition: all .22s cubic-bezier(.16,1,.3,1) !important;
    cursor: pointer !important;
    box-shadow: 0 4px 16px rgba(232,168,56,.2) !important;
    position: relative; overflow: hidden;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(232,168,56,.35) !important;
    background: linear-gradient(135deg, #f5ba52 0%, #f97316 100%) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: var(--surf) !important;
    color: var(--txt-dim) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    height: 40px !important;
    font-size: .78rem !important; font-weight: 500 !important;
    width: 100% !important;
    letter-spacing: .02em !important;
    box-shadow: none !important;
    transition: all .2s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--border-h) !important;
    background: var(--card-alt) !important;
    color: var(--txt) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Selectbox */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
    background: var(--surf) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--txt) !important;
    transition: border-color .2s ease !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"]:hover > div:first-child {
    border-color: var(--border-h) !important;
}

/* Textarea */
.stTextArea > div > div > textarea {
    background: var(--surf) !important;
    color: var(--txt) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .775rem !important;
    line-height: 1.7 !important;
    transition: border-color .2s ease, box-shadow .2s ease !important;
    resize: vertical !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: rgba(232,168,56,.4) !important;
    box-shadow: 0 0 0 3px rgba(232,168,56,.07) !important;
    outline: none !important;
}

/* ════════════════════════════════════════════════
   CODE BLOCK — Header-integrated Copy Button
════════════════════════════════════════════════ */
[data-testid="stCode"] {
    position: relative !important;
    padding-top: 0 !important;
}
[data-testid="stCode"] > div {
    background: #0d0d18 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    position: relative !important;
    overflow: visible !important; /* Critical: allow button to float out */
}

/* Force the real copy button into the Header section */
[data-testid="stCode"] button {
    opacity: 1 !important;
    visibility: visible !important;
    position: absolute !important;
    
    /* Position it next to the tag in the header */
    top: -51px !important;
    right: 74px !important; 
    
    z-index: 99 !important;
    width: auto !important; height: auto !important;
    padding: 3px 10px !important;
    background: rgba(232,168,56,.08) !important;
    border: 1px solid rgba(232,168,56,.25) !important;
    border-radius: 6px !important;
    color: var(--gold) !important;
    font-size: .62rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: .05em;
    transition: all .2s ease !important;
    box-shadow: none !important;
}

[data-testid="stCode"] button:hover {
    background: var(--gold) !important;
    color: #0b0b0f !important;
    transform: translateY(-1px) !important;
}

/* Adjust Expanders to account for the lifted button */
[data-testid="stExpander"] {
    margin-top: 14px !important;
    border: 1px solid var(--border) !important;
    background: transparent !important;
}

/* ════════════════════════════════════════════════
   EXPANDER (code "show more")
════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
    margin-top: 14px !important;
    transition: border-color .2s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color: var(--border-h) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
    background: var(--surf) !important;
    padding: 12px 16px !important;
    cursor: pointer !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .8rem !important;
    font-weight: 600 !important;
    color: var(--txt-dim) !important;
    transition: color .2s ease !important;
    list-style: none !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--txt) !important;
}
[data-testid="stExpander"] > details > summary > span {
    display: flex; align-items: center; gap: 8px;
}
details[data-testid="stExpander"] {
    border: none !important;
    background: transparent !important;
}

/* Alerts */
[data-testid="stAlertContainer"] { border-radius: var(--radius-sm) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* Spinner */
[data-testid="stSpinner"] { color: var(--gold) !important; }
[data-testid="stSpinner"] > div > div {
    border-top-color: var(--gold) !important;
}

/* ════════════════════════════════════════════════
   UTILITY CLASSES
════════════════════════════════════════════════ */
.lbl {
    font-size:.65rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.12em; color:var(--muted); margin-bottom:10px; display:block;
}
.tag {
    display:inline-flex; align-items:center; gap:4px;
    padding:3px 9px; border-radius:5px;
    font-size:.62rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
}
.tag-html { background:rgba(249,115,22,.1); color:#fb923c; }
.tag-py   { background:rgba(99,102,241,.1); color:#a5b4fc; }
.tag-img  { background:rgba(16,185,129,.1); color:#34d399; }

.sec-head {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:16px; padding-bottom:14px;
    border-bottom:1px solid var(--border);
}
.sec-title  { display:flex; align-items:center; gap:12px; }
.sec-icon   {
    width:38px; height:38px; border-radius:10px;
    display:grid; place-items:center; font-size:1rem; flex-shrink:0;
    font-family: 'Syne', sans-serif; font-weight:800; font-size:.85rem;
}
.icon-gold   { background:var(--gold-dim); color:var(--gold); border:1px solid rgba(232,168,56,.14); }
.icon-indigo { background:var(--indigo-dim); color:#818cf8; border:1px solid rgba(99,102,241,.14); }
.icon-green  { background:rgba(16,185,129,.08); color:var(--green); border:1px solid rgba(16,185,129,.14); }
.sec-name   { font-family:'Syne',sans-serif; font-size:.92rem; font-weight:700; color:var(--txt); }
.sec-desc   { font-size:.7rem; color:var(--muted); margin-top:2px; }

.dinfo {
    display:flex; align-items:flex-start; gap:12px;
    background:rgba(16,185,129,.05); border:1px solid rgba(16,185,129,.18);
    border-radius:var(--radius-sm); padding:13px 16px; margin-bottom:12px;
}
.dinfo-txt { font-size:.82rem; font-weight:600; color:var(--green); }
.dinfo-sub { font-size:.7rem; color:var(--muted); margin-top:2px; }

.browser-bar {
    background:var(--surf); border:1px solid var(--border);
    border-bottom:none; border-radius:14px 14px 0 0;
    padding:10px 16px; display:flex; align-items:center; gap:10px;
}
.bdots { display:flex; gap:5px; }
.bd { width:10px; height:10px; border-radius:50%; }
.bd-r { background:#f43f5e; }
.bd-y { background:#f59e0b; }
.bd-g { background:var(--green); }
.burl {
    flex:1; background:var(--card); border:1px solid var(--border);
    border-radius:5px; padding:3px 10px;
    font-family:'JetBrains Mono',monospace; font-size:.65rem; color:var(--muted);
}
.browser-frame {
    border:1px solid var(--border); border-top:none;
    border-radius:0 0 14px 14px; overflow:hidden;
}

.empty-state { text-align:center; padding:80px 24px; }
.empty-icon  {
    width:52px; height:52px; border-radius:14px;
    background:var(--sub); display:inline-flex; align-items:center; justify-content:center;
    margin-bottom:18px;
}
.empty-icon-inner { font-size:1.4rem; opacity:.3; }
.empty-title { font-size:.88rem; font-weight:600; color:var(--muted); }
.empty-sub   { font-size:.73rem; color:var(--muted); opacity:.55; margin-top:6px; }

.section-pad { padding: 32px 0; }

/* ════════════════════════════════════════════════
   KEYFRAMES
════════════════════════════════════════════════ */
@keyframes pulse-glow  { 0%,100%{opacity:1;} 50%{opacity:.25;} }
@keyframes orb-drift-a { 0%,100%{transform:translate(0,0) scale(1);} 33%{transform:translate(60px,-40px) scale(1.06);} 66%{transform:translate(-30px,50px) scale(.96);} }
@keyframes orb-drift-b { 0%,100%{transform:translate(0,0) scale(1);} 40%{transform:translate(-50px,30px) scale(1.04);} 75%{transform:translate(40px,-50px) scale(.98);} }
@keyframes orb-drift-c { 0%,100%{transform:translate(0,0) scale(1);} 50%{transform:translate(30px,-30px) scale(1.08);} }
@keyframes hero-rise   { from{opacity:0;transform:translateY(28px);} to{opacity:1;transform:translateY(0);} }
@keyframes underline-draw { from{transform:scaleX(0);} to{transform:scaleX(1);} }
@keyframes float-in    { from{opacity:0;transform:translateY(44px);} to{opacity:1;transform:translateY(0);} }
@keyframes spin-slow   { to{transform:rotate(360deg);} }

/* Scrollbar */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--sub); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:var(--border-h); }
</style>
""", unsafe_allow_html=True)

# ── Scroll-reveal + misc JS ──────────────────────────────────────────────────
st.markdown("""
<script>
(function() {
  if (window.__ADDP_SCROLL_INIT__) return;
  window.__ADDP_SCROLL_INIT__ = true;

  function applyReveal() {
    const cards = document.querySelectorAll(
      '[data-testid="stVerticalBlockBorderWrapper"]:not([data-reveal])'
    );
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(function(e) {
        if (e.isIntersecting) {
          e.target.classList.remove('reveal-init');
          e.target.classList.add('reveal-done');
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });

    cards.forEach(function(el, i) {
      el.dataset.reveal = '1';
      el.classList.add('reveal-init');
      // stagger by index
      el.style.transitionDelay = (i * 0.07) + 's';
      obs.observe(el);
    });
  }

  // Run on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyReveal);
  } else {
    applyReveal();
  }

  // Re-run on Streamlit re-render (MutationObserver)
  var mo = new MutationObserver(function() { applyReveal(); });
  mo.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  API GUARD
# ════════════════════════════════════════════════════════════════════════════
if not OLLAMA_API_KEY:
    st.markdown('<div style="height:70px"></div>', unsafe_allow_html=True)
    st.error("OLLAMA_API_KEY is missing. Add it to your .env file and restart the server.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ════════════════════════════════════════════════════════════════════════════
_DEFAULTS = {
    "backend_proc": None,
    "gen_f":        "",
    "gen_b":        "",
    "diagram_img":  None,
    "diagram_type": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════════
def call_ollama_cloud(prompt: str, images=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "HTTP-Referer": "https://aidrivendesignprototyping.streamlit.app/",
        "X-Title": "ADDP - AI Driven Design Prototyping"
    }
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": { "temperature": 0.7, "top_p": 0.9 }
    }
    if images:
        payload["images"] = images
    try:
        base_url  = OLLAMA_URL.rstrip("/")
        endpoint  = f"{base_url}/api/generate"
        session   = requests.Session()
        response  = session.post(endpoint, headers=headers, json=payload, timeout=300, verify=False)
        if response.status_code == 401 or "unauthorized" in response.text.lower():
            st.error("Ollama Cloud: Unauthorized. Check your API Key.")
            return ""
        response.raise_for_status()
        raw = response.json().get("response", "")
        raw = re.sub(r"<thought>[\s\S]*?<\/thought>",   "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"<reasoning>[\s\S]*?<\/reasoning>","", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```[a-zA-Z]*\n?", "", raw).replace("```", "").strip()
        return raw
    except Exception as e:
        st.error(f"Ollama Cloud Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            st.write(f"Server Response: {e.response.text}")
        return ""

def _strip_fences(t: str) -> str:
    t = re.sub(r"```[a-zA-Z]*\n?", "", t)
    return t.replace("```", "").strip()

def stop_backend():
    proc = st.session_state.backend_proc
    if proc:
        try:
            if os.name == "nt":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                proc.terminate()
        except Exception:
            pass
        st.session_state.backend_proc = None

def start_backend(code: str):
    stop_backend()
    with open("generated_backend.py", "w", encoding="utf-8") as fh:
        fh.write(code)
    proc = subprocess.Popen(
        ["python", "generated_backend.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, shell=(os.name == "nt"),
    )
    st.session_state.backend_proc = proc
    time.sleep(1.5)

# ════════════════════════════════════════════════════════════════════════════
#  SERVER STATUS & ROUTING
# ════════════════════════════════════════════════════════════════════════════
_proc = st.session_state.backend_proc
if _proc is not None and _proc.poll() is not None:
    st.session_state.backend_proc = None
    _proc = None
_server_on = _proc is not None

# Simple route via session state
if "page" not in st.session_state:
    st.session_state.page = "home"

mode = None # Default to prevent NameErrors on Home

# Navbar action capture
_params = st.query_params
if "p" in _params:
    st.session_state.page = _params["p"]

_curr_page = st.session_state.page

# ════════════════════════════════════════════════════════════════════════════
#  NAVBAR
# ════════════════════════════════════════════════════════════════════════════
_pill_cls = "srv-on"     if _server_on else "srv-off"
_dot_cls  = "srv-dot-on" if _server_on else "srv-dot-off"
_srv_txt  = (f"localhost:5000 &nbsp;&middot;&nbsp; PID {_proc.pid}" if _server_on
             else "No active server")

_h_active = "active" if _curr_page == "home" else ""
_a_active = "active" if _curr_page == "about" else ""
_t_active = "active" if _curr_page == "team" else ""

st.markdown(f"""
<nav class="nav">
  <div class="nav-logo">
    <div class="nav-mark">A</div>
    <div>
      <div class="nav-name">ADDP</div>
      <div class="nav-tagline">AI Driven Design Prototyping</div>
    </div>
  </div>
  
  <div class="nav-links">
    <a href="/?p=home" target="_self" class="nav-link {_h_active}">Home</a>
    <a href="/?p=home#about" target="_self" class="nav-link">About</a>
    <a href="/?p=home#team" target="_self" class="nav-link">Team</a>
  </div>

  <div class="nav-right">
    <a href="/?p=tools" target="_self" class="nav-btn">Launch Prototype</a>
    <div class="srv-pill {_pill_cls}">
      <div class="srv-dot {_dot_cls}"></div>
      {_srv_txt}
    </div>
  </div>
</nav>
<div style="height:62px"></div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTING CONTENT
# ════════════════════════════════════════════════════════════════════════════

if _curr_page == "home":
    # ── HERO ─────────────────────────────────────────────────────────────
    st.markdown("""
<div class="hero-wrap">
  <!-- animated background -->
  <div class="orb-stage">
    <div class="orb orb-a"></div>
    <div class="orb orb-b"></div>
    <div class="orb orb-c"></div>
  </div>
  <div class="hero-grid"></div>
  <!-- content -->
  <div class="hero-content">
    <div class="hero-badge">
      <div class="hero-badge-dot"></div>
      Capstone Project &nbsp;&middot;&nbsp; Live Prototype
    </div>
    <h1 class="hero-h1">
      <span class="hero-grad">Blueprint</span> to<br>
      <span class="hero-underline">Production</span>&nbsp;in&nbsp;Seconds
    </h1>
    <p class="hero-sub">
      ADDP bridges the gap between architectural vision and running software.
      Upload any UML diagram and receive a complete full-stack application &mdash;
      or reverse-engineer your codebase into clean visual architecture.
    </p>
    <div class="hero-stats">
      <div class="stat">
        <span class="stat-n">AI-Driven</span>
        <span class="stat-l">Multi-modal Analysis</span>
      </div>
      <div class="stat">
        <span class="stat-n">Bi-directional</span>
        <span class="stat-l">UML ↔ Code Logic</span>
      </div>
      <div class="stat">
        <span class="stat-n">Full-Stack</span>
        <span class="stat-l">Automated App Engine</span>
      </div>
</div>
<div class="section-divider"></div>

<!-- ── ABOUT SECTION ── -->
<div class="section-wrap" id="about">
  <div class="sec-label">Our Story</div>
  <div class="about-grid">
    <div>
      <h2 class="sec-h">Bridging the Gap<br>from Vision to Code</h2>
      <div class="about-text">
        Modern software development relies heavily on UML for design, but the transition to code is often manual and slow. 
        <b>ADDP (AI-Driven Design Prototyping)</b> was born out of the need to automate this bidirectional transformation.
        <br><br>
        Using cutting-edge multimodal AI, we enable engineers to generate functional full-stack applications from simple diagrams 
        and reverse-engineer complex codebases back into structured visual models instantly.
      </div>
    </div>
    <div class="feature-cards">
      <div class="f-card">
        <div class="f-card-icon">◈</div>
        <div class="f-card-h">Bi-directional</div>
        <div class="f-card-p">Seamlessly flow between UML design and functional codebases.</div>
      </div>
      <div class="f-card">
        <div class="f-card-icon">✦</div>
        <div class="f-card-h">Full-Stack Gen</div>
        <div class="f-card-p">Generate HTML, Tailwind CSS, and Flask backends automatically.</div>
      </div>
      <div class="f-card">
        <div class="f-card-icon">⌘</div>
        <div class="f-card-h">Code Analysis</div>
        <div class="f-card-p">Extract Class, Sequence, and Use Case diagrams from source.</div>
      </div>
      <div class="f-card">
        <div class="f-card-icon">◎</div>
        <div class="f-card-h">Lite Storage</div>
        <div class="f-card-p">Built-in Excel-based data handling for rapid prototyping.</div>
      </div>
    </div>
  </div>
</div>

<div class="section-divider"></div>

<!-- ── TEAM SECTION ── -->
<div class="section-wrap" id="team" style="text-align:center;">
  <div class="sec-label">The Team</div>
  <h2 class="sec-h">Building the Future of Prototyping</h2>
  
  <div class="team-grid">
    <div class="team-card">
      <div class="team-avatar">VK</div>
      <div class="team-name">CH Venkata Krishna Raju</div>
      <div class="team-id">VU22CSEN0100729</div>
      <div class="team-role">Team Lead</div>
    </div>
    <div class="team-card">
      <div class="team-avatar">SM</div>
      <div class="team-name">P Sai Madhav</div>
      <div class="team-id">VU22CSEN0100031</div>
      <div class="team-role">Team Member</div>
    </div>
    <div class="team-card">
      <div class="team-avatar">AC</div>
      <div class="team-name">Aashritha CH</div>
      <div class="team-id">VU22CSEN0100197</div>
      <div class="team-role">Team Member</div>
    </div>
    <div class="team-card">
      <div class="team-avatar">PS</div>
      <div class="team-name">P Sai</div>
      <div class="team-id">VU22CSEN0100559</div>
      <div class="team-role">Team Member</div>
    </div>
  </div>

  <div class="guide-badge">
    <div style="font-size: .7rem; color: #6366f1; text-transform: uppercase; font-weight: 800; letter-spacing: .1em; margin-bottom: 12px;">Under the guidance of</div>
    <div style="font-weight: 800; font-size: 1.4rem;">Dr. Srinivas Prasad</div>
    <div style="font-size: .85rem; color: var(--muted); margin-top: 4px;">Assistant Professor &middot; Department of CSE &middot; GITAM University</div>
  </div>
</div>

<div class="section-divider"></div>
""", unsafe_allow_html=True)
    st.stop()

# ── TOOLS HEADER ───
st.markdown('<div style="height:48px"></div>', unsafe_allow_html=True)
st.markdown('<div class="fade-up">', unsafe_allow_html=True)
st.markdown('<h2 style="text-align:center; font-family:Syne; font-size:2.4rem; font-weight:800; letter-spacing:-1px; margin-bottom:8px;">AI Design Engine</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:var(--muted); font-size:0.9rem; margin-bottom:40px;">Select your processing mode below to start synthesizing architecture</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
    
# ── MODE TOGGLE ───
st.markdown('<div class="mode-wrap">', unsafe_allow_html=True)
_, _tc, _ = st.columns([1, 2, 1])
with _tc:
    mode = st.radio(
        "mode_sel",
        ["Diagram → Full Stack", "Code → Architecture"],
        label_visibility="collapsed",
        horizontal=True,
    )
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
# ════════════════════════════════════════════════════════════════════════════
#  CONTENT WRAPPER
# ════════════════════════════════════════════════════════════════════════════
_, _mc, _ = st.columns([1, 16, 1])

with _mc:

    # ═══════════════════════════════════════
    #  A: DIAGRAM → FULL STACK
    # ═══════════════════════════════════════
    if mode == "Diagram → Full Stack":

        # ── Upload section ─────────────────
        with st.container(border=True):
            st.markdown("""
            <div style="padding:4px 0 0">
            <div class="sec-head">
              <div class="sec-title">
                <div class="sec-icon icon-gold">BP</div>
                <div>
                  <div class="sec-name">Blueprint Input</div>
                  <div class="sec-desc">Upload a UML, flow, sequence, ER, or architecture diagram — PNG or JPG</div>
                </div>
              </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            upload = st.file_uploader(
                "upload_diagram",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed",
            )

            if upload:
                st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
                _, _ic, _ = st.columns([1, 4, 1])
                with _ic:
                    st.image(upload, caption="Uploaded Blueprint", use_container_width=True)

                img_bytes = upload.getvalue()
                mime_type = upload.type or "image/png"
                st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

                if st.button("Generate Full-Stack Application", key="gen_btn"):
                    with st.spinner("Analysing blueprint via Ollama Cloud — generating your application..."):
                        try:
                            _prompt = """You are a senior full-stack software architect.
Carefully analyse the uploaded diagram and generate a COMPLETE, production-grade application.

Requirements:
1. FRONTEND — A complete, modern HTML page using Tailwind CSS (loaded via CDN).
   Dark theme, premium UI, fully functional, reflecting every element shown in the diagram.
2. BACKEND  — A complete Flask REST API (flask + flask-cors) on port 5000.
   Implement every route implied by the diagram with proper JSON responses.
3. DATA     — Use pandas + openpyxl for data persistence via a file called data.xlsx.

Output EXACTLY this format with no additional text or commentary:
===frontend===
[Complete HTML source code here]
===backend===
[Complete Python Flask source code here]"""

                            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                            _raw    = call_ollama_cloud(_prompt, images=[img_b64])

                            _f, _b = "", ""
                            if "===frontend===" in _raw:
                                if "===backend===" in _raw:
                                    _parts = _raw.split("===frontend===")[1].split("===backend===")
                                    _f = _strip_fences(_parts[0])
                                    _b = _strip_fences(_parts[1])
                                else:
                                    _f = _strip_fences(_raw.split("===frontend===")[1])

                            if _f or _b:
                                st.session_state.gen_f = _f
                                st.session_state.gen_b = _b
                                st.rerun()
                            else:
                                st.error("Failed to parse the generation. The model response was unexpected.")
                                with st.expander("Show raw response"):
                                    st.write(_raw)

                        except Exception as _e:
                            st.error(f"Generation failed: {_e}")

        # ── Generated output ────────────────
        if st.session_state.gen_f or st.session_state.gen_b:
            st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

            col_f, col_b = st.columns(2, gap="large")

            # — Frontend column —
            with col_f:
                with st.container(border=True):
                    st.markdown("""
                    <div style="padding:4px 0 0">
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-gold">FE</div>
                        <div>
                          <div class="sec-name">Frontend Layer</div>
                          <div class="sec-desc">HTML &middot; Tailwind CSS</div>
                        </div>
                      </div>
                      <span class="tag tag-html">HTML</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.session_state.gen_f:
                        with st.expander("View Frontend Code", expanded=False):
                            st.code(st.session_state.gen_f, language="html")
                        st.download_button(
                            "Download index.html",
                            st.session_state.gen_f,
                            file_name="index.html",
                            mime="text/html",
                            key="dl_f",
                        )
                    else:
                        st.caption("Frontend was not generated in this response.")

            # — Backend column —
            with col_b:
                with st.container(border=True):
                    st.markdown("""
                    <div style="padding:4px 0 0">
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-indigo">BE</div>
                        <div>
                          <div class="sec-name">Backend Layer</div>
                          <div class="sec-desc">Flask &middot; REST API &middot; Port 5000</div>
                        </div>
                      </div>
                      <span class="tag tag-py">Python</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.session_state.gen_b:
                        with st.expander("View Backend Code", expanded=False):
                            st.code(st.session_state.gen_b, language="python")
                        st.download_button(
                            "Download backend.py",
                            st.session_state.gen_b,
                            file_name="backend.py",
                            mime="text/plain",
                            key="dl_b",
                        )
                        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

                        # ── Deploy controls ─────────────────
                        if _server_on:
                            _pid = _proc.pid if _proc else "—"
                            st.markdown(f"""
                            <div class="dinfo">
                              <div>
                                <div class="dinfo-txt">Server running on localhost:5000</div>
                                <div class="dinfo-sub">PID {_pid} &middot; Flask &middot; Active this session</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("Stop Server", key="stop_btn"):
                                stop_backend()
                                st.rerun()
                        else:
                            if st.button("Deploy to Localhost (port 5000)", key="deploy_btn"):
                                with st.spinner("Launching Flask server..."):
                                    start_backend(st.session_state.gen_b)
                                st.success("Server deployed on port 5000.")
                                st.rerun()
                    else:
                        st.caption("Backend was not generated in this response.")

            # ── Live preview ──────────────────
            if st.session_state.gen_f:
                st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)

                st.markdown("""
                <div class="browser-bar">
                  <div class="bdots">
                    <div class="bd bd-r"></div>
                    <div class="bd bd-y"></div>
                    <div class="bd bd-g"></div>
                  </div>
                  <div class="burl">localhost &nbsp;&middot;&nbsp; Live Preview</div>
                </div>
                <div class="browser-frame">
                """, unsafe_allow_html=True)

                _prev = st.session_state.gen_f
                if "tailwindcss" not in _prev:
                    _prev = '<script src="https://cdn.tailwindcss.com"></script>\n' + _prev
                st.components.v1.html(_prev, height=580, scrolling=True)

                st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  B: CODE → ARCHITECTURE
    # ═══════════════════════════════════════
    else:
        col_in, col_out = st.columns([1, 1], gap="large")

        # — Input column —
        with col_in:
            with st.container(border=True):
                st.markdown("""
                <div style="padding:4px 0 0">
                <div class="sec-head" style="margin-bottom:18px">
                  <div class="sec-title">
                    <div class="sec-icon icon-indigo">AE</div>
                    <div>
                      <div class="sec-name">Architecture Extraction</div>
                      <div class="sec-desc">Reverse-engineer code into UML diagrams</div>
                    </div>
                  </div>
                </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<span class="lbl">Diagram Type</span>', unsafe_allow_html=True)
                uml_choice = st.selectbox(
                    "diag_type",
                    ["Class Diagram", "Sequence Diagram", "Use Case Diagram",
                     "Activity Diagram", "Component Diagram"],
                    label_visibility="collapsed",
                    key="uml_choice",
                )

                st.markdown('<div style="height:14px"></div>'
                            '<span class="lbl">Source Code</span>', unsafe_allow_html=True)
                code_in = st.text_area(
                    "code_area",
                    height=308,
                    placeholder=(
                        "// Paste your source code here...\n\n"
                        "class UserService {\n"
                        "  constructor(private db: Database) {}\n"
                        "  async getUser(id: string) { ... }\n"
                        "}"
                    ),
                    label_visibility="collapsed",
                    key="code_input",
                )

                st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

                if st.button("Extract Architecture Diagram", key="extract_btn"):
                    if not code_in.strip():
                        st.error("Please paste some source code before extracting.")
                    else:
                        with st.spinner(f"Analysing code via Ollama Cloud and building {uml_choice}..."):
                            try:
                                _prompt = f"""Analyse the source code and produce a JSON representation for a {uml_choice}.

Output ONLY valid JSON — no markdown fences, no preamble, no commentary whatsoever.

Required JSON format per diagram type:
- Class Diagram:     [{{"name":"ClassName","attributes":["attr:Type"],"methods":["method()"],"relations":[{{"target":"OtherClass","type":"extends"}}]}}]
- Sequence Diagram:  {{"participants":["A","B"],"messages":[{{"from":"A","to":"B","message":"call()"}}]}}
- Use Case Diagram:  {{"actors":["User"],"use_cases":["Login"],"relations":[{{"actor":"User","use_case":"Login"}}]}}
- Activity Diagram:  {{"steps":["Start","Validate Input","Process","End"]}}
- Component Diagram: {{"components":[{{"name":"Frontend"}},{{"name":"Backend"}}],"connections":[{{"source":"Frontend","target":"Backend"}}]}}

Source Code:
{code_in}"""

                                _raw  = call_ollama_cloud(_prompt)
                                _raw  = _strip_fences(_raw.strip())
                                _s    = min(
                                    _raw.find("{") if "{" in _raw else len(_raw),
                                    _raw.find("[") if "[" in _raw else len(_raw),
                                )
                                _e    = max(
                                    _raw.rfind("}") if "}" in _raw else -1,
                                    _raw.rfind("]") if "]" in _raw else -1,
                                )
                                _data = json.loads(_raw[_s: _e + 1])

                                # ── Build Mermaid diagram ───────────
                                _mermaid = ""
                                if uml_choice == "Class Diagram" and isinstance(_data, list):
                                    _mermaid = "classDiagram\n"
                                    for _cls in _data:
                                        _n = _cls.get("name", "Unknown").replace(" ", "_")
                                        _mermaid += f"    class {_n} {{\n"
                                        for _at in (_cls.get("attributes", []) or []):
                                            _mermaid += f"        {_at}\n"
                                        for _mt in (_cls.get("methods", []) or []):
                                            _mermaid += f"        {_mt}\n"
                                        _mermaid += "    }\n"
                                        for _r in (_cls.get("relations") or []):
                                            _target = (_r.get("target") or _r.get("to", "")).replace(" ", "_")
                                            if _target:
                                                _mermaid += f"    {_n} --> {_target} : {_r.get('type', '')}\n"

                                elif uml_choice == "Sequence Diagram":
                                    _mermaid = "sequenceDiagram\n"
                                    for _p in _data.get("participants", []):
                                        _mermaid += f"    participant {_p}\n"
                                    for _m in _data.get("messages", []):
                                        _f = _m.get("from", "")
                                        _t = _m.get("to", "")
                                        _msg = _m.get("message", "call()")
                                        if _f and _t:
                                            _mermaid += f"    {_f}->>{_t}: {_msg}\n"

                                elif uml_choice == "Use Case Diagram":
                                    _mermaid = "graph LR\n"
                                    for _ac in _data.get("actors", []):
                                        _mermaid += f"    {_ac}((Actor: {_ac}))\n"
                                    for _uc in _data.get("use_cases", []):
                                        _mermaid += f"    {_uc}({_uc})\n"
                                    for _r2 in _data.get("relations", []):
                                        _a2 = _r2.get("actor", "")
                                        _u2 = _r2.get("use_case", "")
                                        if _a2 and _u2:
                                            _mermaid += f"    {_a2} --- {_u2}\n"

                                elif uml_choice == "Activity Diagram":
                                    _mermaid = "graph TD\n"
                                    _steps = _data.get("steps", [])
                                    for _i, _sn in enumerate(_steps):
                                        _mermaid += f"    Step{_i}({_sn})\n"
                                        if _i > 0:
                                            _mermaid += f"    Step{_i-1} --> Step{_i}\n"

                                elif uml_choice == "Component Diagram":
                                    _mermaid = "graph TD\n"
                                    for _comp in _data.get("components", []):
                                        _cn = (_comp if isinstance(_comp, str) else _comp.get("name", "?")).replace(" ", "_")
                                        _mermaid += f"    {_cn}[[{_cn}]]\n"
                                    for _conn in _data.get("connections", []):
                                        _cs = _conn.get("source", "").replace(" ", "_")
                                        _ct = _conn.get("target", "").replace(" ", "_")
                                        if _cs and _ct:
                                            _mermaid += f"    {_cs} --> {_ct}\n"

                                if _mermaid:
                                    # ── Convert Mermaid to Image via Mermaid.ink server-side ──
                                    try:
                                        _b64      = base64.b64encode(_mermaid.encode("ascii")).decode("ascii")
                                        _img_url  = f"https://mermaid.ink/img/{_b64}"
                                        
                                        # Server-side fetch to avoid browser issues
                                        _res = requests.get(_img_url, timeout=10)
                                        if _res.status_code == 200:
                                            st.session_state.diagram_img  = _res.content
                                            st.session_state.diagram_raw  = _mermaid
                                            st.session_state.diagram_type = uml_choice
                                            st.rerun()
                                        else:
                                            st.error(f"Image generation service failed (HTTP {_res.status_code})")
                                    except Exception as _fe:
                                        st.error(f"Failed to fetch diagram: {_fe}")
                                else:
                                    st.error("Could not generate diagram syntax.")

                            except json.JSONDecodeError as _je:
                                st.error(
                                    f"JSON parse error — try a different diagram type or "
                                    f"simplify the code.\n\nDetails: {_je}"
                                )
                            except Exception as _ex:
                                st.error(f"Extraction failed: {_ex}")

        # — Output column —
        with col_out:
            if st.session_state.diagram_img:
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="padding:4px 0 0">
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-gold">UML</div>
                        <div>
                          <div class="sec-name">{st.session_state.diagram_type}</div>
                          <div class="sec-desc">Auto-generated from source analysis</div>
                        </div>
                      </div>
                      <span class="tag tag-img">PNG</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.image(st.session_state.diagram_img, use_container_width=True)
                    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
                    st.download_button(
                        "Download High-Res PNG",
                        st.session_state.diagram_img,
                        file_name=f"architecture_{st.session_state.diagram_type.lower().replace(' ', '_')}.png",
                        mime="image/png",
                        key="dl_diag_png",
                        use_container_width=True,
                    )
                    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
                    st.text_area("Mermaid Syntax (Copy-paste to Mermaid.live)", st.session_state.diagram_raw, height=100)
            else:
                with st.container(border=True):
                    st.markdown("""
                    <div class="empty-state">
                      <div class="empty-icon">
                        <div class="empty-icon-inner">◈</div>
                      </div>
                      <div class="empty-title">Your diagram will appear here</div>
                      <div class="empty-sub">Paste source code on the left, then click Extract</div>
                    </div>
                    """, unsafe_allow_html=True)

# ── Bottom padding ─────────────────────────────────────────────────────────
st.markdown('<div style="height:100px"></div>', unsafe_allow_html=True)