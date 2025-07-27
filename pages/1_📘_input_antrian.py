import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
import pytz
import re
from fpdf import FPDF
import os

# Konfigurasi halaman
st.set_page_config(page_title="Input Antrian", page_icon="📝", layout="centered")
st.title("📝 Form Antrian")

# Inisialisasi koneksi Firebase
db = init_firebase()
antrian_ref = db.collection("antrian")

# Fungsi validasi nama
def validasi_nama(nama):
    return bool(re.match(r"^[a-zA-ZÀ-ÿ\s.'-]+$", nama.strip()))

# Fungsi untuk mendapatkan nomor antrian berikutnya
def get_nomor_berikutnya():
    hari_ini = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d")
    existing_docs = antrian_ref.where("tanggal", "==", hari_ini) \
                               .order_by("no", direction="DESCENDING") \
                               .limit(1).stream()
    for doc in existing_docs:
        last_no = doc.to_dict().get("no", "PST-000")
        try:
            next_no = int(last_no.split("-")[1]) + 1
            return f"PST-{str(next_no).zfill(3)}"
        except:
            return "PST-001"
    return "PST-001"

# Fungsi cetak tiket PDF
def generate_tiket_pdf(tiket):
    pdf = FPDF(orientation='P', unit='mm', format=(100, 150))
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "BPS LABURA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, "Layanan Statistik", ln=True, align="C")
    pdf.cell(0, 6, "---------------------------", ln=True, align="C")

    pdf.set_font("Arial", "B", 26)
    pdf.cell(0, 16, tiket["no"], ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Nama     : {tiket['nama']}", ln=True)
    pdf.cell(0, 6, f"PST    : {tiket['loket']}", ln=True)
    pdf.cell(0, 6, f"Layanan: {tiket['keperluan']}", ln=True)
    pdf.cell(0, 6, f"Tanggal  : {tiket['tanggal']}", ln=True)
    pdf.cell(0, 6, f"Waktu    : {tiket['waktu']}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Harap menunggu panggilan. Terima kasih.")

    filename = f"tiket_{tiket['no']}.pdf"
    pdf.output(filename)
    return filename

# --- FORM INPUT ---
with st.form("form_input"):
    nama = st.text_input(
        "Nama Lengkap",
        max_chars=50,
        placeholder="Masukkan nama lengkap...",
        help="Hanya huruf, spasi, titik, tanda kutip (') dan strip (-)"
    )
    
    keperluan = st.selectbox("Layanan", ["Statistik", "Data Mikro", "Konsultasi Statistik","Pengaduan Masyarakat", "Lainnya"])
    loket = st.selectbox("Pilih PST", ["1", "2", "3"])

    submitted = st.form_submit_button("➕ Tambah ke Antrian")

    if submitted:
        if not nama.strip():
            st.warning("❗ Nama tidak boleh kosong.")
        elif not validasi_nama(nama):
            st.warning("❗ Nama hanya boleh berisi huruf, spasi, titik, tanda kutip, dan strip.")
        else:
            try:
                no_baru = get_nomor_berikutnya()
                now = datetime.now(pytz.timezone("Asia/Jakarta"))
                data_baru = {
                    "no": no_baru,
                    "nama": nama.strip().title(),
                    "keperluan": keperluan,
                    "loket": loket,
                    "tanggal": now.strftime("%Y-%m-%d"),
                    "waktu": now.strftime("%H:%M:%S"),
                    "status": "menunggu",
                    "timestamp": now
                }

                antrian_ref.add(data_baru)
                st.success(f"✅ Antrian nomor `{no_baru}` berhasil ditambahkan. Silakan menunggu panggilan.")
                st.session_state["id_antrian"] = no_baru
                st.session_state["tiket_terakhir"] = {
                    "no": no_baru,
                    "nama": nama.strip().title(),
                    "keperluan": keperluan,
                    "loket": loket,
                    "tanggal": now.strftime("%d-%m-%Y"),
                    "waktu": now.strftime("%H:%M:%S"),
                }

            except Exception as e:
                st.error(f"❌ Gagal menambahkan ke antrian: {e}")

# --- CETAK TIKET ---
if "tiket_terakhir" in st.session_state:
    st.markdown("---")
    with st.expander("🖨️ Cetak Tiket"):
        tiket = st.session_state["tiket_terakhir"]
        st.write(f"**No Antrian:** {tiket['no']}")
        st.write(f"**Nama:** {tiket['nama']}")
        st.write(f"**Keperluan:** {tiket['keperluan']}")
        st.write(f"**Loket:** {tiket['loket']}")
        st.write(f"**Tanggal:** {tiket['tanggal']}")
        st.write(f"**Waktu:** {tiket['waktu']}")

        if st.button("📄 Download Tiket PDF"):
            filename = generate_tiket_pdf(tiket)
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Klik untuk Unduh",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
            os.remove(filename)  # Optional: bersihkan file setelah unduh
