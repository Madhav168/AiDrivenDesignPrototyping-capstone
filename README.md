# AI UML ↔ Frontend Code Generator

A powerful Streamlit-based tool that uses Google's Gemini 2.5 Flash model to convert UML diagrams into frontend code and vice-versa.

## Features
- **UML → Frontend Code**: Upload an image of a Sequence, Class, Use-case, Activity, or Component diagram and generate responsive HTML + CSS or React (JSX).
- **Frontend Code → UML**: Paste your code and generate a structured UML diagram (rendered via Graphviz).

---

## Local Setup Instructions

Follow these steps to run the project on your machine:

### 1. Prerequisites
- **Python 3.8+** installed.
- **Graphviz** installed on your system (Required for Code → UML mode).
  - **Windows**: Download from [Graphviz.org](https://graphviz.org/download/) and ensure `C:\Program Files\Graphviz\bin` exists.
  - **Linux/Mac**: Use `sudo apt install graphviz` or `brew install graphviz`.

### 2. Configure Environment Variables
1. Create a file named `.env` in the root directory (if it doesn't already exist).
2. Add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
   *You can get a free API key from [Google AI Studio](https://aistudio.google.com/).*

### 3. Run the Application
The application now automatically detects and installs missing Python libraries (`streamlit`, `google-generativeai`, etc.) on its first run.

Simply run:
```bash
streamlit run app.py
```

---

## Deployment to GitHub

When pushing this project to GitHub:
1. The `.env` file is ignored by `.gitignore` to keep your API key safe.
2. For **Streamlit Cloud** deployment:
   - Go to your app settings.
   - Add a Secret named `GEMINI_API_KEY` with your key.
   - Ensure `packages.txt` is present (included in this repo).
