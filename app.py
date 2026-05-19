# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 13.5 (ULTIMATE FULL VERSION - Tangerang Hybrid PO & Vendor Memory Conqueror)
# Fitur: Auto-Fill PCS, Unlocked Master Editor, Split PO & FPB, Dashboard, Catalog
# ==============================================================================

import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import io
import time
import json
import re
import urllib.parse
import datetime
import gspread
import base64
from PIL import Image
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN & TAMPILAN ERP
# ==========================================
st.set_page_config(layout="wide", page_title="ERP Holding Purchasing | Panca Budi", page_icon="🏢")

st.markdown("""
    <style>
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* --- 🛡️ ARMOR ANTI-DARK MODE (FORCE LIGHT UI DI SEMUA DEVICE) --- */
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
    }
    
    /* Paksa Semua Teks Standar Menjadi Gelap */
    [data-testid="stMarkdownContainer"] > p, [data-testid="stText"], label, .stSelectbox label {
        color: #334155 !important;
    }
    h1, h2, h3, h4, h5, h6 { 
        color: #0F172A !important; 
    }
    
    /* Paksa Input Box & Dropdown Menjadi Terang dengan Teks Gelap */
    div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Paksa Pilihan Dropdown agar tulisannya tidak hilang */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    ul[data-baseweb="menu"] li {
        color: #0F172A !important;
    }
    
    /* Paksa Teks di Expander Guide Book */
    div[data-testid="stExpander"] summary p {
        color: #047857 !important;
        font-weight: 700 !important;
    }
    
    /* --- FITUR STEALTH & MENGHILANGKAN BLANK SPACE BAWAH --- */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    footer { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    
    /* Widget Cards */
    .stMetric { 
        padding: 24px; 
        border-radius: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        background-color: transparent !important;
        transition: transform 0.2s ease-in-out;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    
    /* COMPACT LUXURY BUTTONS */
    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        padding: 12px 0 !important; 
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #064E3B 0%, #047857 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(4, 120, 87, 0.2) !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 15px rgba(4, 120, 87, 0.3) !important;
    }
    div[data-testid="stButton"] button[kind="primary"] p {
        color: #FFFFFF !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #334155 !important;
        border: 2px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #CBD5E1 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 15px rgba(0,0,0,0.05) !important;
    }
    
    /* COMPACT LUXURY INPUT FIELD */
    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        border: 2px solid #E2E8F0 !important;
        padding: 12px !important; 
        font-size: 14px !important;
        text-align: center !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #047857 !important;
        box-shadow: 0 0 0 4px rgba(4, 120, 87, 0.15) !important;
    }
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SISTEM KONEKSI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1EJnbmhufaKfKEQmAmkQFYvJZ9_Kx_vJ7C1HvcyzK4WQ"
GID_MASTER = "0"              
GID_VENDOR = "168217676"      
GID_DASHBOARD = "1693047728"  
GID_SANDBOX = "1722600044"    

PASSWORD_ADMIN = "12345"

def get_gspread_client():
    key_dict = json.loads(st.secrets["google_json"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=120) 
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    return pd.read_csv(url)

@st.cache_data(ttl=120)
def get_sync_time():
    tz_wib = datetime.timezone(datetime.timedelta(hours=7))
    now = datetime.datetime.now(tz_wib)
    bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{now.day} {bulan[now.month]} {now.year}, {now.strftime('%H:%M')} WIB"

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def format_rupiah(angka):
    try:
        val = str(angka).strip()
        if val.upper() in ['NAN', 'NONE', '']: return "Rp 0"
        if val.endswith('.0'): val = val[:-2]
        if val.endswith(',00'): val = val[:-3]
        num_str = re.sub(r'[^0-9]', '', val)
        if num_str: return f"Rp {int(num_str):,}".replace(',', '.')
        return val
    except: return "Rp 0"

def parse_harga(x):
    try:
        s = str(x).upper().replace('RP', '').replace('IDR', '').strip()
        if s.endswith('.0'): s = s[:-2]
        if s.endswith(',00'): s = s[:-3]
        s = re.sub(r'[^0-9]', '', s)
        return float(s) if s else 0.0
    except: return 0.0

def convert_to_standard_date(date_str):
    try:
        s = str(date_str).strip().upper()
        if not s or s in ['NAN', 'NONE', '-']: return datetime.datetime(2000, 1, 1) 
        if re.match(r'^\d{4}-\d{2}-\d{2}', s): return pd.to_datetime(s.split(' ')[0])
        
        months_map = {
            'JANUARI': 1, 'FEBRUARI': 2, 'PEBRUARI': 2, 'MARET': 3, 'APRIL': 4, 'MEI': 5, 
            'JUNI': 6, 'JULI': 7, 'AGUSTUS': 8, 'SEPTEMBER': 9, 'OKTOBER': 10, 'NOVEMBER': 11, 'DESEMBER': 12,
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MEI': 5, 'JUN': 6, 'JUL': 7, 'AGU': 8, 'SEP': 9, 'OKT': 10, 'NOV': 11, 'DES': 12
        }
        match = re.search(r'(\d{1,2})\s+([A-Z]+)', s)
        if match:
            day = int(match.group(1))
            month = months_map.get(match.group(2), 1)
            year_match = re.search(r'\b(20\d{2})\b', s)
            year = int(year_match.group(1)) if year_match else 2026
            return datetime.datetime(year, month, day)
        return pd.to_datetime(s, errors='coerce') if pd.to_datetime(s, errors='coerce') is not pd.NaT else datetime.datetime(2000, 1, 1)
    except: return datetime.datetime(2000, 1, 1)

def parse_numeric(value):
    try:
        if pd.isna(value) or str(value).strip() == "": return None
        s = str(value).strip()
        if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', s): return None
        s_clean = re.sub(r'(?i)rp|idr|\s|\xa0', '', s)
        if not re.match(r'^[-0-9.,]+$', s_clean): return None
        if '.' in s_clean and ',' not in s_clean:
            parts = s_clean.split('.')
            if len(parts[-1]) == 3: s_clean = s_clean.replace('.', '')
        if ',' in s_clean and '.' in s_clean:
            if s_clean.rfind(',') > s_clean.rfind('.'): s_clean = s_clean.replace('.', '').replace(',', '.')
            else: s_clean = s_clean.replace(',', '')
        elif ',' in s_clean:
            if len(s_clean.split(',')[-1]) == 3: s_clean = s_clean.replace(',', '')
            else: s_clean = s_clean.replace(',', '.')
        return float(s_clean)
    except: return None

def process_image_url(url):
    if not isinstance(url, str) or str(url).strip().lower() in ['nan', 'none', '']: return ""
    url_str = str(url).strip()
    if url_str.startswith("data:image"): return url_str 
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url_str)
    if match: return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800"
    return url_str

def image_to_base64(image_file):
    try:
        img = Image.open(image_file)
        if img.mode != 'RGB': img = img.convert('RGB')
        img.thumbnail((250, 250)) 
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=60)
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    exceptException as e: return None

def extract_code(text):
    try: return text.split('(')[1].split(')')[0].strip().zfill(3) 
    except: return "000"

def generate_new_sku(prefix_val, kat_full, det_full, current_df):
    try:
        prefix = str(prefix_val).strip().zfill(3)
        c_kat = extract_code(str(kat_full))
        c_det = extract_code(str(det_full))
        pattern = f"{prefix}-{c_kat}-{c_det}-"
        df_match = current_df[current_df['NOMOR SKU'].astype(str).str.contains(pattern, na=False)]
        if not df_match.empty:
            last_nums = []
            for s in df_match['NOMOR SKU'].astype(str):
                try: last_nums.append(int(s.split('-')[-1]))
                except: pass
            next_val = max(last_nums) + 1 if last_nums else 1
        else: next_val = 1
        return f"{prefix}-{c_kat}-{c_det}-{next_val:03d}"
    except: return "000-000-000-001"

# ==========================================
# 4. LOAD CORE DATA & LOOKUP LOGIC
# ==========================================
try:
    df_master = load_data(GID_MASTER)
    df_master.columns = df_master.columns.str.strip().str.upper()
    df_master = df_master.dropna(subset=['NAMA BAKU'])
    
    c_lvl = next((c for c in df_master.columns if 'LEVEL' in c or 'KELOMPOK' in c), 'LEVEL')
    if c_lvl in df_master.columns: df_master[c_lvl] = df_master[c_lvl].ffill().astype(str).str.strip().str.upper()
    if 'KATEGORI' in df_master.columns: df_master['KATEGORI'] = df_master['KATEGORI'].ffill().astype(str).str.strip().str.upper()
    if 'DETAIL KATEGORI' in df_master.columns: df_master['DETAIL KATEGORI'] = df_master['DETAIL KATEGORI'].ffill().astype(str).str.strip().str.upper()
    
    df_trans = load_data(GID_DASHBOARD)
    df_trans.columns = df_trans.columns.str.strip().str.upper()
    
    c_tgl_h = next((c for c in df_trans.columns if ('TANGGAL' in c or 'TGL' in c or 'DATE' in c) and 'REKAP' not in c), None)
    c_harga_h = next((c for c in df_trans.columns if 'HARGA' in c), None)
    c_baku_h = next((c for c in df_trans.columns if 'BAKU' in c), None)
    
    latest_price_map = {}
    if c_tgl_h and c_harga_h and c_baku_h:
        df_trans['PRICE_TEMP'] = df_trans[c_harga_h].apply(parse_harga)
        df_valid_trans = df_trans.dropna(subset=[c_baku_h]).copy()
        if not df_valid_trans.empty:
            df_valid_trans['TRUE_DATE'] = df_valid_trans[c_tgl_h].apply(convert_to_standard_date)
            df_sorted = df_valid_trans.sort_values(by=[c_baku_h, 'TRUE_DATE'], ascending=[True, True])
            df_latest = df_sorted.drop_duplicates(subset=[c_baku_h], keep='last')
            for _, row in df_latest.iterrows():
                if row['PRICE_TEMP'] > 0:
                    latest_price_map[str(row[c_baku_h]).strip().upper()] = {'harga': row['PRICE_TEMP'], 'tanggal': str(row[c_tgl_h]).strip()}

    df_master['AI_LOOKUP'] = df_master['NAMA BAKU'].astype(str).str.upper()
    if 'NAMA ITEM' in df_master.columns: df_master['AI_LOOKUP'] += " " + df_master['NAMA ITEM'].fillna("").astype(str).str.upper()
        
    search_list = df_master['AI_LOOKUP'].tolist()
    lookup_to_baku_map = dict(zip(df_master['AI_LOOKUP'], df_master['NAMA BAKU']))
    df_master_clean = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last').copy()
    mapping_master_info = df_master_clean.set_index('NAMA BAKU').to_dict('index')
except Exception as e: st.error(f"⚠️ Gagal Load Database Utama: {e}"); st.stop()

# ==========================================
# 5. SISTEM KEAMANAN (RBAC)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align: center; margin-top: 1vh; margin-bottom: 2vh;">
            <div style="display: inline-block; background: #ECFDF5; color: #047857; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 12px;">SECURE LOGIN PORTAL</div>
            <h1 style="color: #064E3B; font-weight: 800; font-size: 36px; letter-spacing: -1px; margin: 0;">PANCA BUDI</h1>
            <p style="color: #64748B; font-weight: 700; letter-spacing: 3px; font-size: 11px; text-transform: uppercase; margin-top: 5px;">Enterprise Procurement System</p>
        </div> """, unsafe_allow_html=True)
    _, col_guide, _ = st.columns([1.5, 5.3, 1.5])
    with col_guide:
        with st.expander("📖 PANDUAN PENGGUNAAN SISTEM (Klik untuk membaca)"):
            st.markdown("Sistem ERP Purchasing Holding untuk otomasi standarisasi material pabrik.")
    st.markdown("<div style='margin-bottom: 2.5vh;'></div>", unsafe_allow_html=True)
    col_space1, col_tamu, col_gap, col_admin, col_space2 = st.columns([1.5, 2.5, 0.3, 2.5, 1.5])
    with col_tamu:
        if st.button("Masuk Sebagai Tamu", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = True; st.session_state['role'] = "VIEWER"; st.session_state['nama'] = "Tamu Pabrik"; st.rerun()
    with col_admin:
        with st.form("form_admin"):
            input_pass = st.text_input("Kode Akses", type="password", placeholder="••••••••", label_visibility="collapsed")
            if st.form_submit_button("Otorisasi Akses", use_container_width=True, type="primary"):
                if input_pass == PASSWORD_ADMIN: st.session_state['logged_in'] = True; st.session_state['role'] = "ADMIN"; st.session_state['nama'] = "Admin Purchasing"; st.rerun()
                else: st.error("❌ Akses Ditolak")
    st.stop()

# Sidebar Navigation
with st.sidebar:
    st.markdown("<div style='text-align: center; padding: 10px 0;'><h1 style='color:#047857; font-weight:800; margin:0;'>PANCA BUDI</h1></div>", unsafe_allow_html=True)
    if st.button("🔄 Sync Database", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Logout / Keluar", use_container_width=True): st.session_state.clear(); st.rerun()
    user_role = st.session_state.get('role', 'VIEWER')
    menu_options = ["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"] if user_role == "ADMIN" else ["Pencarian Barang", "E-Catalog & Studio", "Database Vendor"]
    menu = option_menu("", menu_options, icon="dot", default_index=0)

# ==========================================
# MENU 1: PEMBERSIHAN PO (SUPER HYBRID DETECT)
# ==========================================
if menu == "Pembersihan PO":
    st.markdown("## ✨ Pembersihan Data Laporan Pabrik (Holding)")
    pilihan_format = st.selectbox("🏢 Pilih Asal Laporan / Format Pabrik:", ["Plant RA (Auto-Detect Format)", "Plant PGP (Auto-Detect Format)", "Plant Tangerang (Auto-Detect Format)", "Plant Pemalang (Auto-Detect Format)", "Plant Solo (Auto-Detect Format)", "Plant PIHC (Rekap Formulir Permintaan)", "ERP Pusat (Include/Exclude)"])
    
    with st.form("upload_holding"):
        file_raw = st.file_uploader("📥 Upload Excel Mentah:", type=["xlsx", "xls"])
        btn_proses = st.form_submit_button("🚀 Mulai Ekstraksi & AI Matching", type="primary")

    if btn_proses and file_raw:
        try:
            dict_df = pd.read_excel(file_raw, sheet_name=None, header=None)
            extracted_rows = []
            master_format_type = None

            for sheet_name, df_input in dict_df.items():
                format_type = ""
                detected_plant = ""
                
                # Scan layout token
                text_sample = " ".join([str(v) for v in df_input.head(15).values.flatten() if pd.notna(v)]).upper()

                if "ERP Pusat" in pilihan_format: format_type = "PUSAT"; detected_plant = "PUSAT"
                elif "PIHC" in pilihan_format: format_type = "NEW"; detected_plant = "PIHC"
                else:
                    if "Plant RA" in pilihan_format: detected_plant = "RA"
                    elif "Plant PGP" in pilihan_format: detected_plant = "PGP"
                    elif "Plant Tangerang" in pilihan_format: detected_plant = "TANGERANG"
                    elif "Plant Pemalang" in pilihan_format: detected_plant = "PEMALANG"
                    elif "Plant Solo" in pilihan_format: detected_plant = "SOLO"
                    
                    if "LAPORAN PO PER PEMASOK" in text_sample or ("NO BUKTI" in text_sample and "T. TERIMA" in text_sample):
                        format_type = "TANGERANG_LAP_PO"
                    else:
                        is_new = any("REKAP FORMULIR" in " ".join([str(c) for c in row.values if pd.notna(c)]).upper() for idx, row in df_input.head(20).iterrows())
                        format_type = "NEW" if is_new else ("RA_OLD" if "Plant RA" in pilihan_format else "OLD")

                if master_format_type is None: master_format_type = format_type
                else: format_type = master_format_type

                col_nama = col_qty = col_harga = col_vendor = col_po_asli = col_fpb = col_tgl = col_ppn = col_ket = col_sat = -1
                start_idx = 0
                global_date = "-"
                current_solo_month = ""
                curr_vendor_memory = ""

                # --- SENSOR BARU: TANGERANG PO PER PEMASOK CRACKER ---
                if format_type == "TANGERANG_LAP_PO":
                    for idx, row in df_input.iterrows():
                        row_cells = [str(c).strip() for c in row.values]
                        row_str = " | ".join(row_cells).upper()
                        
                        if any(x in row_str for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO"]): continue
                        
                        po_match = re.search(r'(02PBI-[A-Z0-9-]+|\b02PBI\d+\b)', row_str)
                        if po_match:
                            # Mengunci header PO dan Vendor Memory (Teks Warna Biru)
                            curr_po_block = po_match.group(1)
                            potensi = [c for c in row.values if pd.notna(c) and str(c).strip() != "" and curr_po_block not in str(c) and str(c).strip().upper() not in ["RP", "EUR", "USD", "NO BUKTI", "T. TERIMA", "NAMA BARANG"]]
                            if potensi: curr_vendor_memory = str(potensi[0]).strip()
                            continue
                        
                        date_m = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})', row_str)
                        if date_m and curr_vendor_memory != "":
                            # Baris Item Terdeteksi
                            item_name = ""
                            for c_idx in [3, 4, 2]: # Scan kolom Nama Barang / Nama Bahan
                                if c_idx < len(row.values) and pd.notna(row.values[c_idx]) and str(row.values[c_idx]).strip() != "" and not re.search(r'\d{2}/\d{2}/\d{4}', str(row.values[c_idx])):
                                    item_name = str(row.values[c_idx]).strip(); break
                            
                            if not item_name or item_name.lower() in ['nan', 'none', 'nama barang', 'nama bahan', 'eur', 'rp']: continue
                            
                            qty_val = parse_numeric(row.values[5]) if len(row.values) > 5 else 1.0
                            if qty_val is None: qty_val = 1.0
                            prc_val = parse_numeric(row.values[8]) if len(row.values) > 8 else 0.0
                            if prc_val is None: prc_val = 0.0
                            
                            ppn_val = "NON PPN"
                            if len(row.values) > 11:
                                ppn_num = parse_numeric(row.values[11])
                                if ppn_num and ppn_num > 0: ppn_val = "PPN"

                            extracted_rows.append({
                                "UNIT KERJA": "TANGERANG", "NO PO": curr_po_block, "NO FPB": "", "TANGGAL": date_m.group(0), "VENDOR": curr_vendor_memory,
                                "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "SATUAN": "PCS", "HARGA": prc_val, "STATUS_PPN": ppn_val
                            })

                # --- JALUR EXTRAC FORMAT LAMA ---
                elif format_type == "RA_OLD":
                    curr_po, curr_tgl, curr_vendor = "", "-", "-"
                    for idx, row in df_input.iterrows():
                        row_upper = [str(c).strip().upper() for c in row.values]
                        if "NAMA BARANG" in row_upper and "HARGA" in row_upper:
                            col_nama = row_upper.index("NAMA BARANG"); col_harga = row_upper.index("HARGA")
                            col_qty = next((i for i, x in enumerate(row_upper) if 'QTY' in x), -1)
                            col_sat = next((i for i, x in enumerate(row_upper) if 'SATUAN' in x), -1)
                            break
                    if col_nama != -1:
                        for idx, row in df_input.iterrows():
                            val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                            if not val_list or any(x in " | ".join(val_list).upper() for x in ["SUBTOTAL", "TOTAL :"]): continue
                            date_m = next((v for v in val_list if re.search(r'\d{2}/\d{2}/\d{4}', v)), None)
                            po_m = next((v for v in val_list if len(v) >= 4 and re.search(r'\d', v) and not re.match(r'^[-0-9.,]+$', v)), None)
                            if date_m:
                                curr_tgl = date_m.split(" ")[0]; curr_po = re.sub(r'^[\s:]+', '', po_m) if po_m else ""
                                pot = [v for v in val_list if v != date_m and v != po_m and not re.match(r'^[-0-9.,]+$', v)]
                                curr_vendor = max(pot, key=len) if pot else "CASH"
                                continue
                            if curr_po:
                                item_name = str(row.values[col_nama]).strip()
                                if item_name.lower() in ['', 'nan', 'nama barang']: continue
                                sat_val = str(row.values[col_sat]).strip() if col_sat != -1 and pd.notna(row.values[col_sat]) else "PCS"
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": curr_po, "NO FPB": "", "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": parse_numeric(row.values[col_qty]), "SATUAN": sat_val, "HARGA": parse_numeric(row.values[col_harga]), "STATUS_PPN": "NON PPN"
                                })

                elif format_type == "NEW":
                    for idx_g, row_g in df_input.head(15).iterrows():
                        text_g = " ".join([str(c).strip().upper() for c in row_g.values if pd.notna(c)])
                        m_g = re.search(r'\d{1,2}\s+[A-Z]+\s+\d{4}|\d{2}/\d{2}/\d{4}', text_g)
                        if m_g and "TANGGAL" in text_g: global_date = m_g.group(0); break

                    for idx, row in df_input.head(30).iterrows():
                        for i, c in enumerate(row.values):
                            if pd.isna(c): continue
                            x_clean = re.sub(r'\s+', ' ', str(c).strip().upper())
                            if ('JENIS BARANG' in x_clean or 'NAMA BARANG' in x_clean) and col_nama == -1: col_nama = i; start_idx = max(start_idx, idx)
                            elif 'HARGA' in x_clean and col_harga == -1: col_harga = i
                            elif 'VENDOR' in x_clean and col_vendor == -1: col_vendor = i
                            elif 'QTY' in x_clean and col_qty == -1: col_qty = i
                            elif 'SATUAN' in x_clean and col_sat == -1: col_sat = i
                            elif 'NO PO' in x_clean and col_po_asli == -1: col_po_asli = i
                            elif 'NO FPB' in x_clean: col_fpb = i
                            elif 'PPN' in x_clean: col_ppn = i

                    if col_nama != -1 and col_harga != -1:
                        for idx, row in df_input.iloc[start_idx+1:].iterrows():
                            val_list = [str(c).strip() for c in row.values if pd.notna(c)]
                            line_text = " | ".join(val_list).upper()
                            
                            if detected_plant == "SOLO":
                                for v in val_list:
                                    if v.upper() in ['JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI', 'JULI', 'AGUSTUS', 'SEPTEMBER', 'OKTOBER', 'NOVEMBER', 'DESEMBER']: current_solo_month = v.upper(); break
                            if any(x in line_text for x in ["SUBTOTAL", "TOTAL"]): continue
                            
                            try:
                                item_name = str(row.values[col_nama]).strip()
                                if not item_name or item_name.lower() in ['nan', 'none']: continue
                                sat_val = str(row.values[col_sat]).strip() if col_sat != -1 and pd.notna(row.values[col_sat]) else "PCS"
                                if sat_val.upper() in ['NAN', 'NONE', '']: sat_val = "PCS"
                                po_val = re.sub(r'^[\s:]+', '', str(row.values[col_po_asli])).strip() if col_po_asli != -1 else ""
                                
                                tgl_val = global_date
                                if detected_plant == "SOLO" and current_solo_month: tgl_val = f"1 {current_solo_month} 2026"
                                
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": po_val, "NO FPB": str(row.values[col_fpb]).strip() if col_fpb != -1 else "", "TANGGAL": tgl_val, "VENDOR": str(row.values[col_vendor]).strip() if col_vendor != -1 else "CASH",
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": parse_numeric(row.values[col_qty]), "SATUAN": sat_val, "HARGA": parse_numeric(row.values[col_harga]), "STATUS_PPN": "PPN" if col_ppn != -1 and "PPN" in str(row.values[col_ppn]).upper() else "NON PPN"
                                })
                            except: pass

            if extracted_rows:
                st.success(f"✔️ Berhasil mengekstrak {len(extracted_rows)} baris data!")
                final_draft = []
                for r in extracted_rows:
                    match = process.extractOne(str(r['ITEM_KOTOR']).upper(), search_list, scorer=fuzz.token_set_ratio)
                    if match and match[1] >= 75:
                        baku = lookup_to_baku_map[match[0]]; info = mapping_master_info.get(baku, {})
                        uom_final = r.get('SATUAN', 'PCS')
                        if uom_final == 'PCS' and str(info.get('SATUAN', '')).upper() not in ['NAN', 'NONE', '', 'PCS']: uom_final = info.get('SATUAN', 'PCS')
                        final_draft.append({
                            "❌ BUKAN SCOPE": False, "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "NO FPB": r.get('NO FPB', ''), "TANGGAL": r['TANGGAL'], "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], 
                            "NAMA_BAKU": baku, "QTY": r['QTY'], "SATUAN": uom_final, "HARGA": r['HARGA'], "STATUS PPN": r['STATUS_PPN'], "KATEGORI": info.get('KATEGORI', '-'), "DETAIL KATEGORI": info.get('DETAIL KATEGORI', '-'), "SKU": info.get('NOMOR SKU', '-')
                        })
                    else:
                        final_draft.append({
                            "❌ BUKAN SCOPE": False, "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "NO FPB": r.get('NO FPB', ''), "TANGGAL": r['TANGGAL'], "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], 
                            "NAMA_BAKU": "⚠️ BARANG BARU", "QTY": r['QTY'], "SATUAN": r.get('SATUAN', 'PCS'), "HARGA": r['HARGA'], "STATUS PPN": r['STATUS_PPN'], "KATEGORI": "", "DETAIL KATEGORI": "", "SKU": "-"
                        })
                cols_order = ["❌ BUKAN SCOPE", "UNIT", "PO", "NO FPB", "TANGGAL", "VENDOR", "ITEM_ASLI", "NAMA_BAKU", "QTY", "SATUAN", "HARGA", "STATUS PPN", "KATEGORI", "DETAIL KATEGORI", "SKU"]
                st.session_state['holding_draft'] = pd.DataFrame(final_draft)[cols_order]
                st.rerun()
        except Exception as e: st.error(f"Error Mesin: {e}")

    if 'holding_draft' in st.session_state:
        st.markdown("### ⚠️ TAHAP REVIEW HOLDING (UNLOCKED)")
        edited_df = st.data_editor(st.session_state['holding_draft'], use_container_width=True, hide_index=True, column_config={"❌ BUKAN SCOPE": st.column_config.CheckboxColumn("❌ BUKAN SCOPE", default=False), "STATUS PPN": st.column_config.SelectboxColumn("STATUS PPN", options=["PPN", "NON PPN"], required=True)})
        
        auto_time = st.checkbox("✅ Catat Waktu Rekap Secara Otomatis", value=True)
        manual_date = st.date_input("📅 Set Tanggal Rekap Manual:") if not auto_time else None
        filter_dokumen_valid = st.checkbox("✅ HANYA SIMPAN DATA BERDOKUMEN VALID (PO / FPB Ada)", value=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 KONFIRMASI: Simpan ke DASHBOARD & WORKBOOK", type="primary", use_container_width=True):
                try:
                    waktu_rekap = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if auto_time else manual_date.strftime("%Y-%m-%d")
                    df_to_save = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
                    if filter_dokumen_valid: df_to_save = df_to_save[(df_to_save['PO'].astype(str).str.strip() != "") | (df_to_save['NO FPB'].astype(str).str.strip() != "")]
                    
                    client = get_gspread_client()
                    sheet_dash = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD))
                    sheet_sandbox = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_SANDBOX))
                    
                    data_to_push = []
                    for _, r in df_to_save.iterrows():
                        data_to_push.append([r['UNIT'], r['PO'], r['NO FPB'], r['TANGGAL'], r['VENDOR'], "RP", r['ITEM_ASLI'], r['NAMA_BAKU'], r['QTY'], r['SATUAN'], r['HARGA'], r['STATUS PPN'], r['KATEGORI'], r['DETAIL KATEGORI'], r['SKU'], waktu_rekap])
                    
                    if data_to_push:
                        sheet_dash.append_rows(data_to_push); sheet_sandbox.append_rows(data_to_push)
                        st.balloons(); st.success("🔥 BERHASIL DISIMPAN!"); del st.session_state['holding_draft']; time.sleep(1.5); st.rerun()
                except Exception as e: st.error(f"Gagal: {e}")
        with c2:
            if st.button("❌ Batalkan Semua", use_container_width=True): del st.session_state['holding_draft']; st.rerun()

