"""
pages/viewer.py
Unified viewer page for both Java and Requirement files.
Handles:
  - /viewer?type=java&file=...&methods=...
  - /viewer?type=req&file=...

Supports:
  - New tab opening (target="_blank")
  - In-source line highlighting for Java
  - Keyword highlighting for Requirements
  - Clean browser-native source viewer feel
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
st.set_page_config(page_title="File Viewer — CIA System", layout="wide")

# Adaptive styles for the viewer (no sidebar)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
:root {
    --v-bg: #FFFFFF; --v-surface: #F6F8FA; --v-border: #D0D7DE; --v-text: #000000; --v-accent: #0969DA; --v-muted: #444444; --v-faint: #666666; --v-hl: rgba(255,166,0,0.12); --v-chip-text: #CF6A00;
}
@media (prefers-color-scheme: dark) {
    :root {
        --v-bg: #0D1117; --v-surface: #161B22; --v-border: #30363D; --v-text: #FFFFFF; --v-accent: #58A6FF; --v-muted: #8B949E; --v-faint: #484F58; --v-hl: rgba(56,139,253,0.15); --v-chip-text: #FFA657;
    }
}
[data-theme="dark"] {
    --v-bg: #0D1117; --v-surface: #161B22; --v-border: #30363D; --v-text: #FFFFFF; --v-accent: #58A6FF; --v-muted: #8B949E; --v-faint: #484F58; --v-hl: rgba(56,139,253,0.15); --v-chip-text: #FFA657;
}
.stApp { background: var(--v-bg); }
.stDeployButton{display:none!important;}
[data-testid="stDeployButton"]{display:none!important;}
[data-testid="stSidebarNav"]{display:none!important;}

.viewer-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 20px; background: var(--v-bg); border-bottom: 1px solid var(--v-border);
    position: sticky; top: 0; z-index: 100;
}
.filename { font-family: monospace; font-size: 18px; font-weight: 600; color: var(--v-accent); }
.close-btn { color: var(--v-muted); text-decoration: none; font-size: 14px; }
.close-btn:hover { color: var(--v-text); }
</style>
""", unsafe_allow_html=True)

# ── Query params ─────────────────────────────────────────────────────────────
try:
    params   = st.query_params
    v_type   = params.get("type", "java")
    filename = params.get("file", "")
except Exception:
    v_type, filename = "java", ""

if not filename:
    st.error("No file specified. Please open this viewer from the main CIA dashboard.")
    st.stop()

filename = urllib.parse.unquote(filename)

