import streamlit as st
from PIL import Image
import base64
from streamlit_lottie import st_lottie
import json

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

# Validasi login
if not st.session_state.get("login", False):
    st.warning("⚠️ Anda belum login.")
    st.stop()

# Fungsi load gambar base64
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Load logo dan background
logo_kiri = get_base64_image("assets/bps.png")
logo_kanan = get_base64_image("assets/se.png")
background = get_base64_image("assets/SE2026.png")

# Load animasi Lottie
def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_statistik = load_lottie_file("assets/statistik.json")

# CSS styling
st.markdown(f"""
<style>
body {{
    background-image: url("data:image/png;base64,{background}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

.logo-container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 30px;
}}

.logo {{
    height: 40px;
}}

.centered-container {{
    text-align: center;
    margin-top: 10px;
}}

h2 {{
    font-style: italic;
    font-size: 32px;
    color: #ffffff;
}}

h4 {{
    font-size: 18px;
    color: #eeeeee;
    margin-top: 10px;
}}

.footer {{
    position: fixed;
    bottom: 5px;
    width: 80%;
    text-align: center;
    font-size: 12px;
    color: black;

    
}}
</style>

<div class="logo-container">
    <img src="data:image/png;base64,{logo_kiri}" class="logo">
    <img src="data:image/png;base64,{logo_kanan}" class="logo">
</div>

<div class="centered-container">
    <h2>SANTIK</h2>
    <h4>Sistem Antrian Statistik</h4>
</div>
""", unsafe_allow_html=True)

# Lottie animation
st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
st_lottie(lottie_statistik, height=300)
st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>© 2025 BPS Kabupaten Labuhanbatu Utara</div>", unsafe_allow_html=True)
