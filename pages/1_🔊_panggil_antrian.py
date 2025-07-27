import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
import pytz
from gtts import gTTS
import os
from playsound import playsound
import shutil

# Konfigurasi halaman
st.set_page_config(page_title="Panggil Antrian", page_icon="🔁", layout="centered")
st.title("🔁 Panggil Antrian")

# Cek login
if "login" not in st.session_state or not st.session_state["login"]:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

# Inisialisasi Firebase
@st.cache_resource
def get_db():
    return init_firebase()

db = get_db()
antrian_ref = db.collection("antrian")
buku_tamu_ref = db.collection("buku_tamu")

# Zona waktu
tz = pytz.timezone("Asia/Jakarta")
now = datetime.now(tz)
tanggal = now.strftime("%Y-%m-%d")

# Fungsi TTS
def tts(text):
    try:
        os.makedirs(".temp_audio", exist_ok=True)
        bell_sound = "assets/bell.mp3"
        if os.path.exists(bell_sound):
            playsound(bell_sound)
        tts = gTTS(text=text, lang='id')
        filename = ".temp_audio/antrian.mp3"
        tts.save(filename)
        playsound(filename)
    except Exception as e:
        st.error(f"❌ Gagal memutar suara: {e}")
    finally:
        shutil.rmtree(".temp_audio", ignore_errors=True)

# Ambil antrian dengan status 'menunggu' untuk hari ini
next_antrian = None
docs = antrian_ref.where("tanggal", "==", tanggal).where("status", "==", "menunggu") \
                  .order_by("waktu").limit(1).stream()

for doc in docs:
    next_antrian = doc
    break

if next_antrian:
    data = next_antrian.to_dict()
    st.info(f"📢 Antrian Selanjutnya: **{data['no']} - {data['nama']}** | PST: {data['loket']}")
    st.write(f"📝 Layanan: {data['keperluan']}")

    col1, col2, col3 = st.columns(3)

    # PANGGIL
    if col1.button("🔔 Panggil Berikutnya"):
        try:
            now = datetime.now(tz)

            # Update status di koleksi antrian
            antrian_ref.document(next_antrian.id).update({
                "status": "melayani",
                "waktu": now.strftime("%H:%M:%S"),
                "timestamp": now
            })

            # Tambahkan ke buku tamu jika belum ada
            if not buku_tamu_ref.document(next_antrian.id).get().exists:
                buku_tamu_ref.document(next_antrian.id).set({
                    "id_antrian": next_antrian.id,
                    "nama_lengkap": data.get("nama"),
                    "jenis_kelamin": data.get("jenis_kelamin", ""),
                    "email": data.get("email", ""),
                    "pendidikan": data.get("pendidikan", ""),
                    "instansi": data.get("instansi", ""),
                    "kontak": data.get("kontak", ""),
                    "layanan": data.get("keperluan"),
                    "catatan": data.get("catatan", ""),
                    "waktu_masuk": now,
                    "waktu_selesai": None
                })

            st.session_state["id_antrian"] = next_antrian.id

            tts(f"Nomor antrian {data['no']}. Atas nama {data['nama']}. Silakan ke P-S-T {data['loket']}.")
            st.success(f"✅ Antrian {data['no']} dipanggil.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Gagal memanggil antrian: {e}")

    # SKIP
    if col2.button("⏭ Skip"):
        antrian_ref.document(next_antrian.id).update({"status": "dilewati"})
        st.warning(f"⏩ Antrian {data['no']} dilewati.")
        st.rerun()

    # PAUSE
    if col3.button("⏸ Pause"):
        antrian_ref.document(next_antrian.id).update({"status": "pause"})
        st.warning(f"⏸ Antrian {data['no']} di-pause.")
        st.rerun()

else:
    st.success("✅ Tidak ada antrian menunggu saat ini.")

# --- RESET ANTRIAN HARI INI
st.markdown("---")
if st.button("🗑️ Reset Antrian Hari Ini"):
    try:
        docs_today = antrian_ref.where("tanggal", "==", tanggal).stream()
        deleted = 0
        for doc in docs_today:
            antrian_ref.document(doc.id).delete()
            deleted += 1
        st.success(f"✅ {deleted} antrian berhasil dihapus.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Gagal mereset antrian: {e}")
