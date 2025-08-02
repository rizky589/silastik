import streamlit as st
from config_firebase import init_firebase
from datetime import datetime, time
import pytz
import pandas as pd
from PIL import Image
import os
from fpdf import FPDF
import tempfile

# Konfigurasi halaman
st.set_page_config(page_title="Presensi Pegawai", page_icon="🕒")
st.title("🕒 Presensi Harian Petugas PST")

# Inisialisasi Firebase
db = init_firebase()
presensi_ref = db.collection("presensi")

# Waktu sekarang
wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib)
today = now.date()
jam_sekarang = now.time()

# Input nama pengguna (jika belum login)
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

username = st.session_state["username"]

# Direktori penyimpanan foto
foto_dir = "presensi_foto"
os.makedirs(foto_dir, exist_ok=True)

# SHIFT WAKTU TETAP
shifts = {
    "Pagi": (time(8, 0), time(12, 0)),
    "Siang": (time(13, 0), time(16, 30))
}

# Presensi
st.subheader("📍 Presensi Hari Ini")
st.caption(f"Tanggal: {today} | Jam: {now.strftime('%H:%M:%S')}")

for shift, (start, end) in shifts.items():
    st.markdown(f"**Shift {shift}**: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")

    # Cek apakah sudah absen shift ini
    sudah_absen = presensi_ref.where("user", "==", username).where("tanggal", "==", str(today)).where("shift", "==", shift).limit(1).stream()
    if any(sudah_absen):
        st.success(f"✅ Sudah presensi shift {shift}")
        continue

    # Validasi waktu shift
    if start <= jam_sekarang <= end:
        st.info(f"Silakan ambil foto sebagai bukti kehadiran untuk shift {shift}.")
        foto = st.camera_input(f"📸 Ambil Foto Shift {shift}")

        if foto and st.button(f"✅ Konfirmasi Presensi Shift {shift}", key=shift):
            # Simpan presensi ke Firebase
            presensi_ref.add({
                "user": username,
                "tanggal": str(today),
                "jam": now.strftime("%H:%M"),
                "shift": shift,
                "status": "Hadir",
                "timestamp": now,
                "operator": st.session_state.get("username", "Tidak diketahui")
                })
            
            # Simpan foto ke folder
            img = Image.open(foto)
            foto_path = os.path.join(foto_dir, f"{username}_{shift}_{today}.jpg")
            img.save(foto_path)

            st.success(f"Presensi shift {shift} berhasil dicatat dan foto tersimpan.")
    else:
        st.info(f"⏳ Presensi shift {shift} hanya dapat dilakukan antara {start.strftime('%H:%M')}–{end.strftime('%H:%M')}")

# Riwayat presensi
st.subheader("📜 Riwayat Presensi")
data_presensi = presensi_ref.where("user", "==", username).order_by("timestamp", direction="DESCENDING").stream()
records = []
for p in data_presensi:
    d = p.to_dict()
    records.append([
        d.get("tanggal", ""),
        d.get("shift", ""),
        d.get("jam", ""),
        d.get("status", ""),
        d.get("operator", "Tidak diketahui")
    ])

if records:
    df = pd.DataFrame(records, columns=["Tanggal", "Shift", "Jam", "Status", "Operator"])
    st.dataframe(df, use_container_width=True)

    # 🔽 Generate PDF dari DataFrame
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, f"Rekap Presensi - {username}", ln=True, align="C")
            self.set_font("Arial", "", 10)
            self.cell(0, 10, f"Diperbarui: {now.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
            self.ln(5)

        def table(self, data):
            self.set_font("Arial", "B", 10)
            col_widths = [40, 30, 30, 30,40]
            headers = ["Tanggal", "Shift", "Jam", "Status", "Operator"]
            for i, header in enumerate(headers):
                self.cell(col_widths[i], 10, header, border=1, align="C")
            self.ln()
            self.set_font("Arial", "", 10)
            for row in data:
                for i, item in enumerate(row):
                    self.cell(col_widths[i], 10, str(item), border=1, align="C")
                self.ln()

    pdf = PDF()
    pdf.add_page()
    pdf.table(df.values.tolist())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        st.download_button(
            label="📥 Unduh Rekap PDF",
            data=open(tmp_pdf.name, "rb").read(),
            file_name=f"Rekap_Presensi_{username}.pdf",
            mime="application/pdf"
        )

                # 🔽 Generate Rekap Semua Operator untuk bulan ini
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])  # pastikan kolom tanggal berupa datetime
        bulan_ini = now.month
        tahun_ini = now.year
                # Pilih bulan dan tahun
        bulan_dict = {
            "Januari": 1,
            "Februari": 2,
            "Maret": 3,
            "April": 4,
            "Mei": 5,
            "Juni": 6,
            "Juli": 7,
            "Agustus": 8,
            "September": 9,
            "Oktober": 10,
            "November": 11,
            "Desember": 12,
        }

        st.subheader("📅 Pilih Bulan & Tahun Rekap Presensi")
        selected_bulan = st.selectbox("Pilih Bulan", list(bulan_dict.keys()), index=now.month - 1)
        selected_tahun = st.number_input("Pilih Tahun", min_value=2020, max_value=2100, value=now.year, step=1)

        bulan_ini = bulan_dict[selected_bulan]
        tahun_ini = selected_tahun


        df_bulanan = df[(df['Tanggal'].dt.month == bulan_ini) & (df['Tanggal'].dt.year == tahun_ini)]


        if not df_bulanan.empty:
            class PDFAll(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 14)
                    self.cell(0, 10, f"Rekap Presensi Semua Operator - {now.strftime('%B %Y')}", ln=True, align="C")
                    self.set_font("Arial", "", 10)
                    self.cell(0, 10, f"Diperbarui: {now.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
                    self.ln(5)

                def table(self, data):
                    self.set_font("Arial", "B", 10)
                    headers = ["Tanggal", "Shift", "Jam", "Status", "Operator"]
                    col_widths = [30, 25, 25, 25, 50]
                    for i, header in enumerate(headers):
                        self.cell(col_widths[i], 10, header, border=1, align="C")
                    self.ln()
                    self.set_font("Arial", "", 10)
                    for row in data:
                        for i, item in enumerate(row):
                            self.cell(col_widths[i], 10, str(item), border=1, align="C")
                        self.ln()

            pdf_all = PDFAll()
            pdf_all.add_page()
            pdf_all.table(df_bulanan[["Tanggal", "Shift", "Jam", "Status", "Operator"]].values.tolist())

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_all_pdf:
                pdf_all.output(tmp_all_pdf.name)
                st.download_button(
                    label="📥 Unduh Rekap Semua Operator (Bulan Ini)",
                    data=open(tmp_all_pdf.name, "rb").read(),
                    file_name=f"Rekap_Presensi_Bulan_{now.strftime('%Y_%m')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Belum ada data presensi semua operator untuk bulan ini.")