# ==========================================
# MENU 2: PENCARIAN BARANG
# ==========================================
elif menu == "Pencarian Barang":
    st.markdown("<h2>🔍 Global Search Engine</h2>", unsafe_allow_html=True)
    kata_cari = st.text_input("Ketik Kata Kunci (Nama Barang / SKU):")
    if kata_cari:
        hasil = process.extract(kata_cari, search_list, scorer=fuzz.token_set_ratio, limit=10)
        res_list = []
        for m in hasil:
            if m[1] >= 40:
                baku = lookup_to_baku_map[m[0]]; info = mapping_master_info.get(baku, {})
                harga_data = latest_price_map.get(str(baku).strip().upper(), {})
                res_list.append({"Match": f"{m[1]}%", "Nama Baku": baku, "SKU": info.get('NOMOR SKU', '-'), "Kategori": info.get('KATEGORI', '-'), "Est. Harga Live": format_rupiah(harga_data.get('harga', 0)), "Tgl PO Terakhir": harga_data.get('tanggal', '-')})
        st.dataframe(pd.DataFrame(res_list), use_container_width=True)

# ==========================================
# MENU 3: E-CATALOG & STUDIO GAMBAR
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio (Update Gambar)"])
    
    with t_cat:
        col_s, col_f, col_sort = st.columns([2, 1, 1])
        with col_s: search_cat = st.text_input("🔍 Cari Produk:")
        with col_f: filter_cat = st.selectbox("📁 Filter Kategori:", ["Semua Kategori"] + sorted([k for k in df_master_clean['KATEGORI'].unique() if pd.notna(k)]))
        df_show = df_master_clean.copy()
        if filter_cat != "Semua Kategori": df_show = df_show[df_show['KATEGORI'] == filter_cat]
        if search_cat: df_show = df_show[df_show['NAMA BAKU'].astype(str).str.contains(search_cat, case=False)]
        
        items_per_page = 20
        total_pages = max(1, (len(df_show) - 1) // items_per_page + 1)
        page_number = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
        df_page = df_show.iloc[(page_number - 1) * items_per_page : page_number * items_per_page]
        
        cols = st.columns(4)
        for idx, (_, row) in enumerate(df_page.iterrows()):
            with cols[idx % 4]:
                baku = row['NAMA BAKU']; harga_data = latest_price_map.get(str(baku).strip().upper(), {})
                img_url = process_image_url(str(row.get('LINK GAMBAR', '')).strip())
                img_element = f"<img src='{img_url}' style='width:100%; height:160px; object-fit:contain;'>" if img_url else "<div style='height:160px; background:#F1F5F9; text-align:center; padding-top:60px;'>No Image</div>"
                st.markdown(f"<div style='background:white; padding:16px; border-radius:12px; border:1px solid #E2E8F0;'>{img_element}<b>{baku}</b><br><small>SKU: {row.get('NOMOR SKU', '-')}</small><br><span style='color:#047857; font-weight:800;'>{format_rupiah(harga_data.get('harga', 0))}</span></div>", unsafe_allow_html=True)

    with t_studio:
        if user_role != "ADMIN": st.error("⛔ Akses Ditolak")
        else:
            barang_pilih = st.selectbox("Pilih Nama Produk:", df_master_clean['NAMA BAKU'].tolist())
            file_upload = st.file_uploader("Paste Gambar (Ctrl+V) / Upload", type=['png', 'jpg', 'jpeg'])
            if file_upload and st.button("💾 Simpan Gambar ke Database"):
                b64 = image_to_base64(file_upload)
                if b64:
                    client = get_gspread_client(); sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                    all_data = sheet_master.get_all_values(); headers_upper = [str(h).strip().upper() for h in all_data[0]]
                    col_letter = col_num_to_letter(headers_upper.index('LINK GAMBAR') + 1)
                    matching_rows = [idx + 2 for idx in df_master[df_master['NAMA BAKU'].astype(str).str.strip().str.upper() == barang_pilih.strip().upper()].index]
                    if matching_rows:
                        sheet_master.batch_update([{'range': f"{col_letter}{r}", 'values': [[b64]]} for r in matching_rows])
                        st.success("✅ Gambar Berhasil Ditanam!"); st.cache_data.clear(); st.rerun()

# ==========================================
# MENU 4: DATABASE VENDOR
# ==========================================
elif menu == "Database Vendor":
    st.markdown("<h2>🏢 Supplier Directory</h2>", unsafe_allow_html=True)
    keyword = st.text_input("Cari Vendor / PIC / Item:")
    try:
        df_v = load_data(GID_VENDOR); df_v.columns = df_v.columns.str.strip().str.upper()
        res = df_v[df_v.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)] if keyword else df_v.head(25)
        for _, v in res.iterrows():
            with st.expander(f"🏢 {v.get('NAMA VENDOR', '-')} | Cat: {v.get('KATEGORI', '-')} "):
                st.write(f"**Contact PIC:** {v.get('PIC', '-')} | 📞 {v.get('KONTAK', '-')}")
                st.write(f"**Alamat:** {v.get('ALAMAT', '-')}")
    except: st.warning("Koneksi Database Vendor Bermasalah.")

