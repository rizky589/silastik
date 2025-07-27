import streamlit as st
from config_firebase import init_firebase
from datetime import datetime
import pandas as pd
import io
from fpdf import FPDF

# Inisialisasi koneksi Firebase
db = init_firebase()
buku_tamu_ref = db.collection("buku_tamu")

# Konfigurasi halaman
st.set_page_config(page_title="📄 Laporan", page_icon="📄", layout="wide")
st.title("📄 Laporan Buku Tamu")

# Fungsi mengambil data dari Firestore
@st.cache_data(ttl=600)
def get_data():
    docs = buku_tamu_ref.stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        data.append(item)
    return pd.DataFrame(data)

# Fungsi filter data berdasarkan tanggal
def filter_data(df, start_date, end_date):
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    return df[(df['tanggal'] >= pd.to_datetime(start_date)) & (df['tanggal'] <= pd.to_datetime(end_date))]

# Input tanggal
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Tanggal Mulai", value=datetime.now().replace(day=1))
with col2:
    end_date = st.date_input("Tanggal Selesai", value=datetime.now())

# Ambil dan filter data
df = get_data()
filtered_df = filter_data(df, start_date, end_date)

# Hapus kolom waktu_masuk dan waktu_selesai jika ada
for col in ['waktu_masuk', 'waktu_selesai']:
    if col in filtered_df.columns:
        filtered_df.drop(columns=[col], inplace=True)

st.dataframe(filtered_df, use_container_width=True)

# Tombol untuk ekspor CSV
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name='laporan_buku_tamu.csv',
    mime='text/csv'
)

# Tombol untuk ekspor PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Laporan Buku Tamu', ln=True, align='C')

    def table(self, data):
        self.set_font('Arial', '', 10)
        col_widths = [35, 35, 30, 30, 50]
        headers = ['Tanggal', 'Nama', 'Keperluan', 'Loket', 'Keterangan']
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1)
        self.ln()
        for index, row in data.iterrows():
            self.cell(col_widths[0], 10, str(row.get('tanggal', '')), 1)
            self.cell(col_widths[1], 10, str(row.get('nama', '')), 1)
            self.cell(col_widths[2], 10, str(row.get('keperluan', '')), 1)
            self.cell(col_widths[3], 10, str(row.get('loket', '')), 1)
            self.cell(col_widths[4], 10, str(row.get('keterangan', '')), 1)
            self.ln()

if st.button("📄 Download PDF"):
    pdf = PDF()
    pdf.add_page()
    pdf.table(filtered_df)
    buffer = io.BytesIO()
    pdf.output(buffer)
    st.download_button(
        label="📥 Simpan PDF",
        data=buffer.getvalue(),
        file_name="laporan_buku_tamu.pdf",
        mime="application/pdf"
    )
