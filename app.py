import os
import json
import re
import base64
import requests
import streamlit as st
from graphviz import Digraph
from dotenv import load_dotenv
import subprocess
import time

# ── Environment ─────────────────────
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl")

# ── Graphviz path fix (Windows) ───────────────────────────────────────────────
if os.name == "nt":
    _gv = r"C:\Program Files\Graphviz\bin"
    if os.path.exists(_gv):
        os.environ["PATH"] += os.pathsep + _gv

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ADDP — AI Driven Design Prototyping",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Tokens ──────────────────────────────────── */
:root {
    --bg:          #0b0b0f;
    --surf:        #131319;
    --card:        #1a1a22;
    --card-alt:    #1f1f2a;
    --border:      #29293a;
    --border-h:    #3e3e52;
    --gold:        #e8a838;
    --gold-h:      #f5ba52;
    --gold-dim:    rgba(232,168,56,.11);
    --gold-glow:   rgba(232,168,56,.3);
    --indigo:      #6366f1;
    --indigo-dim:  rgba(99,102,241,.11);
    --green:       #10b981;
    --red:         #f43f5e;
    --txt:         #eeeef3;
    --muted:       #68687e;
    --sub:         #31313f;
}

/* ── Reset & base ────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background-color: var(--bg) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,168,56,.06) 0%, transparent 70%),
        linear-gradient(rgba(255,255,255,.013) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.013) 1px, transparent 1px);
    background-size: 100% 100%, 64px 64px, 64px 64px;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--txt) !important;
}

/* ── Hide Streamlit chrome ───────────────────── */
header[data-testid="stHeader"],
footer, #MainMenu, .stDeployButton,
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ════════════════════════════════════════════════
   NAVBAR
════════════════════════════════════════════════ */
.nav {
    position: fixed; top:0; left:0; right:0; z-index:9999;
    height: 60px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 36px;
    background: rgba(11,11,15,.92);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
}
.nav-logo { display: flex; align-items: center; gap: 11px; }
.nav-mark {
    width: 34px; height: 34px;
    background: linear-gradient(140deg, var(--gold) 0%, #f97316 100%);
    border-radius: 9px;
    display: grid; place-items: center;
    font-family: 'Syne', sans-serif;
    font-size: .9rem; font-weight: 800; color: #0b0b0f;
    flex-shrink: 0;
    box-shadow: 0 0 16px rgba(232,168,56,.25);
}
.nav-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 800; letter-spacing: -.4px;
    color: var(--txt); line-height: 1.15;
}
.nav-sub { font-size: .62rem; color: var(--muted); font-weight: 400; }
.nav-badge {
    position: absolute; left:50%; transform: translateX(-50%);
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 16px; border-radius: 100px;
    background: var(--surf); border: 1px solid var(--border);
    font-size: .67rem; color: var(--muted);
    text-transform: uppercase; letter-spacing: .08em;
    white-space: nowrap;
}
.nav-spark {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--gold); animation: blink 2.2s ease-in-out infinite;
}
.srv-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 15px; border-radius: 100px;
    font-size: .7rem; font-weight: 600;
    font-family: 'DM Sans', sans-serif;
}
.srv-on  { background: rgba(16,185,129,.09); border:1px solid rgba(16,185,129,.28); color: var(--green); }
.srv-off { background: rgba(104,104,126,.07); border:1px solid var(--border); color: var(--muted); }
.srv-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink:0; }
.srv-dot-on  { background: var(--green); animation: blink 1.6s ease-in-out infinite; }
.srv-dot-off { background: var(--sub); }

