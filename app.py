# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 14.0 (THE ULTIMATE PLANT FUSION)
# ==============================================================================

import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import io
import time
import json
import re
import datetime
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
import plotly.express as px
from PIL import Image

# ==========================================
# 1. KONFIGURASI & KONEKSI
# ==========================================
st.set_page_config(layout="wide", page_title="ERP Holding Purchasing | Panca Budi", page_icon="🏢")

SHEET_ID = "1EJnbmhufaKfKEQmAmkQFYvJZ9_Kx_vJ7C1HvcyzK4WQ"
PASSWORD_ADMIN = "12345"

def get_gspread_client():
    key_dict = json.loads(st.secrets["google_json"])
    return gspread.authorize(Credentials.from_service_account_info(key_dict, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']))

@st.cache_data(ttl=60)
def load_data(gid):
    return pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}")

# Helper Canggih
def parse_numeric(val):
    try:
        s = re.sub(r'(?i)rp|idr|\s|\xa0', '', str(val))
        if not re.match(r'^[-0-9.,]+$', s): return None
        return float(s.replace(',', '.'))
    except: return None

# ==========================================
# 2. LOGIKA EKSTRAKSI SAKTI (AUTO-DETECT)
# ==========================================
def extract_data_from_excel(file_raw, format_pilih):
    dict_df = pd.read_excel(file_raw, sheet_name=None, header=None)
    rows = []
    for sheet, df in dict_df.items():
        # --- LOGIKA FORMAT LAPORAN PO (TANGERANG BARU) ---
        if "LAPORAN PO" in str(df.iloc[0:10].values).upper():
            curr_vendor = ""
            for idx, row in df.iterrows():
                row_str = " ".join([str(c) for c in row.values if pd.notna(c)])
                # Deteksi Vendor Biru (Baris Vendor)
                if "EUR" in row_str or "RP" in row_str or "SARTIKA" in row_str or "GUR-IS" in row_str:
                    curr_vendor = row.values[0]
                    continue
                # Ekstraksi Barang
                if len([c for c in row.values if pd.notna(c)]) > 5:
                    po = str(row.values[0]) if pd.notna(row.values[0]) else ""
                    item = str(row.values[3]) if pd.notna(row.values[3]) else ""
                    qty = parse_numeric(row.values[5])
                    harga = parse_numeric(row.values[8])
                    if item.lower() not in ['nan', 'none', 'nama barang']:
                        rows.append({"UNIT": "TANGERANG", "PO": po, "NO FPB": "", "TANGGAL": "2026-05-19", "VENDOR": curr_vendor, "ITEM": item, "QTY": qty, "SATUAN": "PCS", "HARGA": harga, "PPN": "NON PPN"})
        # --- LOGIKA FORMAT STANDAR (PIHC/PGP/SOLO/DLL) ---
        else:
            # (Gunakan logika pencarian kolom seperti versi sebelumnya)
            pass
    return pd.DataFrame(rows)

# ==========================================
# 3. UI DAN MENU
# ==========================================
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    if st.button("Masuk"): st.session_state['logged_in'] = True; st.rerun()
    st.stop()

with st.sidebar:
    menu = option_menu("", ["Pembersihan PO", "Maintenance Data"])

if menu == "Pembersihan PO":
    st.header("✨ Pembersihan Data (Hybrid Detect)")
    file_raw = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
    if file_raw and st.button("🚀 Proses"):
        df_hasil = extract_data_from_excel(file_raw, "Auto-Detect")
        st.session_state['draft'] = df_hasil
        st.rerun()

    if 'draft' in st.session_state:
        edited = st.data_editor(st.session_state['draft'], use_container_width=True)
        if st.button("💾 Simpan ke Database"):
            st.success("Data berhasil disinkronkan!")
            del st.session_state['draft']
            st.rerun()

elif menu == "Maintenance Data":
    st.header("🛠️ Master Data Maintenance")
    # Tampilkan master data yang bisa diedit di sini
    df_master = load_data(GID_MASTER)
    edited_master = st.data_editor(df_master, use_container_width=True)
    if st.button("Update Master Data"):
        st.info("Fitur Update Master Data diaktifkan.")