import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
import re

# Konfigurasi halaman
st.set_page_config(page_title="Buku Tamu", page_icon="📒")
st.title("📋 Buku Tamu")

# Cek login
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

# Inisialisasi Firebase
db = init_firebase()
buku_tamu_ref = db.collection("buku_tamu")
antrian_ref = db.collection("antrian")

# Fungsi validasi email
def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Form input
with st.form("form_buku_tamu", clear_on_submit=True):
    nama = st.text_input("Nama Lengkap").strip()
    email = st.text_input("Email").strip()
    jenis_kelamin = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    pendidikan = st.selectbox("Pendidikan Tertinggi", ["SMA", "D1/D2/D3", "S1", "S2", "S3"])
    instansi = st.text_input("Asal Instansi").strip()
    kontak = st.text_input("Nomor Telepon / WA (maks. 12 digit angka)", max_chars=15).strip()
    layanan = st.selectbox("Jenis Layanan", [
        "Konsultasi Statistik",
        "Perpustakaan",
        "Akses Produk Statistik pada Website",
        "Data Mikro",
        "Pengaduan Masyarakat",
        "Lainnya"
    ])
    catatan = st.text_area("Catatan (opsional)").strip()
    submit = st.form_submit_button("💾 Simpan")

# Proses setelah submit
if submit:
    kontak_bersih = ''.join(filter(str.isdigit, kontak))

    if not all([nama, email, jenis_kelamin, pendidikan, instansi, kontak_bersih, layanan]):
        st.warning("⚠️ Semua field wajib diisi.")
    elif not valid_email(email):
        st.error("❌ Format email tidak valid.")
    elif not (10 <= len(kontak_bersih) <= 12):
        st.error("❌ Nomor WA harus angka dan terdiri dari 10–12 digit.")
    else:
        now = datetime.now()
        data = {
            "nama_lengkap": nama,
            "email": email,
            "jenis_kelamin": jenis_kelamin,
            "pendidikan": pendidikan,
            "instansi": instansi,
            "kontak": kontak_bersih,
            "layanan": layanan,
            "catatan": catatan,
            "waktu_masuk": now.strftime("%Y-%m-%d %H:%M:%S"),
            "waktu_selesai": now,
            "status": "selesai"
        }

        try:
            buku_tamu_ref.add(data)

            # 🔁 Update status antrian jika tersedia
            id_antrian = st.session_state.get("id_antrian")
            if id_antrian:
                # Pastikan dokumen antrian ada sebelum update
                antrian_doc = antrian_ref.document(id_antrian).get()
                if antrian_doc.exists:
                    antrian_ref.document(id_antrian).update({
                        "status": "selesai",
                        "waktu_selesai": now.strftime("%H:%M:%S"),
                        "timestamp_selesai": now
                    })
                    st.success("✅ Data berhasil disimpan!")
                    
                else:
                    st.warning("⚠️ ID antrian tidak ditemukan di database.")
            else:
                st.warning("⚠️ Data tamu disimpan, tapi tidak terhubung ke antrian.")

            st.rerun()

        except Exception as e:
            st.error(f"❌ Gagal menyimpan data: {e}")
