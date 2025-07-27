import streamlit as st
import pandas as pd
from datetime import datetime
from config_firebase import init_firebase
from io import BytesIO
from fpdf import FPDF
import pytz

# Konfigurasi halaman
st.set_page_config(page_title="Laporan", page_icon="🧾", layout="wide")
st.title("📄 Halaman Laporan Buku Tamu")

# 🔌 Koneksi ke Firestore
db = init_firebase()
ref = db.collection("buku_tamu")
docs = ref.stream()

# Fungsi bantu untuk parsing waktu + konversi zona
def parse_datetime_to_jakarta(waktu):
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

# Ambil data dari Firestore
data = []
for doc in docs:
    d = doc.to_dict()
    d["id"] = doc.id

    d["waktu_selesai"] = parse_datetime_to_jakarta(d.get("waktu_selesai"))
    d["waktu_masuk"] = parse_datetime_to_jakarta(d.get("waktu_masuk"))

    data.append(d)

df = pd.DataFrame(data)

if df.empty:
    st.warning("📭 Belum ada data pengunjung.")
    st.stop()

# Hapus data yang tidak memiliki waktu_selesai
df = df.dropna(subset=["waktu_selesai"])
df = df.sort_values(by="waktu_selesai", ascending=False)

# 📅 Filter Tanggal
st.subheader("📆 Filter Berdasarkan Tanggal")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari tanggal", df["waktu_selesai"].min().date())
with col2:
    end_date = st.date_input("Sampai tanggal", df["waktu_selesai"].max().date())

mask = (df["waktu_selesai"].dt.date >= start_date) & (df["waktu_selesai"].dt.date <= end_date)
filtered_df = df.loc[mask]

st.success(f"✅ Menampilkan {len(filtered_df)} data dari {start_date} s.d. {end_date}")

# Atur urutan kolom
desired_order = [
    "id_antrian", "nama_lengkap", "jenis_kelamin", "email", "pendidikan",
    "instansi", "kontak", "layanan", "waktu_masuk", "waktu_selesai", "catatan"
]
existing_cols = [col for col in desired_order if col in filtered_df.columns]
filtered_df = filtered_df[existing_cols + [col for col in filtered_df.columns if col not in existing_cols]]

# 🌐 Tampilkan Data
st.dataframe(filtered_df, use_container_width=True)

# 🔽 Download sebagai Excel
def convert_df_to_excel(df):
    output = BytesIO()
    df_excel = df.copy()
    # Hapus timezone sebelum export
    for col in ["waktu_selesai", "waktu_masuk"]:
        if col in df_excel.columns:
            df_excel[col] = df_excel[col].dt.tz_localize(None)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_excel.to_excel(writer, index=False, sheet_name="Laporan")
    return output.getvalue()

excel_data = convert_df_to_excel(filtered_df)

st.download_button(
    label="⬇️ Download Excel",
    data=excel_data,
    file_name="laporan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# 📄 Download sebagai PDF
def generate_full_pdf(dataframe):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Laporan Buku Tamu Lengkap", ln=1, align="C")
    pdf.set_font("Arial", size=8)

    col_width = 40
    row_height = 6

    headers = dataframe.columns.tolist()
    for header in headers:
        pdf.cell(col_width, row_height, str(header)[:15], border=1)
    pdf.ln()

    for _, row in dataframe.iterrows():
        for col in headers:
            value = row[col]
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M")
            pdf.cell(col_width, row_height, str(value)[:15], border=1)
        pdf.ln()

    return pdf.output(dest="S").encode("latin1")

pdf_bytes = generate_full_pdf(filtered_df)

st.download_button(
    label="⬇️ Download PDF",
    data=pdf_bytes,
    file_name="laporan.pdf",
    mime="application/pdf"
)
