"""CSS global de l'application."""
import streamlit as st


def apply_styles() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',system-ui,-apple-system,sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;font-size:2.2rem!important;
   background:linear-gradient(135deg,#64b5f6,#a78bfa,#f472b6);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;}
h2,h3{font-family:'Syne',sans-serif!important;font-weight:700!important;color:#c8cad6!important;}
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:600!important;
   background:linear-gradient(135deg,#3b82f6,#7c3aed)!important;color:white!important;
   border:none!important;border-radius:8px!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;
   box-shadow:0 6px 20px rgba(99,102,241,.4)!important;}
.stSelectbox>div>div,.stTextInput>div>div>input,
.stNumberInput>div>div>input{
   background:#1a1d27!important;border:1px solid #2a2d3e!important;
   border-radius:8px!important;color:#e8eaf0!important;font-family:'Syne',sans-serif!important;}
.stSelectbox>div>div:hover,.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus{border-color:#6366f1!important;
   box-shadow:0 0 0 2px rgba(99,102,241,.2)!important;}
.sql-display{background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;
   border-radius:10px;padding:18px 22px;font-family:'JetBrains Mono',monospace;
   font-size:.85rem;color:#a5f3fc;line-height:1.8;white-space:pre-wrap;margin:8px 0;}
.tree-wrap{background:#0f111a;border:1px solid #1e2130;border-radius:12px;
   padding:18px 18px 12px;margin:10px 0;}
.t-root{display:inline-block;background:linear-gradient(135deg,#312e81,#4c1d95);color:#c4b5fd;
   padding:6px 16px;border-radius:6px;font-family:'JetBrains Mono',monospace;
   font-weight:600;font-size:.85rem;}
.t-leaf{background:#1e293b;border:1px solid #334155;border-radius:6px;
   padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.8rem;
   display:inline-block;line-height:1.8;}
[data-testid="stMetric"]{background:#13151d;border:1px solid #1e2130;
   border-radius:10px;padding:14px 18px;}
[data-testid="stMetricValue"]{color:#6366f1!important;
   font-family:'JetBrains Mono',monospace!important;font-weight:700!important;}
[data-testid="stDataFrame"]{border:1px solid #1e2130;border-radius:10px;overflow:hidden;}
[data-testid="stExpander"]{background:#13151d!important;border:1px solid #1e2130!important;
   border-radius:10px!important;}
hr{border-color:#1e2130!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0d0f14;}
::-webkit-scrollbar-thumb{background:#2a2d3e;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#6366f1;}
</style>
""", unsafe_allow_html=True)
