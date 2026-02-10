import os
import sys
import subprocess
import json
import re

# ------------------- AUTO-INSTALL REQUIREMENTS -------------------
def install_dependencies():
    required = ["streamlit", "google-generativeai", "python-dotenv", "graphviz"]
    for package in required:
        try:
            __import__(package.replace("-", "_") if package != "google-generativeai" else "google.generativeai")
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])

install_dependencies()

import streamlit as st
import google.generativeai as genai
from graphviz import Digraph
from dotenv import load_dotenv

if __name__ == "__main__":
    if "streamlit" not in sys.modules:
        print("\n[!] To run this app, please use: streamlit run app.py")
        print("[!] If streamlit is not installed, run: pip install streamlit\n")
        # Optional: try to run it for them if possible, but safer to let them do it

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

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="AI UML ↔ Frontend Code Generator", layout="wide")
st.title("🧠 AI UML ↔ Frontend Code Generator")
st.caption("Convert ANY UML diagram ↔ Frontend UI • Convert Code → ANY UML Diagram")

# ------------------- GEMINI CONFIG -------------------
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.warning("⚠️ API Key not found. Please set `GEMINI_API_KEY` in your .env file or Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)
st.success("✅ Gemini AI Connected!")

# ------------------- UTILITY -------------------
def clean_html(code):
    code = re.sub(r"```html", "", code)
    code = re.sub(r"```", "", code)
    return code.strip()

def is_html(code):
    c = code.lower()
    return (
        "<html" in c or "<div" in c or "<form" in c or "<input" in c or
        "<section" in c or "<button" in c or c.startswith("<")
    )

# ------------------- SIDEBAR -------------------
mode = st.sidebar.radio("Select Mode:", ["UML → Frontend Code", "Frontend Code → UML Diagram"])

# =====================================================================
# 1️⃣ UML IMAGE → FRONTEND UI
# =====================================================================
if mode == "UML → Frontend Code":
    st.subheader("📥 Upload ANY UML Diagram → Generate UI Code")

    upload = st.file_uploader("Upload UML (PNG/JPG)", type=["png", "jpg", "jpeg"])
    fmt = st.selectbox("Output Format:", ["HTML + CSS", "React (JSX)"])

    if upload:
        st.image(upload, caption="UML Diagram", use_container_width=True)
        img_bytes = upload.read()

        if st.button("🚀 Generate UI Code"):
            with st.spinner("Understanding UML and generating UI…"):
                model = genai.GenerativeModel("models/gemini-2.5-flash")

                prompt = f"""
                You are a senior frontend engineer.
                Convert this UML diagram into a clean and working {fmt} UI layout.
                RULES:
                - DO NOT output any markdown or backticks.
                - PRODUCE ONLY real {fmt} code.
                OUTPUT = ONLY {fmt} CODE.
                """

                resp = model.generate_content([prompt, {"mime_type":"image/png","data":img_bytes}])
                code = clean_html(resp.text)

                st.subheader("🧩 Generated UI Code")
                st.code(code, language="html" if fmt=="HTML + CSS" else "jsx")

                ext = "html" if fmt=="HTML + CSS" else "jsx"
                st.download_button("⬇ Download", code, f"ui_output.{ext}")

                if fmt == "HTML + CSS" and is_html(code):
                    st.subheader("🎨 Live HTML Preview")
                    st.components.v1.html(code, height=650, scrolling=True)

# =====================================================================
# 2️⃣ FRONTEND CODE → ANY UML DIAGRAM
# =====================================================================
else:
    st.subheader("💻 Convert Frontend Code → UML Diagram")

    uml_type = st.selectbox("Choose UML Type:", [
        "Class Diagram", "Sequence Diagram", "Use Case Diagram", 
        "Activity Diagram", "Component Diagram"
    ])

    code_input = st.text_area("Paste your HTML / CSS / JS / React code here", height=300)

    if st.button("🎯 Generate UML Diagram"):
        if not code_input.strip():
            st.error("Paste code first!")
            st.stop()

        with st.spinner("Generating UML..."):
            model = genai.GenerativeModel("models/gemini-2.5-flash")

            prompt = f"""
            Convert the following frontend code into a structured {uml_type}.
            You MUST return ONLY JSON following the standard UML object format.
            OUTPUT STRICTLY = ONLY JSON. NO MARKDOWN.
            """

            resp = model.generate_content(prompt + "\n\n" + code_input)
            raw = resp.text.strip()

            try:
                match = re.search(r'\{.*\}|\[.*\]', raw, re.DOTALL)
                json_data = match.group(0)
                data = json.loads(json_data)
            except Exception as e:
                st.error(f"Failed to parse AI response as JSON: {e}")
                st.stop()

            st.subheader("📦 Extracted UML JSON")
            st.code(json.dumps(data, indent=2))

            dot = Digraph(format="png")
            dot.attr(rankdir="TB", dpi="300")

            if uml_type=="Class Diagram":
                for cls in data:
                    attrs = "\\l".join(cls.get("attributes", []))
                    methods = "\\l".join(cls.get("methods", []))
                    label = f"{{{cls['name']}|{attrs}\\l|{methods}\\l}}"
                    dot.node(cls["name"], label, shape="record")
                for cls in data:
                    for rel in cls.get("relations", []):
                        dot.edge(cls["name"], rel["target"])

            elif uml_type=="Sequence Diagram":
                for obj in data["objects"]:
                    dot.node(obj, shape="box")
                for msg in data["messages"]:
                    dot.edge(msg["from"], msg["to"], label=msg["msg"])

            elif uml_type=="Use Case Diagram":
                dot.attr(shape="ellipse")
                for case in data["use_cases"]:
                    dot.node(case)
                dot.attr(shape="box")
                for actor in data["actors"]:
                    dot.node(actor)
                for rel in data["relations"]:
                    dot.edge(rel["actor"], rel["use_case"])

            elif uml_type=="Activity Diagram":
                dot.node("Start", shape="circle", style="filled", fillcolor="black")
                last = "Start"
                for step in data["steps"]:
                    dot.node(step, shape="rect")
                    dot.edge(last, step)
                    last = step
                dot.node("End", shape="doublecircle")
                dot.edge(last, "End")

            elif uml_type=="Component Diagram":
                for c in data["components"]:
                    dot.node(c["name"], shape="component")
                for conn in data["connections"]:
                    dot.edge(conn["source"], conn["target"])

            output_path = "uml_output"
            dot.render(output_path, cleanup=True)
            st.image(f"{output_path}.png", caption=uml_type, use_container_width=True)

            with open(f"{output_path}.png","rb") as f:
                st.download_button("⬇ Download UML", f, "uml_output.png")
