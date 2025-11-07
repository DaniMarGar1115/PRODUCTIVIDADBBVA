import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date
from io import StringIO

# ============= Branding BBVA =============
st.set_page_config(page_title="BBVA | Portal único (Empleado + Admin)", page_icon="💼", layout="wide")

BBVA_PRIMARY = "#072146"      # Azul BBVA
BBVA_SECONDARY = "#00A1E0"    # Celeste BBVA
LOGO_URL = st.secrets.get("BBVA_LOGO_URL", os.getenv("BBVA_LOGO_URL", ""))

st.markdown(f"""
<style>
.stApp {{
    background-color: #ffffff;
}}
.bbva-header {{
    display:flex;
    align-items:center;
    gap:14px;
    margin-bottom: 10px;
}}
.bbva-title {{
    font-size: 28px;
    font-weight: 800;
    color: {BBVA_PRIMARY};
    letter-spacing: .3px;
}}
.bbva-sub {{
    color:{BBVA_SECONDARY};
    font-weight:600;
}}
.bbva-card {{
    border: 1px solid #e6e9ef;
    border-radius: 12px;
    padding: 1rem;
    background-color: #f8f9fa;
}}
</style>
""", unsafe_allow_html=True)

# Header visual
st.markdown('<div class="bbva-header">', unsafe_allow_html=True)
if LOGO_URL:
    st.image(LOGO_URL, width=110)
st.markdown('<div class="bbva-title">BBVA · Portal único <span class="bbva-sub"> Empleado + Admin </span></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
