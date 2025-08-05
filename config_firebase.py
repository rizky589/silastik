import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    if not firebase_admin._apps:  # ✅ Cek apakah sudah inisialisasi sebelumnya
        cred = credentials.Certificate("silastik.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()
