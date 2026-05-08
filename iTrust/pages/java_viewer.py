"""
pages/java_viewer.py
Dedicated Java source viewer page.
URL: /java_viewer?file=PatientDAO.java&methods=method1,method2,...

Renders full Java source with:
  - Syntax highlighting via highlight.js (github-dark theme)
  - In-source line highlighting for impacted method declarations
  - Line numbers (GitHub-style table layout)
  - Jump-to-method chip navigation
  - Download button
"""
import sys
import json
import html
import urllib.parse
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from services.data_loader import build_file_index

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Java Viewer — CIA System", layout="wide")

# Hide Streamlit chrome on viewer page too
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stAppDeployButton { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stFooter"] { visibility: hidden !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.stButton>button{
  border-radius:8px!important;padding:8px 20px!important;
  font-weight:500!important;transition:opacity 0.2s!important;
}
.stButton>button:hover{opacity:0.85!important;}
</style>
""", unsafe_allow_html=True)

# ── Read query params ────────────────────────────────────────────────────────
try:
    params   = st.query_params
    filename = params.get("file", "")
    methods_raw = params.get("methods", "")
except Exception:
    filename, methods_raw = "", ""

if not filename:
    st.error("No file specified. Open this viewer from the main CIA dashboard.")
    st.stop()

# Decode
filename     = urllib.parse.unquote(filename)
methods_raw  = urllib.parse.unquote(methods_raw)
impacted_methods = [m.strip() for m in methods_raw.split(",") if m.strip()] if methods_raw else []

# ── Resolve file path ────────────────────────────────────────────────────────
file_index = build_file_index()
file_path  = file_index.get(filename)

# ── Header bar ──────────────────────────────────────────────────────────────
col_back, col_title, col_dl = st.columns([1, 6, 2])
with col_back:
    st.markdown(
        '<a href="javascript:window.close()" style="color:#8B949E;text-decoration:none;font-size:14px;">✕ Close</a>',
        unsafe_allow_html=True,
    )
with col_title:
    st.markdown(
        f'<p style="font-family:monospace;font-size:18px;color:#4FC3F7;font-weight:600;margin:0;">'
        f'📄 {html.escape(filename)}</p>',
        unsafe_allow_html=True,
    )

# ── Load source ──────────────────────────────────────────────────────────────
if file_path is None:
    st.error(f"⚠️ Source file **{filename}** not found in the `code/` directory.")
    st.stop()

try:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# Download button
with col_dl:
    st.download_button(
        "⬇ Download",
        data=source.encode("utf-8"),
        file_name=filename,
        mime="text/x-java-source",
    )

# ── Build the HTML viewer ────────────────────────────────────────────────────
# Extract bare method names for JS matching
bare_methods = list(set([
    m.split(".")[-1].split("(")[0].strip()
    for m in impacted_methods if m
]))

# Escape source for embedding as JS string
escaped_source  = json.dumps(source)
escaped_methods = json.dumps(bare_methods)
escaped_fname   = json.dumps(filename)

num_lines = source.count("\n") + 1
viewer_height = min(max(num_lines * 20 + 160, 600), 4000)

# Pick highlight.js theme based on Streamlit theme stored in session_state
# (Streamlit sets st.session_state._stcore_theme when theme changes)
_hljs_theme = "github-dark"
try:
    import streamlit.runtime.scriptrunner as _sr
    _theme = st.get_option("theme.base") or ""
    if _theme == "light":
        _hljs_theme = "github"
except Exception:
    pass

VIEWER_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/{_hljs_theme}.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --v-bg:#0D1117;--v-surface:#161B22;--v-border:#30363D;
  --v-text:#E6EDF3;--v-muted:#8B949E;--v-faint:#484F58;
  --v-accent:#4FC3F7;--v-chip-text:#FFA657;--v-hl:rgba(255,166,87,0.13);
}}
@media(prefers-color-scheme:light){{
  :root{{
    --v-bg:#FFFFFF;--v-surface:#F6F8FA;--v-border:#D0D7DE;
    --v-text:#1F2328;--v-muted:#656D76;--v-faint:#9198A1;
    --v-accent:#0969DA;--v-chip-text:#CF6A00;--v-hl:rgba(255,166,0,0.12);
  }}
}}
body{{background:var(--v-bg);color:var(--v-text);font-family:'Segoe UI',system-ui,sans-serif;}}

/* Method chips bar */
#chips-bar{{
  background:var(--v-surface);border-bottom:1px solid var(--v-border);
  padding:8px 12px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;
  position:sticky;top:0;z-index:50;
}}
#chips-bar .label{{font-size:12px;color:var(--v-muted);margin-right:4px;white-space:nowrap;}}
.chip{{
  background:var(--v-bg);border:1px solid var(--v-border);color:var(--v-chip-text);
  padding:3px 10px;border-radius:20px;font-size:12px;cursor:pointer;
  font-family:monospace;transition:all 0.15s;white-space:nowrap;
}}
.chip:hover{{background:var(--v-chip-text);color:var(--v-bg);border-color:var(--v-chip-text);}}

/* Code table */
.code-wrap{{overflow-x:auto;}}
table.ctable{{
  width:100%;border-collapse:collapse;
  font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
  font-size:13px;line-height:1.6;
}}
.ctable tr{{vertical-align:top;}}
.ctable tr:hover td{{background:color-mix(in srgb,var(--v-text) 3%,transparent);}}
.ctable td.ln{{
  min-width:48px;padding:0 12px;text-align:right;
  color:var(--v-faint);user-select:none;border-right:1px solid var(--v-border);
  white-space:nowrap;
}}
.ctable td.code{{padding:0 8px;white-space:pre;}}

/* Highlighted line */
.hl-row td{{
  background:var(--v-hl) !important;
  border-left:3px solid var(--v-chip-text);
}}
.hl-row td.ln{{color:var(--v-chip-text) !important;}}

/* No results banner */
#no-methods{{
  padding:12px 16px;background:var(--v-surface);color:var(--v-muted);
  font-size:13px;text-align:center;display:none;
}}
</style>
</head>
<body>
<div id="chips-bar">
  <span class="label">⚡ Impacted:</span>
  <span id="chips-container"></span>
  <span id="no-methods">No impacted methods specified.</span>
</div>
<div class="code-wrap">
  <table class="ctable" id="ctable"></table>
</div>

<script>
const rawSource  = {escaped_source};
const methods    = {escaped_methods};
const filename   = {escaped_fname};

// 1. Syntax-highlight the full source
const highlighted = hljs.highlight(rawSource, {{language:'java'}}).value;

// 2. Split highlighted HTML into lines
//    (split on newlines inside the HTML string)
const hlLines = highlighted.split('\\n');
const rawLines = rawSource.split('\\n');

// 3. Find which line numbers (0-based) contain method declarations
const methodLineMap = {{}};  // methodName -> first matching line index
const highlightedLineNos = new Set();

methods.forEach(method => {{
  if (!method) return;
  // Match: method name followed by '(' — covers declarations & calls
  const re = new RegExp('\\\\b' + method.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&') + '\\\\s*\\\\(', 'g');
  rawLines.forEach((line, i) => {{
    if (re.test(line)) {{
      highlightedLineNos.add(i);
      if (!(method in methodLineMap)) methodLineMap[method] = i;
    }}
    re.lastIndex = 0;
  }});
}});

// 4. Build code table
const table = document.getElementById('ctable');
hlLines.forEach((line, i) => {{
  const tr = document.createElement('tr');
  tr.id = 'L' + (i + 1);
  if (highlightedLineNos.has(i)) tr.className = 'hl-row';

  const tdLn   = document.createElement('td');
  tdLn.className = 'ln';
  tdLn.textContent = i + 1;

  const tdCode = document.createElement('td');
  tdCode.className = 'code';
  tdCode.innerHTML = line || ' ';

  tr.appendChild(tdLn);
  tr.appendChild(tdCode);
  table.appendChild(tr);
}});

// 5. Build chips and scroll
const chipsContainer = document.getElementById('chips-container');
const noMethodsEl    = document.getElementById('no-methods');

if (methods.length === 0) {{
  noMethodsEl.style.display = 'block';
}} else {{
  methods.forEach(method => {{
    if (!method) return;
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = method;
    chip.title = method in methodLineMap
      ? 'Jump to line ' + (methodLineMap[method] + 1)
      : 'Not found in this file';
    chip.onclick = () => {{
      if (method in methodLineMap) {{
        const el = document.getElementById('L' + (methodLineMap[method] + 1));
        if (el) el.scrollIntoView({{behavior:'smooth', block:'center'}});
      }}
    }};
    chipsContainer.appendChild(chip);
  }});
}}

// 6. Auto-scroll to first highlighted line
if (highlightedLineNos.size > 0) {{
  const firstLine = Math.min(...highlightedLineNos);
  setTimeout(() => {{
    const el = document.getElementById('L' + (firstLine + 1));
    if (el) el.scrollIntoView({{behavior:'smooth', block:'center'}});
  }}, 300);
}}
</script>
</body>
</html>"""

st.components.v1.html(VIEWER_HTML, height=viewer_height, scrolling=True)

# Stats footer
st.caption(f"📊 {num_lines:,} lines · {len(source):,} bytes · {len(impacted_methods)} impacted method(s) highlighted")
