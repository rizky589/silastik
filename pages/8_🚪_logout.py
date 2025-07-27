import streamlit as st

# Set judul halaman dan ikon
st.set_page_config(page_title="Logout", page_icon="🔒", layout="centered")

# Cek apakah user sudah login
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Anda belum login.")
    st.stop()

st.title("🔒 Logout")

st.markdown("Apakah Anda yakin ingin keluar dari aplikasi?")

# Tombol Logout
if st.button("✅ Ya, Logout"):
    # Reset semua session_state terkait user
    st.session_state["login"] = False
    st.session_state.pop("username", None)
    st.session_state.pop("role", None)
    st.session_state.page =("0_home")
    st.success("✅ Anda berhasil logout")
    st.rerun()

# Tombol batal (opsional)
if st.button("❌ Batal"):
    st.switch_page("pages/0_dashboard.py")  # Sesuaikan dengan file tujuan saat batal