# ── Handle Java View ─────────────────────────────────────────────────────────
if v_type == "java":
    methods_raw = params.get("methods", "")
    methods_raw = urllib.parse.unquote(methods_raw)
    impacted_methods = [m.strip() for m in methods_raw.split(",") if m.strip()] if methods_raw else []
    
    file_index = build_file_index()
    file_path  = file_index.get(filename)
    
    if not file_path:
        st.error(f"Source file {filename} not found.")
        st.stop()
        
    source = Path(file_path).read_text(encoding="utf-8", errors="replace")
    
    # Header
    c1, c2, c3 = st.columns([1, 6, 2])
    with c1: st.markdown('<a href="javascript:window.close()" class="close-btn">✕ Close</a>', unsafe_allow_html=True)
    with c2: st.markdown(f'<span class="filename">📂 {html.escape(filename)}</span>', unsafe_allow_html=True)
    with c3: st.download_button("⬇ Download", source, file_name=filename)

    # HLJS Theme logic
    hljs_theme = "github-dark" if st.get_option("theme.base") != "light" else "github"
    
    # Bare method names for matching
    bare_methods = list(set([m.split(".")[-1].split("(")[0].strip() for m in impacted_methods if m]))
    
    escaped_source = json.dumps(source)
    escaped_methods = json.dumps(bare_methods)
    
    num_lines = source.count("\n") + 1
    v_height = min(max(num_lines * 20 + 160, 600), 5000)

    html_code = f"""<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/{hljs_theme}.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root {{
    --v-bg: #FFFFFF; --v-surface: #F6F8FA; --v-border: #D0D7DE; --v-text: #000000; --v-accent: #0969DA; --v-muted: #444444; --v-faint: #666666; --v-hl: rgba(255,166,0,0.12); --v-chip-text: #CF6A00;
}}
@media (prefers-color-scheme: dark) {{
    :root {{
        --v-bg: #0D1117; --v-surface: #161B22; --v-border: #30363D; --v-text: #FFFFFF; --v-accent: #58A6FF; --v-muted: #8B949E; --v-faint: #484F58; --v-hl: rgba(56,139,253,0.15); --v-chip-text: #FFA657;
    }}
}}
body{{background:var(--v-bg);color:var(--v-text);font-family:monospace;font-size:13px;}}
#chips{{background:var(--v-surface);padding:8px;border-bottom:1px solid var(--v-border);display:flex;gap:5px;flex-wrap:wrap;position:sticky;top:0;}}
.chip{{background:var(--v-bg);border:1px solid var(--v-border);color:var(--v-chip-text);padding:2px 8px;border-radius:12px;cursor:pointer;font-size:11px;}}
.chip:hover{{background:var(--v-chip-text);color:var(--v-bg);}}
table{{width:100%;border-collapse:collapse;line-height:1.6;}}
td.ln{{width:40px;text-align:right;padding-right:10px;color:var(--v-faint);user-select:none;border-right:1px solid var(--v-border);}}
td.code{{padding-left:10px;white-space:pre;}}
.hl-row td{{background:var(--v-hl)!important;border-left:3px solid var(--v-chip-text);}}
.hl-row td.ln{{color:var(--v-chip-text)!important;}}
</style>
</head>
<body>
<div id="chips"></div>
<table id="t"></table>
<script>
const src={escaped_source}; const meths={escaped_methods};
const hl = hljs.highlight(src, {{language:'java'}}).value;
const lines = hl.split('\\n'); const rLines = src.split('\\n');
const hlLines = new Set(); const map = {{}};
meths.forEach(m => {{
    const re = new RegExp('\\\\b' + m + '\\\\s*\\\\(', 'g');
    rLines.forEach((l, i) => {{ if(re.test(l)) {{ hlLines.add(i); if(!map[m]) map[m]=i; }} re.lastIndex=0; }});
}});
const t = document.getElementById('t');
lines.forEach((l, i) => {{
    const tr = document.createElement('tr'); tr.id='L'+(i+1); if(hlLines.has(i)) tr.className='hl-row';
    tr.innerHTML = `<td class="ln">${{i+1}}</td><td class="code">${{l||' '}}</td>`;
    t.appendChild(tr);
}});
const c = document.getElementById('chips');
meths.forEach(m => {{
    const s = document.createElement('span'); s.className='chip'; s.textContent=m;
    s.onclick=()=>{{ const el=document.getElementById('L'+(map[m]+1)); if(el) el.scrollIntoView({{behavior:'smooth',block:'center'}}); }};
    c.appendChild(s);
}});
if(hlLines.size>0) setTimeout(()=>{{ const el=document.getElementById('L'+(Math.min(...hlLines)+1)); if(el) el.scrollIntoView({{behavior:'smooth',block:'center'}}); }},300);
</script>
</body>
</html>"""
    st.components.v1.html(html_code, height=v_height, scrolling=True)

# ── Handle Requirement View ──────────────────────────────────────────────────
elif v_type == "req":
    file_path = Path(__file__).parent.parent / "req" / filename
    if not file_path.exists():
        st.error(f"Requirement file {filename} not found.")
        st.stop()
    
    content = file_path.read_text(encoding="utf-8", errors="replace")
    
    # Header
    c1, c2, c3 = st.columns([1, 6, 2])
    with c1: st.markdown('<a href="javascript:window.close()" class="close-btn">✕ Close</a>', unsafe_allow_html=True)
    with c2: st.markdown(f'<span class="filename">📄 {html.escape(filename)}</span>', unsafe_allow_html=True)
    with c3: st.download_button("⬇ Download", content, file_name=filename)
    
    st.markdown("---")
    kw = st.text_input("🔍 Highlight keyword", placeholder="Type a word...")
    
    disp = html.escape(content)
    if kw:
        import re
        disp = re.sub(f"({re.escape(html.escape(kw))})", r'<mark style="background:rgba(255,220,0,0.3);color:inherit;border-radius:2px;padding:0 2px;">\1</mark>', disp, flags=re.IGNORECASE)
    
    st.markdown(f'<div style="background:var(--v-surface);border:1px solid var(--v-border);border-radius:12px;padding:30px;line-height:1.8;white-space:pre-wrap;font-size:15px;color:var(--v-text);">{disp}</div>', unsafe_allow_html=True)