/* ════════════════════════════════════════════════
   HERO
════════════════════════════════════════════════ */
.hero {
    text-align: center !important;
    padding: 100px 24px 52px;
    max-width: 1000px; margin: 0 auto;
    position: relative;
    display: flex; flex-direction: column; align-items: center;
}
.hero-eye {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 16px; border-radius: 100px;
    background: var(--gold-dim); border: 1px solid rgba(232,168,56,.2);
    font-size: .7rem; font-weight: 700; color: var(--gold);
    text-transform: uppercase; letter-spacing: .11em;
    margin-bottom: 28px;
}
.hero-h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.8rem, 5.5vw, 4.6rem);
    font-weight: 800; line-height: 1.06;
    letter-spacing: -2px; color: var(--txt);
    margin-bottom: 20px;
}
.grad {
    background: linear-gradient(110deg, var(--gold) 0%, #f97316 42%, var(--indigo) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-p, .hero-p * {
    font-size: 1.05rem !important; line-height: 1.78 !important;
    color: var(--muted) !important; max-width: 800px !important; margin: 0 auto 48px !important;
    font-weight: 400 !important; text-align: center !important; width: 100% !important;
    display: block !important;
}

/* ════════════════════════════════════════════════
   MODE TOGGLE (radio → pill switcher)
════════════════════════════════════════════════ */
div[data-testid="stRadio"] {
    display: flex !important; justify-content: center !important;
    width: 100% !important; margin: 0 auto !important;
}
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: inline-flex !important; flex-direction: row !important; gap: 8px !important;
    background: var(--surf) !important; border: 1px solid var(--border) !important;
    border-radius: 100px !important; padding: 6px !important;
    justify-content: center !important; width: fit-content !important;
    margin: 0 auto !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    display: flex !important; align-items: center !important; justify-content: center !important; gap: 0 !important;
    padding: 11px 32px !important; border-radius: 100px !important; cursor: pointer !important;
    transition: all .22s ease !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .875rem !important; font-weight: 500 !important;
    color: var(--muted) !important; white-space: nowrap !important; margin: 0 !important;
    text-align: center !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input[type=radio]:checked) {
    background: var(--gold) !important; color: #0b0b0f !important; font-weight: 700 !important;
    box-shadow: 0 2px 16px var(--gold-glow) !important;
}
div[data-testid="stRadio"] label > div:first-child { display: none !important; }
div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { 
    margin: 0 !important; text-align: center !important; width: 100% !important;
}

/* ════════════════════════════════════════════════
   BORDERED CONTAINERS → CARDS
════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card) !important; border-color: var(--border) !important;
    border-radius: 18px !important; overflow: hidden !important;
    transition: border-color .2s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: var(--border-h) !important; }

/* ════════════════════════════════════════════════
   STREAMLIT COMPONENTS
════════════════════════════════════════════════ */

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surf) !important; border: 2px dashed var(--border) !important;
    border-radius: 14px !important; transition: all .2s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(232,168,56,.38) !important;
    background: rgba(232,168,56,.018) !important;
}

/* Primary button (all .stButton) */
.stButton > button {
    background: var(--gold) !important; color: #0b0b0f !important;
    border: none !important; border-radius: 12px !important;
    height: 48px !important; width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .88rem !important; font-weight: 700 !important; letter-spacing: .02em !important;
    transition: all .18s ease !important; cursor: pointer !important;
}
.stButton > button:hover {
    background: var(--gold-h) !important;
    transform: translateY(-2px) !important; box-shadow: 0 8px 24px var(--gold-glow) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: var(--surf) !important; color: var(--txt) !important;
    border: 1px solid var(--border) !important; border-radius: 11px !important;
    height: 42px !important; font-size: .8rem !important; font-weight: 500 !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--border-h) !important; background: var(--card-alt) !important;
    transform: none !important; box-shadow: none !important;
}

/* Selectbox */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
    background: var(--surf) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important; color: var(--txt) !important;
}

/* Textarea */
.stTextArea > div > div > textarea {
    background: var(--surf) !important; color: var(--txt) !important;
    border: 1px solid var(--border) !important; border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .78rem !important; line-height: 1.65 !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: rgba(232,168,56,.45) !important;
    box-shadow: 0 0 0 3px var(--gold-dim) !important; outline: none !important;
}

