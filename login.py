import streamlit as st
from config_firebase import init_firebase
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
        {"username": "admin", "password": "e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7", "role": "admin"},
        {"username": "rizky", "password": "a04f0cd8fc9684c371a8989cd41953e210d06aec32e7309eb44d24985dbe9f13", "role": "operator"},
        {"username": "paulina", "password": "33f9be939550d3f1cfb6d7c97e8d6a37b7e0746a2a468c9385351b355a78da2a", "role": "operator"},
        {"username": "zul", "password": "d422f3865fd805f49c8b15506f32c944f33b522929ef2663b2eea0507a027ea8", "role": "operator"},
        {"username": "sukur", "password": "5228771e6aaeb6a35a1798974a9e593c592d03d2bdfd43e059cb56912ae88f19", "role": "operator"},
        {"username": "rozi", "password": "c37aca9e49673d08caa74efe79466600994fdab6c924ff7d8d58498a014fedde", "role": "operator"},
        {"username": "iqbal", "password": "aa97ba92ae53e2827030d96de460ab3acddf6a9de2b10588bb2b4b6fb91f5bdb", "role": "operator"},
        {"username": "alfan", "password": "051d4e79a9b23314a72291ac4a7597e5c13fff5da35a6b8c2a0f4c8f3cfcba43", "role": "operator"},
        {"username": "fandi", "password": "56e5b3bb836e54fab1db710952542c7e679d0c6b22dd5d7c6c30074000e067ad", "role": "operator"},
        {"username": "iin", "password": "993b34158d35140abdd654ebf4e32373c437aeef2518400586c4b4e08bee00c3", "role": "operator"},
        {"username": "caca", "password": "f9647984948af7fd618dbcc255fecfef838e540a94b2f26f81fde85c82ec5db9", "role": "operator"},
        {"username": "deliana", "password": "37a78d44ec4895c4b3ec976483b17f590577b8155aa98f2f9d96147ad863b760", "role": "operator"},
        {"username": "grace", "password": "1a68cb068e9bee74c03cde92796e8a5e0c9acd3aa6096864cb79380aa17856e5", "role": "operator"},
        {"username": "onita", "password": "768394d6c6853d4bcec45ca97c82988a10010f8aa6e2b19c9db390ebfe6ecea1", "role": "operator"},
        {"username": "siti", "password": "51b348eb0bd4c9ada49c9d5cc9517bd928b2d3e562b798c983e8281179a1c98d", "role": "operator"},
        {"username": "emmy", "password": "f91b9e0b2b6ea27a8b9b204778f56540943165f3366b9abfb4db429ceb56ff8e", "role": "operator"},
    ]
    for user in daftar_user:
        exists = users_ref.document(user["username"]).get().exists
        if not exists:
            users_ref.document(user["username"]).set({
                "username": user["username"],
                "password": user["password"],
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
