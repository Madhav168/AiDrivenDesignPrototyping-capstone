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
            
            You MUST return ONLY JSON. NO MARKDOWN. NO CODE BLOCKS.
            
            FORMATS:
            - Class Diagram: [{{ "name": "A", "attributes": [], "methods": [], "relations": [{{ "target": "B" }}] }}]
            - Sequence Diagram: {{ "objects": ["User", "System"], "messages": [{{ "from": "User", "to": "System", "msg": "login()" }}] }}
            - Use Case Diagram: {{ "actors": ["User"], "use_cases": ["Login"], "relations": [{{ "actor": "User", "use_case": "Login" }}] }}
            - Activity Diagram: {{ "steps": ["Step 1", "Step 2"] }}
            - Component Diagram: {{ "components": [{{ "name": "UI" }}], "connections": [{{ "source": "UI", "target": "API" }}] }}
            """

            resp = model.generate_content(prompt + "\n\n" + code_input)
            raw = resp.text.strip()

            try:
                # Robust extraction: find the first '[' or '{' and the last ']' or '}'
                start_idx = min(raw.find('{') if '{' in raw else len(raw), raw.find('[') if '[' in raw else len(raw))
                end_idx = max(raw.rfind('}') if '}' in raw else -1, raw.rfind(']') if ']' in raw else -1)
                
                if start_idx == len(raw) or end_idx == -1:
                    raise ValueError("No JSON found in response")
                
                json_data = raw[start_idx:end_idx+1]
                data = json.loads(json_data)
            except Exception as e:
                st.error(f"Failed to parse AI response as JSON: {e}")
                st.info(f"Raw Response: {raw}")
                st.stop()

            st.subheader("📦 Extracted UML JSON")
            st.code(json.dumps(data, indent=2))

            dot = Digraph(format="png")
            dot.attr(rankdir="TB", dpi="300")

            if uml_type=="Class Diagram" and isinstance(data, list):
                for cls in data:
                    name = cls.get("name", "Unknown")
                    attrs = "\\l".join(cls.get("attributes", []) or [])
                    methods = "\\l".join(cls.get("methods", []) or [])
                    label = f"{{{name}|{attrs}\\l|{methods}\\l}}"
                    dot.node(name, label, shape="record")
                for cls in data:
                    name = cls.get("name", "Unknown")
                    for rel in cls.get("relations", []) or []:
                        target = rel.get("target") or rel.get("to")
                        if target:
                            dot.edge(name, target)

            elif uml_type=="Sequence Diagram":
                objs = data.get("objects") or data.get("participants") or []
                for obj in objs:
                    # Handle if objects are dicts or strings
                    name = obj if isinstance(obj, str) else obj.get("name", "Unknown")
                    dot.node(name, shape="box")
                
                msgs = data.get("messages") or []
                for msg in msgs:
                    f = msg.get("from")
                    t = msg.get("to")
                    m = msg.get("msg") or msg.get("message") or ""
                    if f and t:
                        dot.edge(f, t, label=m)

            elif uml_type=="Use Case Diagram":
                cases = data.get("use_cases") or data.get("usecases") or []
                dot.attr(shape="ellipse")
                for case in cases:
                    dot.node(case)
                
                actors = data.get("actors") or []
                dot.attr(shape="box")
                for actor in actors:
                    dot.node(actor)
                
                rels = data.get("relations") or []
                for rel in rels:
                    a = rel.get("actor")
                    u = rel.get("use_case") or rel.get("usecase")
                    if a and u:
                        dot.edge(a, u)

            elif uml_type=="Activity Diagram":
                dot.node("Start", shape="circle", style="filled", fillcolor="black")
                last = "Start"
                steps = data.get("steps") or []
                for step in steps:
                    dot.node(step, shape="rect")
                    dot.edge(last, step)
                    last = step
                dot.node("End", shape="doublecircle")
                dot.edge(last, "End")

            elif uml_type=="Component Diagram":
                comps = data.get("components") or []
                for c in comps:
                    name = c.get("name", "Unknown")
                    dot.node(name, shape="component")
                
                conns = data.get("connections") or data.get("links") or []
                for conn in conns:
                    s = conn.get("source") or conn.get("from")
                    t = conn.get("target") or conn.get("to")
                    if s and t:
                        dot.edge(s, t)

            output_path = "uml_output"
            dot.render(output_path, cleanup=True)
            st.image(f"{output_path}.png", caption=uml_type, use_container_width=True)

            with open(f"{output_path}.png","rb") as f:
                st.download_button("⬇ Download UML", f, "uml_output.png")