/* Code blocks */
[data-testid="stCode"] > div {
    background: var(--surf) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* Alerts */
[data-testid="stAlertContainer"] { border-radius: 12px !important; }
hr { border-color: var(--border) !important; }

/* ════════════════════════════════════════════════
   UTILITY CLASSES
════════════════════════════════════════════════ */
.lbl {
    font-size: .67rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .1em; color: var(--muted); margin-bottom: 8px; display: block;
}
.tag {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 2px 8px; border-radius: 5px;
    font-size: .63rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
}
.tag-html { background: rgba(249,115,22,.12); color: #f97316; }
.tag-py   { background: rgba(99,102,241,.12);  color: #818cf8; }
.tag-img  { background: rgba(16,185,129,.12);  color: #10b981; }

/* Section heading */
.sec-head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
}
.sec-title {
    display: flex; align-items: center; gap: 10px;
}
.sec-icon {
    width: 36px; height: 36px; border-radius: 10px;
    display: grid; place-items: center; font-size: 1rem; flex-shrink:0;
}
.icon-gold   { background: var(--gold-dim); }
.icon-indigo { background: var(--indigo-dim); }
.sec-name {
    font-family: 'Syne', sans-serif; font-size: .95rem;
    font-weight: 700; color: var(--txt); line-height: 1.2;
}
.sec-desc { font-size: .72rem; color: var(--muted); }

/* Deploy info banner */
.dinfo {
    display: flex; align-items: flex-start; gap: 13px;
    background: rgba(16,185,129,.055); border: 1px solid rgba(16,185,129,.22);
    border-radius: 13px; padding: 14px 18px; margin-bottom: 14px;
}
.dinfo-txt { font-size: .84rem; font-weight: 600; color: var(--green); }
.dinfo-sub { font-size: .72rem; color: var(--muted); margin-top: 3px; }

/* Browser chrome for live preview */
.browser-bar {
    background: var(--surf); border: 1px solid var(--border);
    border-bottom: none; border-radius: 14px 14px 0 0;
    padding: 10px 16px; display: flex; align-items: center; gap: 12px;
}
.bdots { display: flex; gap: 5px; }
.bd { width: 10px; height: 10px; border-radius: 50%; }
.bd-r { background: #f43f5e; }
.bd-y { background: #f59e0b; }
.bd-g { background: var(--green); }
.burl {
    flex: 1; background: var(--card); border: 1px solid var(--border);
    border-radius: 6px; padding: 3px 12px;
    font-family: 'JetBrains Mono', monospace; font-size: .68rem; color: var(--muted);
}
.browser-frame {
    border: 1px solid var(--border); border-top: none;
    border-radius: 0 0 14px 14px; overflow: hidden;
}

/* Empty state */
.empty-state {
    text-align: center; padding: 72px 24px;
}
.empty-icon { font-size: 2.8rem; opacity: .2; margin-bottom: 16px; }
.empty-title { font-size: .9rem; font-weight: 600; color: var(--muted); }
.empty-sub   { font-size: .76rem; color: var(--muted); opacity: .6; margin-top: 6px; }

/* ════════════════════════════════════════════════
   ANIMATIONS
════════════════════════════════════════════════ */
@keyframes blink  { 0%,100%{opacity:1} 50%{opacity:.28} }
@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
.fade-up  { animation: fadeUp .45s ease-out both; }
.fade-up2 { animation: fadeUp .45s .12s ease-out both; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--sub); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-h); }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  API GUARD
# ══════════════════════════════════════════════════════════════════════════════
if not OLLAMA_API_KEY:
    st.markdown('<div style="height:64px"></div>', unsafe_allow_html=True)
    st.error("⚠️  `OLLAMA_API_KEY` is missing. Add it to your `.env` file and restart the server.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def call_ollama_cloud(prompt: str, images=None):
    """
    Calls the Ollama Cloud API (compatible with standard Ollama API).
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        # Browser-mimic headers to prevent 404 blocks from cloud proxies
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "HTTP-Referer": "https://aidrivendesignprototyping.streamlit.app/",
        "X-Title": "ADDP - AI Driven Design Prototyping"
    }
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    
    if images:
        # images list expected to contain base64 strings
        payload["images"] = images
        
    try:
        # Pre-clean the URL to ensure no double slashes (like https://ollama.com//api/generate)
        base_url = OLLAMA_URL.rstrip("/")
        endpoint = f"{base_url}/api/generate"
        
        # Using a session to handle local proxy intercepts more reliably
        session = requests.Session()
        response = session.post(endpoint, headers=headers, json=payload, timeout=300, verify=False)
        
        if response.status_code == 401 or "unauthorized" in response.text.lower():
            st.error("Ollama Cloud: Unauthorized. Please check your API Key.")
            return ""
            
        response.raise_for_status()
        raw_output = response.json().get("response", "")
        
        # Deep cleaning: mirrors ShadowPrep's LLMHelper.cleanJsonResponse()
        clean_text = re.sub(r"<thought>[\s\S]*?<\/thought>", "", raw_output, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"<reasoning>[\s\S]*?<\/reasoning>", "", clean_text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"```[a-zA-Z]*\n?", "", clean_text).replace("```", "").strip()
        
        return clean_text
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

# ══════════════════════════════════════════════════════════════════════════════
#  SERVER STATUS (auto-detect crash)
# ══════════════════════════════════════════════════════════════════════════════
_proc = st.session_state.backend_proc
if _proc is not None and _proc.poll() is not None:
    st.session_state.backend_proc = None
    _proc = None
_server_on = _proc is not None

# ══════════════════════════════════════════════════════════════════════════════
#  NAVBAR
# ══════════════════════════════════════════════════════════════════════════════
_pill_cls = "srv-on"      if _server_on else "srv-off"
_dot_cls  = "srv-dot-on"  if _server_on else "srv-dot-off"
_srv_txt  = (f"localhost:5000 &nbsp;·&nbsp; PID {_proc.pid}" if _server_on
             else "No active server")

st.markdown(f"""
<nav class="nav">
  <div class="nav-logo">
    <div class="nav-mark">A</div>
    <div>
      <div class="nav-name">ADDP</div>
      <div class="nav-sub">AI Driven Design Prototyping</div>
    </div>
  </div>
  <div class="nav-badge">
    <div class="nav-spark"></div>
    Capstone project &nbsp;·&nbsp; Live Prototype
  </div>
  <div class="srv-pill {_pill_cls}">
    <div class="srv-dot {_dot_cls}"></div>
    {_srv_txt}
  </div>
</nav>
<div style="height:60px"></div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero fade-up">
  <div class="hero-eye">⬡ &nbsp; Powered by Ollama Cloud (qwen3-vl)</div>
  <h1 class="hero-h1">
    <span class="grad">AI Driven</span><br>Design Prototyping
  </h1>
  <p class="hero-p" style="text-align: center !important; width: 100% !important;">
    ADDP bridges the gap between architectural vision and production software. Upload any UML blueprint and receive a complete full-stack application — or reverse-engineer your codebase into clean visual diagrams.
  </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODE TOGGLE
# ══════════════════════════════════════════════════════════════════════════════
_, _tc, _ = st.columns([1, 2, 1])
with _tc:
    mode = st.radio(
        "mode_sel",
        ["Diagram → Full Stack", "Code → Architecture"],
        label_visibility="collapsed",
        horizontal=True,
    )

st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CONTENT WRAPPER
# ══════════════════════════════════════════════════════════════════════════════
_, _mc, _ = st.columns([1, 10, 1])

with _mc:

    # ══════════════════════════════════════════
    #  A: DIAGRAM → FULL STACK
    # ══════════════════════════════════════════
    if mode == "Diagram → Full Stack":

        # ── Upload section ────────────────────
        with st.container(border=True):
            st.markdown("""
            <div class="sec-head">
              <div class="sec-title">
                <div class="sec-icon icon-gold">📐</div>
                <div>
                  <div class="sec-name">Blueprint Input</div>
                  <div class="sec-desc">Upload a UML, flow, sequence, ER, or architecture diagram (PNG / JPG)</div>
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
                st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
                _, _ic, _ = st.columns([1, 4, 1])
                with _ic:
                    st.image(upload, caption="Uploaded Blueprint", use_container_width=True)

                img_bytes = upload.getvalue()
                mime_type = upload.type or "image/png"

                st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

                if st.button("⬡  Synthesize Full-Stack Application", key="gen_btn"):
                    with st.spinner("Analysing blueprint via Ollama Cloud and generating your application…"):
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

                            # Convert image to base64 for Ollama
                            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                            
                            _raw = call_ollama_cloud(_prompt, images=[img_b64])

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

        # ── Generated output ──────────────────
        if st.session_state.gen_f or st.session_state.gen_b:
            st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

            col_f, col_b = st.columns(2, gap="large")

            # — Frontend column —
            with col_f:
                with st.container(border=True):
                    st.markdown("""
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-gold">🌐</div>
                        <div>
                          <div class="sec-name">Frontend Layer</div>
                          <div class="sec-desc">HTML · Tailwind CSS</div>
                        </div>
                      </div>
                      <span class="tag tag-html">HTML</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.session_state.gen_f:
                        st.code(st.session_state.gen_f, language="html")
                        st.download_button(
                            "⬇  Download index.html",
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
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-indigo">⚙️</div>
                        <div>
                          <div class="sec-name">Backend Layer</div>
                          <div class="sec-desc">Flask · REST API · Port 5000</div>
                        </div>
                      </div>
                      <span class="tag tag-py">Python</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.session_state.gen_b:
                        st.code(st.session_state.gen_b, language="python")
                        st.download_button(
                            "⬇  Download backend.py",
                            st.session_state.gen_b,
                            file_name="backend.py",
                            mime="text/plain",
                            key="dl_b",
                        )
                        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

                        # ── Deploy controls ───────────────────────
                        if _server_on:
                            _pid = _proc.pid if _proc else "—"
                            st.markdown(f"""
                            <div class="dinfo">
                              <span style="font-size:1.35rem">🟢</span>
                              <div>
                                <div class="dinfo-txt">Server running on localhost:5000</div>
                                <div class="dinfo-sub">PID {_pid} · Flask · Active this session</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("🔴  Stop Server", key="stop_btn"):
                                stop_backend()
                                st.rerun()
                        else:
                            if st.button("🚀  Deploy to Localhost (port 5000)", key="deploy_btn"):
                                with st.spinner("Launching Flask server…"):
                                    start_backend(st.session_state.gen_b)
                                st.success("✅  Server deployed successfully on port 5000.")
                                st.rerun()
                    else:
                        st.caption("Backend was not generated in this response.")

            # ── Live preview ──────────────────
            if st.session_state.gen_f:
                st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)

                st.markdown("""
                <div class="browser-bar">
                  <div class="bdots">
                    <div class="bd bd-r"></div>
                    <div class="bd bd-y"></div>
                    <div class="bd bd-g"></div>
                  </div>
                  <div class="burl">localhost · Live Preview</div>
                </div>
                <div class="browser-frame">
                """, unsafe_allow_html=True)

                _prev = st.session_state.gen_f
                if "tailwindcss" not in _prev:
                    _prev = '<script src="https://cdn.tailwindcss.com"></script>\n' + _prev
                st.components.v1.html(_prev, height=580, scrolling=True)

                st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    #  B: CODE → ARCHITECTURE
    # ══════════════════════════════════════════
    else:
        col_in, col_out = st.columns([1, 1], gap="large")

        # — Input column —
        with col_in:
            with st.container(border=True):
                st.markdown("""
                <div class="sec-head" style="margin-bottom:16px">
                  <div class="sec-title">
                    <div class="sec-icon icon-indigo">🔁</div>
                    <div>
                      <div class="sec-name">Architecture Extraction</div>
                      <div class="sec-desc">Reverse-engineer code into UML diagrams</div>
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
                        "// Paste your source code here…\n\n"
                        "class UserService {\n"
                        "  constructor(private db: Database) {}\n"
                        "  async getUser(id: string) { … }\n"
                        "}"
                    ),
                    label_visibility="collapsed",
                    key="code_input",
                )

                st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

                if st.button("🔁  Extract Architecture Diagram", key="extract_btn"):
                    if not code_in.strip():
                        st.error("Please paste some source code before extracting.")
                    else:
                        with st.spinner(f"Analysing code via Ollama Cloud and building {uml_choice}…"):
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

                                _raw = call_ollama_cloud(_prompt)
                                _raw = _strip_fences(_raw.strip())

                                _s = min(
                                    _raw.find("{") if "{" in _raw else len(_raw),
                                    _raw.find("[") if "[" in _raw else len(_raw),
                                )
                                _e = max(
                                    _raw.rfind("}") if "}" in _raw else -1,
                                    _raw.rfind("]") if "]" in _raw else -1,
                                )
                                _data = json.loads(_raw[_s: _e + 1])

                                # ── Build Graphviz diagram ──────────────────
                                _dot = Digraph(format="png")
                                _dot.attr(rankdir="LR", dpi="180",
                                          fontname="DM Sans", bgcolor="#131319", pad="0.6")
                                _dot.attr("node",
                                          style="filled", fillcolor="#1a1a22",
                                          color="#e8a838", fontcolor="#eeeef3",
                                          fontname="DM Sans", fontsize="11")
                                _dot.attr("edge",
                                          color="#68687e", fontcolor="#68687e",
                                          fontname="DM Sans", fontsize="9")

                                if uml_choice == "Class Diagram" and isinstance(_data, list):
                                    for _cls in _data:
                                        _n  = _cls.get("name", "Unknown")
                                        _at = "\\l".join(_cls.get("attributes", []) or [])
                                        _mt = "\\l".join(_cls.get("methods", []) or [])
                                        _dot.node(_n, f"{{{_n}|{_at}\\l|{_mt}\\l}}", shape="record")
                                        for _r in (_cls.get("relations") or []):
                                            _tgt = _r.get("target") or _r.get("to", "")
                                            if _tgt:
                                                _dot.edge(_n, _tgt, label=_r.get("type", ""))

                                elif uml_choice == "Sequence Diagram":
                                    for _p in _data.get("participants", []):
                                        _dot.node(_p, shape="box")
                                    for _m in _data.get("messages", []):
                                        _f2 = _m.get("from", "")
                                        _t2 = _m.get("to", "")
                                        if _f2 and _t2:
                                            _dot.edge(_f2, _t2, label=_m.get("message", ""))

                                elif uml_choice == "Use Case Diagram":
                                    for _uc in _data.get("use_cases", []):
                                        _dot.node(_uc, shape="ellipse")
                                    for _ac in _data.get("actors", []):
                                        _dot.node(_ac, shape="box",
                                                  color="#6366f1", fillcolor="#1c1c2e")
                                    for _r2 in _data.get("relations", []):
                                        _a2 = _r2.get("actor", "")
                                        _u2 = _r2.get("use_case", "")
                                        if _a2 and _u2:
                                            _dot.edge(_a2, _u2)

                                elif uml_choice == "Activity Diagram":
                                    _steps = _data.get("steps", [])
                                    for _i, _sn in enumerate(_steps):
                                        _shp = "oval" if _i in (0, len(_steps) - 1) else "box"
                                        _dot.node(str(_sn), shape=_shp)
                                        if _i > 0:
                                            _dot.edge(str(_steps[_i - 1]), str(_sn))

                                elif uml_choice == "Component Diagram":
                                    for _comp in _data.get("components", []):
                                        _cn = (_comp if isinstance(_comp, str)
                                               else _comp.get("name", "?"))
                                        _dot.node(_cn, shape="component")
                                    for _conn in _data.get("connections", []):
                                        _cs = _conn.get("source", "")
                                        _ct = _conn.get("target", "")
                                        if _cs and _ct:
                                            _dot.edge(_cs, _ct)

                                st.session_state.diagram_img  = _dot.pipe(format="png")
                                st.session_state.diagram_type = uml_choice
                                st.rerun()

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
                    <div class="sec-head">
                      <div class="sec-title">
                        <div class="sec-icon icon-gold">📊</div>
                        <div>
                          <div class="sec-name">{st.session_state.diagram_type}</div>
                          <div class="sec-desc">Auto-generated from source analysis</div>
                        </div>
                      </div>
                      <span class="tag tag-img">PNG</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.image(
                        st.session_state.diagram_img,
                        caption=st.session_state.diagram_type,
                        use_container_width=True,
                    )
                    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
                    st.download_button(
                        "⬇  Download Diagram (PNG)",
                        st.session_state.diagram_img,
                        file_name="architecture_diagram.png",
                        mime="image/png",
                        key="dl_diag",
                    )
            else:
                with st.container(border=True):
                    st.markdown("""
                    <div class="empty-state">
                      <div class="empty-icon">📊</div>
                      <div class="empty-title">Your diagram will appear here</div>
                      <div class="empty-sub">Paste source code on the left, then click Extract</div>
                    </div>
                    """, unsafe_allow_html=True)

# ── Bottom padding ─────────────────────────────────────────────────────────────
st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)