import streamlit as st
import pandas as pd
from config_firebase import init_firebase
from datetime import datetime
import plotly.express as px

# Cek login
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard Statistik Pengunjung")

# Inisialisasi koneksi Firebase
db = init_firebase()
bukutamu_ref = db.collection("buku_tamu")

# Ambil data
docs = bukutamu_ref.stream()
data = []

for doc in docs:
    item = doc.to_dict()
    # Filter yang punya waktu_selesai
    if "waktu_selesai" in item and item["waktu_selesai"]:
        try:
            # Konversi waktu_selesai ke datetime jika perlu
            if isinstance(item["waktu_selesai"], str):
                item["waktu_selesai"] = datetime.fromisoformat(item["waktu_selesai"])
            elif not isinstance(item["waktu_selesai"], datetime):
                continue
            data.append(item)
        except Exception:
            continue

# Jika tidak ada data
if not data:
    st.warning("📭 Belum ada data buku tamu yang memiliki waktu selesai.")
    st.stop()

# Ubah ke DataFrame
df = pd.DataFrame(data)

# Konversi ke waktu lokal
df["waktu_selesai"] = df["waktu_selesai"].dt.tz_localize("UTC").dt.tz_convert("Asia/Jakarta")

# Tambahkan kolom tanggal dan jam
df["tanggal"] = df["waktu_selesai"].dt.date
df["jam"] = df["waktu_selesai"].dt.hour

# Pilihan rentang tanggal
min_tanggal = min(df["tanggal"])
max_tanggal = max(df["tanggal"])
tanggal_range = st.date_input("📅 Pilih rentang tanggal", (min_tanggal, max_tanggal))

# Filter berdasarkan tanggal yang dipilih
if isinstance(tanggal_range, tuple) and len(tanggal_range) == 2:
    df = df[(df["tanggal"] >= tanggal_range[0]) & (df["tanggal"] <= tanggal_range[1])]

# Statistik total
col1, col2 = st.columns(2)
col1.metric("👥 Total Pengunjung", len(df))
col2.metric("📆 Jumlah Hari", df["tanggal"].nunique())

# Grafik harian
st.subheader("📈 Grafik Kunjungan Harian")
df_harian = df.groupby("tanggal").size().reset_index(name="jumlah")
fig_harian = px.bar(df_harian, x="tanggal", y="jumlah", labels={"jumlah": "Jumlah Pengunjung"})
st.plotly_chart(fig_harian, use_container_width=True)

# Grafik jam
st.subheader("⏰ Grafik Kunjungan per Jam")
df_jam = df.groupby("jam").size().reset_index(name="jumlah")
fig_jam = px.line(df_jam, x="jam", y="jumlah", markers=True, labels={"jumlah": "Jumlah Pengunjung", "jam": "Jam"})
st.plotly_chart(fig_jam, use_container_width=True)
