import os
import sys
import json
import re
import streamlit as st
import google.generativeai as genai
from graphviz import Digraph
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# ------------------- FIX GRAPHVIZ (Local Windows Logic) -------------------
# On Streamlit Cloud, graphviz is pre-installed via packages.txt
# This block attempts to find it on Windows if standard paths fail
IF_WINDOWS = os.name == 'nt'
if IF_WINDOWS:
    GRAPHVIZ_BIN = r"C:\Program Files\Graphviz\bin"
    if os.path.exists(GRAPHVIZ_BIN):
        os.environ["PATH"] += os.pathsep + GRAPHVIZ_BIN

# ------------------- PREMIUM STYLING -------------------
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: scale(1.02);
    }
    .stTextArea textarea {
        border-radius: 15px;
    }
    .css-1kyxreq {
        justify-content: center;
    }
    header {visibility: hidden;}
    .reportview-container .main footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI UML ↔ Premium Frontend Generator")
st.caption("Transform abstract diagrams into functional UI • Extract architecture into visual UML")

# ------------------- GEMINI CONFIG -------------------
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.warning("⚠️ API Key not found. Please set `GEMINI_API_KEY` in your .env file or Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)
st.success("✅ Gemini AI Pro Connected!")

# ------------------- UTILITY -------------------
def clean_html(code):
    # Remove markdown code blocks if present
    code = re.sub(r"```[a-zA-Z]*\n", "", code)
    code = re.sub(r"```", "", code)
    return code.strip()

def is_html(code):
    c = code.lower()
    return (
        "<html" in c or "<div" in c or "<form" in c or "<input" in c or
        "<section" in c or "<button" in c or c.startswith("<")
    )

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("Settings")
    mode = st.radio("Select Mode:", ["UML → Functional UI", "Code → UML Diagram"])
    st.markdown("---")
    st.info("Built for Capstone Project 🎓")

# =====================================================================
# 1️⃣ UML IMAGE → FUNCTIONAL UI (GENERATE READY-TO-USE APP)
# =====================================================================
if mode == "UML → Functional UI":
    st.subheader("🎨 Convert Diagram → Fully Functional Web App")
    st.write("Upload a business diagram (Sequence, Use Case, etc.) and get a working frontend implementation.")

    upload = st.file_uploader("Upload Diagram (PNG/JPG)", type=["png", "jpg", "jpeg"])
    fmt = st.selectbox("Tech Stack:", ["HTML + Tailwind CSS", "React (JSX) + Tailwind"])

    if upload:
        st.image(upload, caption="Source Diagram", use_container_width=True)
        img_bytes = upload.read()

        if st.button("🚀 Synthesize Functional App"):
            with st.spinner("Analyzing architecture and coding UI..."):
                model = genai.GenerativeModel("models/gemini-2.5-flash")

                prompt = f"""
                You are a world-class Frontend Architect.
                
                USER GOAL: Convert this UML/Flow diagram into a REAL, FUNCTIONAL, and BEAUTIFULLY STYLED {fmt} application.
                
                CRITICAL INSTRUCTIONS:
                - DO NOT RECREATE THE DIAGRAM as lines/boxes. 
                - INTERPRET the meaning: If it's a 'Restaurant Order sequence', build a real Restaurant Ordering System with a Menu, Cart, and Checkout UI.
                - If it's a 'Login process', build a complete, sleek Auth page.
                - Use Tailwind CSS for premium, modern aesthetics (rounded corners, shadows, glassmorphism).
                - Ensure the UI is responsive and "ready to use".
                - PRODUCE ONLY {fmt} code. NO markdown backticks.
                """

                resp = model.generate_content([prompt, {"mime_type":"image/png","data":img_bytes}])
                code = clean_html(resp.text)

                st.subheader("📦 Generated Code")
                st.code(code, language="html" if "HTML" in fmt else "jsx")

                # Download
                ext = "html" if "HTML" in fmt else "jsx"
                st.download_button("⬇ Download Project File", code, f"app.{ext}")

                # Live Preview
                if "HTML" in fmt and is_html(code):
                    st.subheader("🖥️ Interactive Live Preview")
                    # Injecting Tailwind CDN if not present for preview
                    if "cdn.tailwindcss.com" not in code:
                        code = f'<script src="https://cdn.tailwindcss.com"></script>\n{code}'
                    st.components.v1.html(code, height=600, scrolling=True)

# =====================================================================
# 2️⃣ FRONTEND CODE → ANY UML DIAGRAM (RENDER IMAGE)
# =====================================================================
else:
    st.subheader("📐 Structural Extraction: Code → UML Diagram")
    st.write("Input your code to generate a visual architecture diagram.")

    uml_type = st.selectbox("Target UML Type:", [
        "Class Diagram", "Sequence Diagram", "Use Case Diagram", 
        "Activity Diagram", "Component Diagram"
    ])

    code_input = st.text_area("Paste your Code (HTML/JS/React) here", height=300, placeholder="import React from 'react'...")

    if st.button("🎯 Generate Visual Diagram"):
        if not code_input.strip():
            st.error("Please provide code input first!")
            st.stop()

        with st.spinner("Generating architecture..."):
            model = genai.GenerativeModel("models/gemini-2.5-flash")

            prompt = f"""
            Reverse engineer the following code into a {uml_type}.
            
            Return ONLY a valid JSON object. No other text.
            
            STRUCTURES:
            - Class Diagram: [{{ "name": "ClassA", "attributes": ["attr1"], "methods": ["do()"], "relations": [{{ "target": "ClassB" }}] }}]
            - Sequence Diagram: {{ "participants": ["User", "Service"], "messages": [{{ "from": "User", "to": "Service", "message": "request()" }}] }}
            - Use Case Diagram: {{ "actors": ["User"], "use_cases": ["Action"], "relations": [{{ "actor": "User", "use_case": "Action" }}] }}
            - Activity Diagram: {{ "steps": ["Start", "Process", "End"] }}
            - Component Diagram: {{ "components": [{{ "name": "A" }}], "connections": [{{ "source": "A", "target": "B" }}] }}
            """

            resp = model.generate_content(prompt + "\n\n" + code_input)
            raw = resp.text.strip()

            try:
                start_idx = min(raw.find('{') if '{' in raw else len(raw), raw.find('[') if '[' in raw else len(raw))
                end_idx = max(raw.rfind('}') if '}' in raw else -1, raw.rfind(']') if ']' in raw else -1)
                data = json.loads(raw[start_idx:end_idx+1])
            except Exception:
                st.error("Could not parse AI response. Retrying with simpler prompt...")
                st.stop()

            # ---------- RENDER ----------
            dot = Digraph(format="png")
            dot.attr(rankdir="LR", dpi="300", fontname="Arial")
            dot.attr('node', shape='rect', style='filled', fillcolor='#E1F5FE')

            if uml_type=="Class Diagram" and isinstance(data, list):
                for cls in data:
                    name = cls.get("name", "Unknown")
                    attrs = "\\l".join(cls.get("attributes", []) or [])
                    methods = "\\l".join(cls.get("methods", []) or [])
                    label = f"{{{name}|{attrs}\\l|{methods}\\l}}"
                    dot.node(name, label, shape="record")
                    for rel in cls.get("relations", []) or []:
                        target = rel.get("target") or rel.get("to")
                        if target: dot.edge(name, target)

            elif uml_type=="Sequence Diagram":
                participants = data.get("participants") or data.get("objects") or []
                for p in participants:
                    dot.node(p if isinstance(p, str) else p.get("name", "Unknown"), shape="box")
                for m in data.get("messages", []):
                    dot.edge(m.get("from"), m.get("to"), label=m.get("message") or m.get("msg"))

            elif uml_type=="Use Case Diagram":
                for uc in data.get("use_cases", []) or data.get("usecases", []):
                    dot.node(uc, shape="ellipse", fillcolor="#FFF9C4")
                for actor in data.get("actors", []):
                    dot.node(actor, shape="box", fillcolor="#F8BBD0")
                for rel in data.get("relations", []):
                    dot.edge(rel.get("actor"), rel.get("use_case") or rel.get("usecase"))

            elif uml_type=="Activity Diagram":
                dot.node("Start", shape="circle", fillcolor="black", fontcolor="white")
                prev = "Start"
                for step in data.get("steps", []):
                    dot.node(step)
                    dot.edge(prev, step)
                    prev = step
                dot.node("End", shape="doublecircle", fillcolor="black", fontcolor="white")
                dot.edge(prev, "End")

            elif uml_type=="Component Diagram":
                for c in data.get("components", []):
                    dot.node(c.get("name"), shape="component")
                for conn in data.get("connections", []) or data.get("links", []):
                    dot.edge(conn.get("source"), conn.get("target"))

            try:
                st.image(dot.pipe(format='png'), caption=f"Generated {uml_type}", use_container_width=True)
                
                with st.expander("Show Technical JSON Data"):
                    st.json(data)
                    
                st.download_button("⬇ Download Diagram", dot.pipe(format='png'), "architecture.png")
            except Exception as ge:
                st.error(f"Graphviz rendering failed. Please check local installation. Error: {ge}")
