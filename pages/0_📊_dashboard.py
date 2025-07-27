import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# Cek login
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

# Set judul halaman
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard Statistik Pengunjung")

# Koneksi ke Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    return client.open("silastik_buku_tamu").worksheet("pengunjung")

# Ambil data dari sheet
sheet = get_sheet()
data = sheet.get_all_records()

# Buat DataFrame
df = pd.DataFrame(data)

if df.empty:
    st.info("Belum ada data pengunjung yang tersedia.")
    st.stop()

# Pastikan kolom datetime dikonversi dengan aman
for col in ["waktu_masuk", "waktu_selesai"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")
    df[col] = df[col].dt.tz_localize("UTC").dt.tz_convert("Asia/Jakarta")

# Tambahkan kolom tanggal saja
df["tanggal"] = df["waktu_masuk"].dt.date
df["bulan"] = df["waktu_masuk"].dt.to_period("M").astype(str)

# =========================
# Statistik Ringkas
# =========================
st.subheader("🔢 Statistik Ringkas")

col1, col2 = st.columns(2)
with col1:
    jumlah_hari_ini = df[df["tanggal"] == datetime.now().date()].shape[0]
    st.metric("👥 Jumlah Hari Ini", jumlah_hari_ini)

with col2:
    bulan_ini = datetime.now().strftime("%Y-%m")
    jumlah_bulan_ini = df[df["bulan"] == bulan_ini].shape[0]
    st.metric("📆 Jumlah Bulan Ini", jumlah_bulan_ini)

# =========================
# Grafik Harian
# =========================
st.subheader("📈 Grafik Kunjungan Harian")

kunjungan_harian = df.groupby("tanggal").size().reset_index(name="jumlah")
fig_harian = px.bar(kunjungan_harian, x="tanggal", y="jumlah", labels={"jumlah": "Jumlah Kunjungan"}, title="Kunjungan Harian", color="jumlah")
st.plotly_chart(fig_harian, use_container_width=True)

# =========================
# Grafik Bulanan
# =========================
st.subheader("📆 Grafik Kunjungan Bulanan")

kunjungan_bulanan = df.groupby("bulan").size().reset_index(name="jumlah")
fig_bulanan = px.bar(kunjungan_bulanan, x="bulan", y="jumlah", labels={"jumlah": "Jumlah Kunjungan"}, title="Kunjungan Bulanan", color="jumlah")
st.plotly_chart(fig_bulanan, use_container_width=True)

# =========================
# Tabel Data Terbaru
# =========================
st.subheader("📋 Daftar Pengunjung Terbaru")
df_tampil = df[["nama", "keperluan", "waktu_masuk", "waktu_selesai"]].sort_values(by="waktu_masuk", ascending=False)
df_tampil["waktu_masuk"] = df_tampil["waktu_masuk"].dt.strftime("%d-%m-%Y %H:%M:%S")
df_tampil["waktu_selesai"] = df_tampil["waktu_selesai"].dt.strftime("%d-%m-%Y %H:%M:%S")
st.dataframe(df_tampil, use_container_width=True)
