import streamlit as st
import hashlib
from config_firebase import init_firebase
from google.cloud.firestore import Client

# Konfigurasi halaman
st.set_page_config(page_title="Login Admin / Operator", page_icon="🔐", layout="centered")
st.title("🔐 Login Petugas PST")

# Inisialisasi koneksi Firebase
db: Client = init_firebase()
users_ref = db.collection("users")

# Fungsi hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Fungsi untuk menambahkan akun default
def tambah_user_default():
    daftar_user = [
        {"username": "admin", "password": "Admin@123", "role": "admin"},
        {"username": "rizky", "password": "rizky@123", "role": "operator"},
        {"username": "edi", "password": "edi@123", "role": "operator"},
        {"username": "zul", "password": "zul@123", "role": "operator"},
        {"username": "hendri", "password": "hendri@123", "role": "operator"},
    ]
    for user in daftar_user:
        exists = users_ref.document(user["username"]).get().exists
        if not exists:
            users_ref.document(user["username"]).set({
                "username": user["username"],
                "password": hash_password(user["password"]),
                "role": user["role"]
            })

# Menambahkan user default hanya saat pertama
tambah_user_default()

# Inisialisasi session
if "login" not in st.session_state:
    st.session_state.login = False

# Jika sudah login, arahkan ke halaman utama
if st.session_state.login:
    st.switch_page("pages/0_🏠_home.py")

# Form Login
with st.form("form_login"):
    username = st.text_input("Username", placeholder="Masukkan username")
    password = st.text_input("Password", type="password", placeholder="Masukkan password")
    login_submit = st.form_submit_button("Login")

if login_submit:
    if username and password:
        hashed_pw = hash_password(password)
        docs = users_ref.where("username", "==", username).where("password", "==", hashed_pw).limit(1).stream()
        user_data = next(docs, None)

        if user_data and user_data.exists:
            user_dict = user_data.to_dict()
            st.session_state.login = True
            st.session_state.username = user_dict["username"]
            st.session_state.role = user_dict.get("role", "operator")
            st.session_state.nama_operator = user_dict["username"]
            st.success(f"✅ Login berhasil sebagai {user_dict['username']} ({st.session_state.role})")
            st.switch_page("pages/0_🏠_home.py")
        else:
            st.error("❌ Username atau password salah.")
    else:
        st.warning("⚠️ Harap isi username dan password.")
