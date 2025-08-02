import streamlit as st
from config_firebase import init_firebase
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

# ----------------------------
# 🧭 Konfigurasi Tampilan App
# ----------------------------
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.markdown("<h1 style='text-align: center; color: #FFA500;'>📊 Dashboard Statistik Pengunjung</h1>", unsafe_allow_html=True)
st.markdown("---")

# ----------------------------
# 🔌 Inisialisasi Firebase & Ambil Data
# ----------------------------
db = init_firebase()
buku_tamu_ref = db.collection("buku_tamu")
docs = buku_tamu_ref.stream()

def parse_waktu(waktu):
    """Parsing datetime dengan konversi ke Asia/Jakarta"""
    if isinstance(waktu, datetime):
        dt = waktu
    elif isinstance(waktu, str):
        try:
            dt = datetime.fromisoformat(waktu)
        except:
            return None
    else:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.timezone("Asia/Jakarta"))

data = []
for doc in docs:
    item = doc.to_dict()
    waktu = item.get("waktu_selesai")
    parsed = parse_waktu(waktu)
    if parsed:
        item["waktu_selesai"] = parsed
        data.append(item)

df = pd.DataFrame(data)

if df.empty:
    st.warning("📭 Belum ada data buku tamu.")
    st.stop()

# ----------------------------
# 🧹 Praproses Data
# ----------------------------
df["tanggal"] = df["waktu_selesai"].dt.date
df["bulan"] = df["waktu_selesai"].dt.to_period("M").astype(str)
df["tahun"] = df["waktu_selesai"].dt.year

# ----------------------------
# 🔢 Statistik Umum
# ----------------------------
#st.subheader("📈 Statistik Umum")
col1, col2 = st.columns(2)
#with col1:
    #st.metric("👥 Total Pengunjung", len(df))

# ----------------------------
# 📅 Grafik Kunjungan Harian
# ----------------------------
st.subheader("Grafik Garis Kunjungan Harian")
harian = df.groupby("tanggal").size().reset_index(name="jumlah")
fig1 = px.line(
    harian,
    x="tanggal",
    y="jumlah",
    markers=True,
    title="Jumlah Pengunjung per Hari",
    template="plotly_white",
    color_discrete_sequence=["#007bff"]
)
fig1.update_layout(xaxis_title="Tanggal", yaxis_title="Jumlah")
st.plotly_chart(fig1, use_container_width=True)

# ----------------------------
# 📆 Grafik Batang Bulanan Tahun 2025
# ----------------------------
st.subheader("Grafik Batang Kunjungan Bulanan (2025)")
df_2025 = df[df["tahun"] == 2025].copy()
df_2025["bulan_angka"] = df_2025["waktu_selesai"].dt.month

bulan_lengkap = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

bulanan = (
    df_2025.groupby("bulan_angka")
    .size()
    .reindex(range(1, 13), fill_value=0)
    .reset_index()
)
bulanan.columns = ["bulan_angka", "Jumlah Pengunjung"]
bulanan["Bulan"] = bulanan["bulan_angka"].map(bulan_lengkap)

fig2 = px.bar(
    bulanan,
    x="Bulan",
    y="Jumlah Pengunjung",
    text="Jumlah Pengunjung",
    template="plotly_white",
    color_discrete_sequence=["#00FF00"]
)
fig2.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah")
st.plotly_chart(fig2, use_container_width=True)

# ----------------------------
# 🥧 Grafik Pie Jenis Layanan
# ----------------------------
if "layanan" in df.columns:
    st.subheader("Persentase Jenis Layanan")
    layanan_count = df["layanan"].value_counts().reset_index()
    layanan_count.columns = ["Layanan", "Jumlah"]
    fig3 = px.pie(
        layanan_count,
        names="Layanan",
        values="Jumlah",
        title="Layanan",
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.3
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("📌 Kolom 'layanan' tidak tersedia dalam data.")
