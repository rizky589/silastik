import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        firebase_cred = json.loads(st.secrets["FIREBASE_JSON"])
        cred = credentials.Certificate(firebase_cred)
        firebase_admin.initialize_app(cred)
    return firestore.client()
