"""
pages/req_viewer.py
Dedicated requirement document viewer page.
URL: /req_viewer?file=UC1S1.txt
"""
import sys
import html
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

BASE_DIR = Path(__file__).parent.parent
REQ_DIR  = BASE_DIR / "req"

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Requirement Viewer — CIA System", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}

.stAppDeployButton { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stFooter"] { visibility: hidden !important; }
[data-testid="stSidebarNav"] { display: none !important; }

.stApp { background: #0D1117; }
.req-doc {
  background: #161B22; border: 1px solid #30363D; border-radius: 12px;
  padding: 28px 32px; line-height: 1.85; font-size: 15px; color: #E6EDF3;
  white-space: pre-wrap; word-wrap: break-word; font-family: 'Inter', sans-serif;
}
.req-filename { font-size: 20px; font-weight: 600; color: #4FC3F7; font-family: monospace; }
.req-badge {
  display: inline-block; background: #161B22; color: #8B949E;
  border: 1px solid #30363D; border-radius: 6px; padding: 2px 10px; font-size: 12px; margin-left: 12px;
}
mark.kw { background: rgba(255,220,80,0.25); color: #F0D060; border-radius: 3px; padding: 1px 2px; }
</style>
""", unsafe_allow_html=True)

# ── Query params ─────────────────────────────────────────────────────────────
try:
    params   = st.query_params
    filename = params.get("file", "")
except Exception:
    filename = ""

if not filename:
    st.error("No file specified. Open this viewer from the main CIA dashboard.")
    st.stop()

filename = urllib.parse.unquote(filename)
file_path = REQ_DIR / filename

# ── Header ───────────────────────────────────────────────────────────────────
col_close, col_hdr, col_dl = st.columns([1, 7, 2])
with col_close:
    st.markdown(
        '<a href="javascript:window.close()" '
        'style="color:#8B949E;text-decoration:none;font-size:14px;">✕ Close</a>',
        unsafe_allow_html=True,
    )
with col_hdr:
    st.markdown(
        f'<span class="req-filename">📄 {html.escape(filename)}</span>'
        f'<span class="req-badge">Requirement Document</span>',
        unsafe_allow_html=True,
    )

# ── Load file ────────────────────────────────────────────────────────────────
if not file_path.exists():
    st.error(f"⚠️ Requirement file **{filename}** not found in `req/` directory.")
    st.stop()

try:
    content = file_path.read_text(encoding="utf-8", errors="replace")
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

# Download button
with col_dl:
    st.download_button(
        "⬇ Download",
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
    )

# ── Keyword search ───────────────────────────────────────────────────────────
st.markdown("---")
keyword = st.text_input(
    "🔍 Highlight keyword",
    placeholder="Type a word to highlight in the document…",
    key="req_keyword",
)

# ── Render document ──────────────────────────────────────────────────────────
escaped_content = html.escape(content)

if keyword.strip():
    import re
    esc_kw = re.escape(html.escape(keyword.strip()))
    escaped_content = re.sub(
        f"({esc_kw})",
        r'<mark class="kw">\1</mark>',
        escaped_content,
        flags=re.IGNORECASE,
    )
    match_count = len(re.findall(esc_kw, html.escape(content), flags=re.IGNORECASE))
    st.caption(f"✨ {match_count} occurrence(s) of **{keyword}** highlighted")

word_count = len(content.split())
char_count = len(content)
st.markdown(
    f'<div class="req-doc">{escaped_content}</div>',
    unsafe_allow_html=True,
)

st.caption(f"📊 {word_count:,} words · {char_count:,} characters")
