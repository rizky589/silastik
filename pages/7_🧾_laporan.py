import streamlit as st
import pandas as pd
from datetime import datetime
from config_firebase import init_firebase
from io import BytesIO
from fpdf import FPDF
import pytz

st.set_page_config(page_title="Laporan", page_icon="🧾", layout="wide")
st.title("📊 Laporan Buku Tamu & Antrian")

# 🔌 Koneksi ke Firestore
db = init_firebase()
ref = db.collection("buku_tamu")
docs = ref.stream()

# Fungsi bantu: parse waktu dan konversi ke Asia/Jakarta
def parse_datetime(waktu):
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

# Ambil data dan parsing waktu
data = []
for doc in docs:
    d = doc.to_dict()
    waktu_masuk = parse_datetime(d.get("waktu_masuk"))
    waktu_selesai = parse_datetime(d.get("waktu_selesai"))
    if waktu_masuk and waktu_selesai:
        d["waktu_masuk"] = waktu_masuk
        d["waktu_selesai"] = waktu_selesai
        data.append(d)

df = pd.DataFrame(data)

if df.empty:
    st.warning("📭 Belum ada data pengunjung yang selesai.")
    st.stop()

# Urutkan berdasarkan waktu selesai
df = df.sort_values(by="waktu_selesai", ascending=False)

# 📅 Filter tanggal
st.subheader("📆 Filter Berdasarkan Tanggal")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Dari tanggal", df["waktu_selesai"].min().date())
with col2:
    end_date = st.date_input("Sampai tanggal", df["waktu_selesai"].max().date())

mask = (df["waktu_selesai"].dt.date >= start_date) & (df["waktu_selesai"].dt.date <= end_date)
filtered_df = df[mask]

st.success(f"Menampilkan {len(filtered_df)} data dari {start_date} s.d. {end_date}")

# 🔻 Kolom yang ditampilkan (hapus waktu_masuk, waktu_selesai, durasi)
cols_hapus = {"waktu_masuk", "waktu_selesai", "durasi_pelayanan (menit)"}
display_df = filtered_df[[col for col in filtered_df.columns if col not in cols_hapus]]

# 🧾 Tampilkan tabel
st.dataframe(display_df, use_container_width=True)

# ⬇️ Download Excel
def convert_df_to_excel(df):
    output = BytesIO()
    df_copy = df.copy()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_copy.drop(columns=cols_hapus & set(df_copy.columns), errors='ignore') \
               .to_excel(writer, index=False, sheet_name="Laporan")
    return output.getvalue()

excel_data = convert_df_to_excel(filtered_df)

st.download_button(
    label="⬇️ Download Excel",
    data=excel_data,
    file_name="laporan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# 📄 Download PDF
def generate_pdf(df):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Laporan Buku Tamu", ln=1, align="C")
    pdf.set_font("Arial", size=8)

    table_df = df.drop(columns=cols_hapus & set(df.columns), errors='ignore')
    headers = table_df.columns.tolist()
    col_width = max(270 // len(headers), 25)
    row_height = 6

    # Header
    for header in headers:
        pdf.cell(col_width, row_height, str(header)[:20], border=1)
    pdf.ln()

    # Rows
    for _, row in table_df.iterrows():
        for col in headers:
            val = row[col]
            if isinstance(val, datetime):
                val = val.strftime("%Y-%m-%d %H:%M")
            pdf.cell(col_width, row_height, str(val)[:20], border=1)
        pdf.ln()

    return pdf.output(dest="S").encode("latin1")

pdf_bytes = generate_pdf(filtered_df)

st.download_button(
    "⬇️ Download PDF",
    data=pdf_bytes,
    file_name="laporan.pdf",
    mime="application/pdf"
)
