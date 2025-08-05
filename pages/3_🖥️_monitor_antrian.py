import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
import pytz
import pandas as pd
import locale
from streamlit_autorefresh import st_autorefresh

# 🛠️ Konfigurasi halaman
st.set_page_config(page_title="Monitor Antrian", page_icon="🎯", layout="wide")

# 🔁 Auto-refresh setiap 5 detik
st_autorefresh(interval=5000, key="auto_refresh_monitor")

# Fungsi format tanggal manual ke Bahasa Indonesia
def format_tanggal_indonesia(dt: datetime) -> str:
    hari_dict = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    bulan_dict = {
        "January": "Januari", "February": "Februari", "March": "Maret",
        "April": "April", "May": "Mei", "June": "Juni",
        "July": "Juli", "August": "Agustus", "September": "September",
        "October": "Oktober", "November": "November", "December": "Desember"
    }
    hari = hari_dict[dt.strftime("%A")]
    bulan = bulan_dict[dt.strftime("%B")]
    return f"{hari}, {dt.day} {bulan} {dt.year}"

# 🔥 Inisialisasi Firebase
db = init_firebase()
antrian_ref = db.collection("antrian")
buku_tamu_ref = db.collection("buku_tamu")

# ⏰ Waktu saat ini
zona = pytz.timezone("Asia/Jakarta")
now = datetime.now(zona)
hari_ini = now.strftime("%Y-%m-%d")
jam_sekarang = now.strftime("%H:%M:%S")
tanggal_lengkap = format_tanggal_indonesia(now).upper()

# 📰 === RUNNING TEXT ===
running_text = f"""
<div style="background-color:#003366; color:white; padding:8px; font-size:22px; border-radius:8px;">
  <marquee behavior="scroll" direction="left">
    🟢 SELAMAT DATANG DI LAYANAN ANTRIAN STATISTIK | <b>{tanggal_lengkap}</b> | <b>{jam_sekarang}</b>
  </marquee>
</div>
"""
st.markdown(running_text, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 🔎 Ambil antrian yang sedang dilayani
docs = antrian_ref.where("status", "==", "melayani") \
                  .where("tanggal", "==", hari_ini) \
                  .order_by("timestamp", direction="DESCENDING") \
                  .limit(1).stream()

antrian_terkini = None
antrian_id = None
for doc in docs:
    antrian_terkini = doc.to_dict()
    antrian_id = doc.id
    break

# 📺 Tampilan fullscreen
st.markdown("<br>", unsafe_allow_html=True)
if antrian_terkini:
    tanggal_obj = datetime.strptime(antrian_terkini.get("tanggal"), "%Y-%m-%d")
    tanggal_str = format_tanggal_indonesia(tanggal_obj).upper()

    st.markdown(f"""
        <div style='text-align: center; font-family: Arial, sans-serif;'>
            <h4 style='margin-bottom: 5px; font-size: 30px;'>PST {antrian_terkini.get("loket")}</h4>
            <h1 style='font-size: 100px; color: #007bff; margin: 10px 0;'> {antrian_terkini.get("no")} </h1>
            <h4 style='margin-bottom: 10px; font-size: 28px;'>{antrian_terkini.get("keperluan")}</h4>
            <p style='font-size: 20px;'> {tanggal_str}, PUKUL {jam_sekarang} </p>
        </div>
    """, unsafe_allow_html=True)

    # ✅ Tombol tandai selesai
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.button("✅ Tandai Selesai"):
        waktu_selesai = datetime.now(zona)

        try:
            # update status dan waktu selesai di antrian
            antrian_ref.document(antrian_id).update({
                "status": "selesai",
                "waktu_selesai": waktu_selesai.strftime("%H:%M:%S")
            })

            # update waktu selesai di buku tamu
            buku_tamu_ref.document(antrian_id).update({
                "waktu_selesai": waktu_selesai
            })

            st.success("✅ Antrian telah ditandai selesai.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Gagal menandai selesai: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align: center; color: gray;'>Tidak ada antrian yang sedang dilayani</h2>", unsafe_allow_html=True)

# 📊 Rekap semua antrian hari ini
st.markdown("---")
st.subheader("📋 Status Seluruh Antrian Hari Ini")

status_style = {
    "menunggu": "🟠 Menunggu",
    "melayani": "🟢 Melayani",
    "selesai": "🔵 Selesai"
}
status_order = ["menunggu", "melayani", "selesai"]

cols = st.columns(len(status_order))
for i, status in enumerate(status_order):
    with cols[i]:
        docs = antrian_ref.where("tanggal", "==", hari_ini) \
                          .where("status", "==", status) \
                          .order_by("timestamp", direction="DESCENDING") \
                          .stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            data.append({
                "No": d.get("no"),
                "Nama": d.get("nama"),
                "Loket": d.get("loket"),
                "Keperluan": d.get("keperluan"),
                "Jam": d.get("waktu")
            })
        st.markdown(f"### {status_style.get(status, status)}")
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.write("Tidak ada data.")
