import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import json

def is_menu_enabled(menu_name):
    with open("config_menu.json") as f:
        config = json.load(f)
    return config.get(menu_name, False)

# Cek apakah halaman aktif
if not is_menu_enabled("9_😊_survey_kepuasan"):
    st.warning("❌ Halaman ini sedang dinonaktifkan, silahkan hubungi petugas IT")
    st.stop()

st.set_page_config(page_title="Survei Kepuasan", page_icon="📝")
st.title("📝 Survei Kepuasan Layanan")

# Inisialisasi Firebase
db = init_firebase()
survey_ref = db.collection("survey_kepuasan")

# Dummy data
pengunjung_list = ["Pengunjung 1", "Pengunjung 2", "Pengunjung 3"]
petugas_list = [{"nama": "Paulina"}, {"nama": "Rizky"}]

pengunjung = st.selectbox("Nama Pengunjung", pengunjung_list)
petugas = st.selectbox("Nama Petugas Pelayanan", [p["nama"] for p in petugas_list])

st.markdown("### Penilaian Pelayanan")

# Label lengkap untuk dicetak di PDF
daftar_pertanyaan = {
    "persyaratan_mudah": "Persyaratan pelayanan mudah",
    "alur_mudah": "Prosedur/Alur pelayanan mudah",
    "jangka_waktu": "Jangka waktu pelayanan sesuai",
    "biaya_sesuai": "Biaya pelayanan sesuai",
    "produk_sesuai": "Produk pelayanan sesuai",
    "sarana_nyaman": "Sarana dan prasarana nyaman",
    "petugas_baik": "Petugas pelayanan merespon dengan baik",
    "keberadaan_mudah": "Keberadaan fasilitas pengaduan mudah diketahui",
    "diskriminasi": "Tidak ada diskriminasi pelayanan",
    "pungli": "Tidak ada pungutan liar dalam pelayanan"
}

# Input skor
penilaian = {}
for key, label in daftar_pertanyaan.items():
    penilaian[key] = st.slider(label, 1, 5, 3)

# Input saran
saran = st.text_area("Saran terkait pelayanan keseluruhan (opsional)", "")

# Hitung total nilai
total_nilai = sum(penilaian.values())

# Tombol kirim
if st.button("📩 Kirim Survei"):
    try:
        # Simpan ke Firebase
        survey_ref.add({
            "pengunjung": pengunjung,
            "petugas": petugas,
            **penilaian,
            "saran": saran,
            "total_nilai": total_nilai,
            "timestamp": datetime.now()
        })

        # Buat PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Hasil Survei Kepuasan Layanan", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.ln(5)
        pdf.cell(0, 10, f"Nama Pengunjung : {pengunjung}", ln=True)
        pdf.cell(0, 10, f"Petugas          : {petugas}", ln=True)
        pdf.cell(0, 10, f"Waktu            : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", ln=True)
        pdf.ln(5)

        for key, val in penilaian.items():
            label = daftar_pertanyaan.get(key, key).strip()
            pdf.multi_cell(0, 10, f"{label}\nNilai: {val}", align='L')
            pdf.ln(1)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total Nilai Kepuasan: {total_nilai} / 50", ln=True)

        if saran.strip():
            pdf.ln(5)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Saran: {saran}")

        # Simpan ke BytesIO
        pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
        buffer = BytesIO(pdf_bytes)

        st.success("✅ Terima kasih, survei Anda berhasil dikirim.")

        # Tombol unduh PDF
        st.download_button(
            label="⬇️ Unduh Hasil Survei (PDF)",
            data=buffer,
            file_name=f"hasil_survei_{pengunjung.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Gagal mengirim survei: {e}")
