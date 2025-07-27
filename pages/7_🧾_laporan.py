import streamlit as st
from config_firebase import init_firebase
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(page_title="📄 Laporan", page_icon="📄", layout="wide")
st.title("📄 Laporan Pengunjung / Buku Tamu")

# Inisialisasi Firebase
db = init_firebase()

# Ambil data dari Firestore
pengunjung_ref = db.collection("pengunjung")
docs = pengunjung_ref.stream()

# Konversi ke DataFrame
data = []
for doc in docs:
    d = doc.to_dict()
    data.append({
        "nama_lengkap": d.get("nama_lengkap", ""),
        "email": d.get("email", ""),
        "jenis_kelamin": d.get("jenis_kelamin", ""),
        "pendidikan": d.get("pendidikan", ""),
        "instansi": d.get("instansi", ""),
        "kontak": d.get("kontak", ""),
        "layanan": d.get("layanan", ""),
        "catatan": d.get("catatan", "")
    })

df = pd.DataFrame(data)

# Filter berdasarkan tanggal jika tersedia
st.subheader("📅 Filter Data")
tanggal_mulai = st.date_input("Tanggal Mulai")
tanggal_akhir = st.date_input("Tanggal Akhir")

# Tampilkan tabel
st.subheader("📊 Data Pengunjung")
st.dataframe(df)

# Tombol ekspor CSV
st.download_button(
    label="⬇️ Download CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name="laporan_pengunjung.csv",
    mime="text/csv"
)

# Tombol ekspor PDF
def export_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # Judul
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Laporan Pengunjung", ln=True, align="C")
    pdf.ln(10)

    # Header tabel
    pdf.set_font("Arial", 'B', 10)
    for col in df.columns:
        pdf.cell(30, 8, col, border=1)
    pdf.ln()

    # Data isi
    pdf.set_font("Arial", size=10)
    for i, row in df.iterrows():
        for item in row:
            pdf.cell(30, 8, str(item)[:30], border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

pdf_data = export_pdf(df)
st.download_button(
    label="⬇️ Download PDF",
    data=pdf_data,
    file_name="laporan_pengunjung.pdf",
    mime="application/pdf"
)
