import streamlit as st
from config_firebase import init_firebase
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Data Pengunjung", page_icon="📋", layout="wide")
st.title("Data Pengunjung per Hari dan Bulan")

# Inisialisasi Firebase
db = init_firebase()
ref = db.collection("buku_tamu")

# Ambil data dari Firebase
try:
    docs = ref.stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        # Pastikan kolom wajib ada
        if "waktu_selesai" in item and "nama_lengkap" in item:
            if isinstance(item["waktu_selesai"], datetime):
                item["waktu_selesai"] = item["waktu_selesai"].isoformat()
            data.append(item)
except Exception as e:
    st.error(f"❌ Gagal mengambil data dari Firebase: {e}")
    st.stop()

# Buat DataFrame
df = pd.DataFrame(data)

if df.empty:
    st.warning("📭 Belum ada data pengunjung yang valid.")
    st.stop()

# Format waktu
try:
    df["waktu_selesai"] = pd.to_datetime(df["waktu_selesai"], errors="coerce")
    df = df.dropna(subset=["waktu_selesai"])  # Buang baris dengan waktu tidak valid
except Exception as e:
    st.error(f"❌ Gagal memproses kolom waktu_selesai: {e}")
    st.stop()

# Tambahkan kolom tanggal, bulan, dan hari
df["tanggal"] = df["waktu_selesai"].dt.date
df["bulan"] = df["waktu_selesai"].dt.to_period("M")
df["hari"] = df["waktu_selesai"].dt.day_name()

# Filter hanya hari kerja (Senin–Jumat)
df = df[df["waktu_selesai"].dt.weekday < 5]

# Tabel Harian
st.markdown("### 📅 Tabel Data Pengunjung Harian (Hari Kerja)")
harian = df.groupby("tanggal").agg(jumlah_pengunjung=("nama_lengkap", "count")).reset_index()
st.dataframe(harian, use_container_width=True)

# Tabel Bulanan
st.markdown("### 🗓️ Tabel Data Pengunjung Bulanan")
bulanan = df.groupby("bulan").agg(jumlah_pengunjung=("nama_lengkap", "count")).reset_index()
st.dataframe(bulanan, use_container_width=True)