# ==========================================
# MENU 5: DASHBOARD LAPORAN (ANALYTICS)
# ==========================================
elif menu == "Dashboard Laporan":
    st.markdown("<h2>📊 Procurement Intelligence & Forecasting</h2>", unsafe_allow_html=True)
    try:
        data_dash = get_gspread_client().open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD)).get_all_values()
        if len(data_dash) > 1:
            df_d = pd.DataFrame(data_dash[1:], columns=data_dash[0]); df_d.columns = df_d.columns.str.strip().str.upper()
            df_d['TOTAL'] = df_d['HARGA SATUAN'].apply(parse_harga) * pd.to_numeric(df_d['QTY'], errors='coerce').fillna(0)
            df_d['DATE_CLEAN'] = df_d['TANGGAL'].apply(convert_to_standard_date)
            
            st.markdown(f"### Ringkasan Total Budget: {format_rupiah(df_d['TOTAL'].sum())}")
            st.plotly_chart(px.box(df_d, x='UNIT KERJA', y='TOTAL', title="Penyebaran Budget Operasional Plant"), use_container_width=True)
    except Exception as e: st.error(f"Gagal memuat visualisasi dashboard: {e}")

# ==========================================
# MENU 6: MAINTENANCE DATA (MASTER DATA EDITOR)
# ==========================================
elif menu == "Maintenance Data":
    st.markdown("<h2>🛠️ System Config & SKU Generator</h2>", unsafe_allow_html=True)
    if st.button("🔄 Generate Preview SKU", type="primary"):
        try:
            sheet_master = get_gspread_client().open_by_key(SHEET_ID).get_worksheet(0)
            all_data = sheet_master.get_all_values(); headers = [str(h).strip().upper() for h in all_data[0]]
            df_m = pd.DataFrame(all_data[1:], columns=headers)
            
            c_s = next((c for c in headers if 'SKU' in c), None)
            c_k = next((c for c in headers if 'KATEGORI' in c and 'DETAIL' not in c and 'LEVEL' not in c), None)
            c_d = next((c for c in headers if 'DETAIL' in c), None)
            c_lvl = next((c for c in headers if 'LEVEL' in c or 'KELOMPOK' in c), None)
            
            preview_data = []
            for idx, row in df_m.iterrows():
                val = str(row[c_s]).strip()
                if len(val) < 10 or val.upper() in ['NAN', 'NONE', '']:
                    prefix_val = extract_code(str(row[c_lvl])) if c_lvl else "001"
                    new_sku = generate_new_sku(prefix_val, row[c_k], row[c_d], df_m)
                    df_m.at[idx, c_s] = new_sku
                    preview_data.append({"Baris Excel": idx + 2, "NAMA BAKU": row.get('NAMA BAKU', '-'), "LEVEL": row[c_lvl], "KATEGORI": row[c_k], "DETAIL KATEGORI": row[c_d], "SKU BARU": new_sku})
            st.session_state['draft_sku_df'] = df_m; st.session_state['preview_sku_list'] = pd.DataFrame(preview_data)
        except Exception as e: st.error(f"Error: {e}")

    if 'preview_sku_list' in st.session_state:
        edited_preview = st.data_editor(st.session_state['preview_sku_list'], disabled=["Baris Excel", "NAMA BAKU"], use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Konfirmasi & Tembak ke Master Data", type="primary", use_container_width=True):
                try:
                    df_full = st.session_state['draft_sku_df']
                    c_s = next((c for c in df_full.columns if 'SKU' in c), None)
                    c_k = next((c for c in df_full.columns if 'KATEGORI' in c and 'DETAIL' not in c), None)
                    c_d = next((c for c in df_full.columns if 'DETAIL' in c), None)
                    c_lvl = next((c for c in df_full.columns if 'LEVEL' in c or 'KELOMPOK' in c), None)
                    
                    for _, row in edited_preview.iterrows():
                        excel_idx = row["Baris Excel"] - 2
                        if c_s: df_full.at[excel_idx, c_s] = row["SKU BARU"]
                        if c_k: df_full.at[excel_idx, c_k] = row["KATEGORI"]
                        if c_d: df_full.at[excel_idx, c_d] = row["DETAIL KATEGORI"]
                        if c_lvl: df_full.at[excel_idx, c_lvl] = row["LEVEL"]
                        
                    sheet_master = get_gspread_client().open_by_key(SHEET_ID).get_worksheet(0)
                    sheet_master.clear(); sheet_master.update(values=[df_full.columns.tolist()] + df_full.values.tolist())
                    st.success("✔️ Berhasil Update!"); del st.session_state['draft_sku_df']; del st.session_state['preview_sku_list']; time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Gagal update: {e}")
        with col2:
            if st.button("❌ Batal", use_container_width=True): del st.session_state['draft_sku_df']; del st.session_state['preview_sku_list']; st.rerun()

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #94A3B8; font-size: 12px;'>ERP Purchasing System v13.5 | Proprietary of PT Panca Budi Idaman Tbk | Created with ❤️ for Raihan Subakti<br><span style='color: #10B981; font-weight: 600;'>🟢 Live Database tersinkronisasi pada: {get_sync_time()}</span></p>", unsafe_allow_html=True)