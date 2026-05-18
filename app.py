# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 11.8 (ULTIMATE FULL VERSION - Smart PO Filter & PIHC Override)
# Fitur: Blank PO Filter, Force Light Mode, Dynamic Pricing, Double Injection
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
    
    /* Header TIDAK disembunyikan agar tombol panah HP tetap terlihat */
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
        color: #FFFFFF !important; /* Pastikan teks tombol utama tetap putih */
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
GID_MASTER = "0"              # Sheet 1: Master Data
GID_VENDOR = "168217676"      # Sheet 2: Database Vendor
GID_DASHBOARD = "1693047728"  # Sheet 3: Dashboard Laporan (Target Utama)
GID_SANDBOX = "1722600044"    # Sheet 4: Lembar Kerja/Sandbox (Target Kedua)

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

def parse_numeric(value):
    try:
        if pd.isna(value) or str(value).strip() == "": return None
        s = str(value).strip()
        if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', s): return None
        s_clean = re.sub(r'(?i)rp|idr|\s|\xa0', '', s)
        if not re.match(r'^[-0-9.,]+$', s_clean): return None
        if ',' in s_clean and '.' in s_clean:
            if s_clean.rfind(',') > s_clean.rfind('.'): s_clean = s_clean.replace('.', '').replace(',', '.')
            else: s_clean = s_clean.replace(',', '')
        elif ',' in s_clean: s_clean = s_clean.replace(',', '.')
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
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        return None

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

def create_metric_card(icon_class, title, value):
    return f"""
    <div style="background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); height:100%; display:flex; flex-direction:column; justify-content:center;">
        <div><i class="{icon_class}" style="color:#D4AF37; font-size:28px; margin-bottom:12px;"></i></div>
        <div style="color:#64748B; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;">{title}</div>
        <div style="color:#0F172A; font-size:22px; font-weight:800; line-height:1.3; word-wrap:break-word;">{value}</div>
    </div>
    """

def col_num_to_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

# ==========================================
# 4. LOAD CORE DATA & DYNAMIC PRICING LOGIC
# ==========================================
try:
    df_master = load_data(GID_MASTER)
    df_master.columns = df_master.columns.str.strip().str.upper()
    df_master = df_master.dropna(subset=['NAMA BAKU'])
    
    if 'KATEGORI' in df_master.columns: df_master['KATEGORI'] = df_master['KATEGORI'].ffill().astype(str).str.strip().str.upper()
    if 'DETAIL KATEGORI' in df_master.columns: df_master['DETAIL KATEGORI'] = df_master['DETAIL KATEGORI'].ffill().astype(str).str.strip().str.upper()
    
    df_trans = load_data(GID_DASHBOARD)
    df_trans.columns = df_trans.columns.str.strip().str.upper()
    
    c_tgl_h = next((c for c in df_trans.columns if ('TANGGAL' in c or 'TGL' in c or 'DATE' in c) and 'REKAP' not in c), None)
    c_harga_h = next((c for c in df_trans.columns if 'HARGA' in c), None)
    c_baku_h = next((c for c in df_trans.columns if 'BAKU' in c), None)
    
    latest_price_map = {}
    if c_tgl_h and c_harga_h and c_baku_h:
        df_trans['DATE_TEMP'] = pd.to_datetime(df_trans[c_tgl_h], errors='coerce')
        df_trans['PRICE_TEMP'] = df_trans[c_harga_h].apply(parse_harga)
        df_valid_trans = df_trans.dropna(subset=['DATE_TEMP', 'PRICE_TEMP', c_baku_h])
        
        if not df_valid_trans.empty:
            df_sorted = df_valid_trans.sort_values(by=[c_baku_h, 'DATE_TEMP'], ascending=[True, False])
            df_latest = df_sorted.drop_duplicates(subset=[c_baku_h])
            for _, row in df_latest.iterrows():
                latest_price_map[str(row[c_baku_h]).strip().upper()] = {
                    'harga': row['PRICE_TEMP'],
                    'tanggal': str(row[c_tgl_h]).split(' ')[0] 
                }

    df_master['AI_LOOKUP'] = df_master['NAMA BAKU'].astype(str).str.upper()
    if 'NAMA ITEM' in df_master.columns: 
        df_master['AI_LOOKUP'] += " " + df_master['NAMA ITEM'].fillna("").astype(str).str.upper()
        
    search_list = df_master['AI_LOOKUP'].tolist()
    lookup_to_baku_map = dict(zip(df_master['AI_LOOKUP'], df_master['NAMA BAKU']))
    
    df_master_clean = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last').copy()
    mapping_master_info = df_master_clean.set_index('NAMA BAKU').to_dict('index')

except Exception as e:
    st.error(f"⚠️ Gagal Load Database Utama: {e}"); st.stop()


# ==========================================
# 5. SISTEM KEAMANAN LUXURY (2 PINTU LOGIN)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align: center; margin-top: 1vh; margin-bottom: 2vh;">
            <div style="display: inline-block; background: #ECFDF5; color: #047857; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 12px;">SECURE LOGIN PORTAL</div>
            <h1 style="color: #064E3B; font-weight: 800; font-size: 36px; letter-spacing: -1px; margin: 0;">PANCA BUDI</h1>
            <p style="color: #64748B; font-weight: 700; letter-spacing: 3px; font-size: 11px; text-transform: uppercase; margin-top: 5px;">Enterprise Procurement System</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col_guide, _ = st.columns([1.5, 5.3, 1.5])
    with col_guide:
        with st.expander("📖 PANDUAN PENGGUNAAN SISTEM (Klik untuk membaca)"):
            st.markdown("""
            **Selamat datang di ERP Purchasing PT Panca Budi Idaman Tbk!**
            Sistem ini dirancang untuk mempermudah operasional *Supply Chain*, pencarian spesifikasi barang, dan standardisasi data antar seluruh pabrik.

            ---
            **🚪 1. PINTU TAMU (Guest Access)**
            Dikhususkan untuk staf Pabrik atau Gudang.
            * **Akses Masuk:** Tidak memerlukan kata sandi. Langsung klik tombol putih *"Masuk Sebagai Tamu"*.
            * **Fitur Terbuka:** * `Pencarian Barang`: Ketik nama barang/SKU untuk mencari spesifikasi standar pusat.
                * `E-Catalog`: Melihat foto fisik barang, estimasi harga terakhir beserta Tanggal PO-nya, dan download PDF Katalog.
                * `Database Vendor`: Mencari nomor telepon dan nama PIC Supplier.
            * *Catatan: Modul Tamu bersifat "Read-Only". Anda tidak dapat menghapus atau merubah data apapun.*

            **👑 2. PINTU ADMIN (Admin Portal)**
            Dikhususkan untuk tim Holding Purchasing Pusat.
            * **Akses Masuk:** Wajib memasukkan Kata Sandi Rahasia Otoritas.
            * **Fitur Ekstra Terbuka:**
                * `Pembersihan PO`: Mesin AI untuk menyamakan nama laporan mentah dari plant (RA, PGP, dll) ke dalam bahasa standar Holding.
                * `Double Injection`: Simpan ke Sheet 3 & Sheet 4 secara bersamaan.
                * `Asset Studio`: Fitur Injeksi Gambar (Bisa Copy-Paste Ctrl+V langsung dari Google).
                * `Dashboard Laporan`: Akses *Executive Filter* dan AI Forecasting.
            
            ---
            *Bila Anda mengalami kendala teknis, silakan hubungi Tim Purchasing Holding Pusat.*
            """)
    
    st.markdown("<div style='margin-bottom: 2.5vh;'></div>", unsafe_allow_html=True)
    
    col_space1, col_tamu, col_gap, col_admin, col_space2 = st.columns([1.5, 2.5, 0.3, 2.5, 1.5])
    
    with col_tamu:
        st.markdown("""
            <div style="text-align: center; padding: 20px 15px 15px 15px; background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 100%; margin-bottom: 15px;">
                <div style="font-size: 40px; margin-bottom: 10px;">🏢</div>
                <h3 style="color: #0F172A; font-weight: 800; font-size: 18px; margin-bottom: 8px;">Guest Access</h3>
                <p style="color: #64748B; font-size: 12px; line-height: 1.4; margin-bottom: 5px; padding: 0 10px;">
                    Jelajahi E-Catalog, spesifikasi SKU, dan direktori Vendor tanpa otorisasi.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Masuk Sebagai Tamu", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = True
            st.session_state['role'] = "VIEWER"
            st.session_state['nama'] = "Tamu Pabrik"
            st.rerun()

    with col_admin:
        st.markdown("""
            <div style="text-align: center; padding: 20px 15px 15px 15px; background-color: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 16px; box-shadow: 0 4px 6px rgba(4,120,87,0.05); height: 100%; margin-bottom: 15px;">
                <div style="font-size: 40px; margin-bottom: 10px;">🛡️</div>
                <h3 style="color: #064E3B; font-weight: 800; font-size: 18px; margin-bottom: 8px;">Admin Portal</h3>
                <p style="color: #047857; font-size: 12px; line-height: 1.4; margin-bottom: 5px; padding: 0 10px;">
                    Akses penuh ke modul pembersihan data, laporan, dan master maintenance.
                </p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("form_admin"):
            input_pass = st.text_input("Kode Akses", type="password", placeholder="••••••••", label_visibility="collapsed")
            btn_login = st.form_submit_button("Otorisasi Akses", use_container_width=True, type="primary")
            
            if btn_login:
                if input_pass == PASSWORD_ADMIN:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = "ADMIN"
                    st.session_state['nama'] = "Admin Purchasing"
                    st.rerun()
                else:
                    st.error("❌ Akses Ditolak: Kode Sandi Tidak Valid")
                    
    st.stop() 


# ==========================================
# 6. SIDEBAR NAVIGATION (DYNAMIC RBAC)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 10px 0 10px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px;'>
            <h1 style='color: #047857; font-weight: 800; margin: 0; font-size: 32px; letter-spacing: -1px;'>PANCA BUDI</h1>
            <p style='color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 2px; margin: 0;'>HOLDING PURCHASING</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Sync Database", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown(f"""
        <div style='background-color:#F1F5F9; padding:10px; border-radius:8px; margin-bottom:15px; text-align:center;'>
            <p style='margin:0; font-size:12px; color:#64748B;'>Login sebagai:</p>
            <p style='margin:0; font-weight:800; color:#0F172A; font-size:14px;'>👤 {st.session_state['nama']}</p>
            <span style='background-color:{"#047857" if st.session_state['role'] == "ADMIN" else "#64748B"}; color:white; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;'>{st.session_state['role']}</span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout / Keluar", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state.clear()
        st.rerun()

    st.write("---")
    
    user_role = st.session_state.get('role', 'VIEWER')
    
    if user_role == "ADMIN":
        menu_options = ["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"]
        menu_icons = ["magic", "search", "images", "shop", "bar-chart-line", "tools"]
    else: 
        menu_options = ["Pencarian Barang", "E-Catalog & Studio", "Database Vendor"]
        menu_icons = ["search", "images", "shop"]
    
    menu = option_menu(
        menu_title="", 
        options=menu_options,
        icons=menu_icons, 
        default_index=0, 
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#64748B", "font-size": "18px"}, 
            "nav-link": {"color": "#334155", "font-weight": "500", "font-size": "15px", "text-align": "left", "margin":"4px 0", "--hover-color": "#F1F5F9", "border-radius": "8px"},
            "nav-link-selected": {"background-color": "#047857", "color": "white", "icon-color": "white", "font-weight": "600"},
        }
    )

# ==========================================
# MENU 1: PEMBERSIHAN PO (HOLDING VERSION)
# ==========================================
if menu == "Pembersihan PO":
    st.markdown("## ✨ Pembersihan Data Laporan Pabrik (Holding)")
    st.write("Ubah laporan mentah dari berbagai format ERP Plant menjadi data bersih Holding.")
    
    col_sel, col_empty = st.columns([1.5, 1])
    with col_sel:
        pilihan_format = st.selectbox("🏢 Pilih Asal Laporan / Format Pabrik:", 
                                     ["Plant RA (Auto-Detect Format)", 
                                      "Plant PGP (Auto-Detect Format)",
                                      "Plant Tangerang (Auto-Detect Format)", 
                                      "Plant Pemalang (Auto-Detect Format)",
                                      "Plant Solo (Auto-Detect Format)",
                                      "Plant PIHC (Rekap Formulir Permintaan)",
                                      "ERP Pusat (Include/Exclude)"])

    with st.form("upload_holding"):
        file_raw = st.file_uploader("📥 Upload Excel Mentah (Drag & Drop di sini):", type=["xlsx", "xls"])
        btn_proses = st.form_submit_button("🚀 Mulai Ekstraksi & AI Matching", type="primary")

    if btn_proses and file_raw:
        try:
            dict_df = pd.read_excel(file_raw, sheet_name=None, header=None)
            extracted_rows = []
            
            if "Plant RA" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect RA sedang memindai format (Lama/Baru) pada seluruh sheet...")
            elif "Plant PGP" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect PGP sedang memindai format (Lama/Baru) pada seluruh sheet...")
            elif "Plant Tangerang" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect Tangerang sedang memindai format (Lama/Baru) pada seluruh sheet...")
            elif "Plant Pemalang" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect Pemalang sedang memindai format (Lama/Baru) pada seluruh sheet...")
            elif "Plant Solo" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect Solo sedang memindai format pada seluruh sheet...")
            elif "PIHC" in pilihan_format:
                st.info("🤖 Mata Pisau Khusus PIHC menjahit kolom beda baris di seluruh sheet...")
            elif "ERP Pusat" in pilihan_format:
                st.info("🤖 Mesin ERP Pusat membaca seluruh sheet...")

            master_format_type = None
            master_cols_new = None

            for sheet_name, df_input in dict_df.items():
                format_type = ""
                detected_plant = ""

                if "ERP Pusat" in pilihan_format:
                    format_type = "PUSAT"; detected_plant = "PUSAT"
                elif "PIHC" in pilihan_format:
                    format_type = "NEW"; detected_plant = "PIHC"
                else:
                    if "Plant RA" in pilihan_format: detected_plant = "RA"
                    elif "Plant PGP" in pilihan_format: detected_plant = "PGP"
                    elif "Plant Tangerang" in pilihan_format: detected_plant = "TANGERANG"
                    elif "Plant Pemalang" in pilihan_format: detected_plant = "PEMALANG"
                    elif "Plant Solo" in pilihan_format: detected_plant = "SOLO"
                    
                    is_new = False
                    for idx, row in df_input.head(20).iterrows():
                        teks_sebaris = " ".join([str(c).strip().upper() for c in row.values if pd.notna(c)])
                        if "REKAP FORMULIR" in teks_sebaris or "PENUNJUKKAN VENDOR" in teks_sebaris or "FORMULIR PERMINTAAN" in teks_sebaris:
                            is_new = True
                            break
                    format_type = "NEW" if is_new else ("RA_OLD" if "Plant RA" in pilihan_format else "OLD")

                if master_format_type is None:
                    master_format_type = format_type
                else:
                    format_type = master_format_type

                if format_type == "RA_OLD":
                    curr_po, curr_tgl, curr_vendor = "", "-", "-"
                    col_nama, col_qty, col_harga = -1, -1, -1
                    
                    for idx, row in df_input.iterrows():
                        row_upper = [str(c).strip().upper() for c in row.values]
                        if "NAMA BARANG" in row_upper and "HARGA" in row_upper:
                            col_nama = row_upper.index("NAMA BARANG")
                            col_harga = row_upper.index("HARGA")
                            for i, x in enumerate(row_upper):
                                if 'QTY' in x: col_qty = i; break
                            break 
                            
                    if col_nama != -1 and col_harga != -1 and col_qty != -1:
                        for idx, row in df_input.iterrows():
                            val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                            if not val_list: continue
                            line_text = " | ".join(val_list).upper()
                            
                            if any(x in line_text for x in ["SUBTOTAL", "TOTAL :", "LAP.PEMBELIAN", "PAGE"]): continue
                            
                            # V11.6 FIX: Cukup deteksi tanggal untuk menandakan Header Row
                            date_m = next((v for v in val_list if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v)), None)
                            po_m = next((v for v in val_list if len(v) >= 4 and re.search(r'\d', v) and not re.match(r'^[-0-9.,]+$', v)), None)
                            
                            if date_m:
                                curr_tgl = date_m.split(" ")[0]
                                curr_po = po_m if po_m else "" # V11.8 FIX: Kosongkan jika tidak ada PO
                                potensi_vendor = [v for v in val_list if v != date_m and v != po_m and not re.match(r'^[-0-9.,]+$', v) and "00/01/1900" not in v]
                                curr_vendor = max(potensi_vendor, key=len).replace("00/01/1900", "").strip() if potensi_vendor else "CASH / TANPA NAMA"
                                continue
                                
                            if curr_po != "-": # Will process if curr_po is "" or string
                                if col_nama < len(row.values) and col_qty < len(row.values) and col_harga < len(row.values):
                                    item_name = str(row.values[col_nama]).strip()
                                    if item_name.lower() in ['', 'nan', 'none', 'nama barang', 'subtotal', 'subtotal :']: continue
                                    
                                    qty_val = parse_numeric(row.values[col_qty])
                                    prc_val = parse_numeric(row.values[col_harga])
                                    
                                    if qty_val is not None and prc_val is not None:
                                        extracted_rows.append({
                                            "UNIT KERJA": detected_plant, "NO PO": curr_po, "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                            "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "HARGA": prc_val
                                        })

                elif format_type == "OLD":
                    curr_po, curr_tgl, curr_vendor, curr_money = "", "-", "-", "RP"

                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        if not val_list: continue
                        line_text = " | ".join(val_list).upper()

                        if any(x in line_text for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line_text or "EXCLUDE" in line_text:
                            curr_po = val_list[0] if len(val_list) > 0 else ""
                            if curr_po.upper() in ["INCLUDE", "EXCLUDE"]: curr_po = "" # Jika salah ambil header
                            
                            for c in val_list: 
                                m = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', c)
                                if m: curr_tgl = m.group(0); break
                                
                            potensi_vendor = [v for v in val_list if " - " in v]
                            if potensi_vendor:
                                curr_vendor = potensi_vendor[-1].split(" - ")[-1].strip()
                            else:
                                curr_vendor = "CASH / TANPA NAMA"
                                
                            curr_money = "RP"
                            for m in ["USD", "EUR", "CNY", "JPY"]:
                                if m in line_text: curr_money = m; break
                            continue
                            
                        if curr_po != "-":
                            nums = []
                            for v in val_list:
                                n = parse_numeric(v)
                                if n is not None: nums.append(n)
                            
                            if len(nums) >= 2:
                                names = []
                                for v in val_list:
                                    v_str = str(v).strip()
                                    if parse_numeric(v_str) is not None: continue
                                    if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v_str): continue
                                    if v_str.upper() in ["RP", "USD", "EUR", "CNY", "IDR"]: continue
                                    
                                    v_clean = v_str.replace('\xa0', '').strip()
                                    if len(v_clean) >= 8 and " " not in v_clean and re.search(r'\d', v_clean):
                                        continue 

                                    names.append(v_str)
                                
                                item_name = max(names, key=len) if names else "Unknown"
                                qty_val = nums[1] if len(nums) > 1 else nums[0]
                                prc_val = nums[2] if len(nums) > 2 else 0.0
                                
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": curr_po, "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                    "MATA UANG": curr_money, "ITEM_KOTOR": item_name, "QTY": qty_val, "HARGA": prc_val
                                })

                elif format_type == "NEW":
                    # V11.8 FIX: HANYA fokus mencari NO PO
                    col_nama = col_qty = col_harga = col_vendor = col_po_asli = col_tgl = -1
                    start_idx = 0
                    global_date = "-"
                    
                    for idx_g, row_g in df_input.head(15).iterrows():
                        text_g = " ".join([str(c).strip().upper() for c in row_g.values if pd.notna(c)])
                        m_g = re.search(r'\d{1,2}\s+[A-Z]+\s+\d{4}|\d{1,2}-[A-Z]{3}-?\d{0,4}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', text_g)
                        if m_g and ("TANGGAL" in text_g or "DATE" in text_g or "TGL" in text_g):
                            global_date = m_g.group(0); break

                    if master_cols_new is None:
                        for idx, row in df_input.head(30).iterrows():
                            for i, c in enumerate(row.values):
                                if pd.isna(c): continue
                                x_clean = re.sub(r'\s+', ' ', str(c).strip().upper())
                                
                                if ('JENIS BARANG' in x_clean or 'NAMA BARANG' in x_clean) and col_nama == -1: 
                                    col_nama = i; start_idx = max(start_idx, idx)
                                elif 'HARGA' in x_clean and 'PER' not in x_clean and 'UPDATE' not in x_clean and col_harga == -1: 
                                    col_harga = i; start_idx = max(start_idx, idx)
                                elif 'VENDOR' in x_clean and 'PENUNJUKKAN' not in x_clean and col_vendor == -1: 
                                    col_vendor = i; start_idx = max(start_idx, idx)
                                elif ('QTY' in x_clean) and col_qty == -1: 
                                    col_qty = i
                                # V11.8 FIX: Paksa HANYA ambil kolom NO PO ASLI
                                elif ('NO PO' in x_clean or 'NOMOR PO' in x_clean or 'NO. PO' in x_clean) and 'STATUS' not in x_clean: 
                                    col_po_asli = i
                                elif ('PENYELESAIAN' in x_clean or 'TGL EMAIL' in x_clean or 'DATANG' in x_clean) and col_tgl == -1: 
                                    col_tgl = i
                        
                        if col_nama != -1 and col_harga != -1:
                            master_cols_new = (col_nama, col_qty, col_harga, col_vendor, col_po_asli, col_tgl)
                    else:
                        col_nama, col_qty, col_harga, col_vendor, col_po_asli, col_tgl = master_cols_new
                        start_idx = -1
                                
                    if col_nama != -1 and col_harga != -1:
                        for idx, row in df_input.iloc[start_idx+1:].iterrows():
                            val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                            if not val_list: continue
                            
                            line_text = " | ".join(val_list).upper()
                            if any(x in line_text for x in ["SUBTOTAL", "TOTAL", "REKAP FORMULIR"]): continue
                            
                            try:
                                item_name = str(row.values[col_nama]).strip()
                                if item_name.lower() in ['', 'nan', 'none']: continue
                                
                                qty_val = parse_numeric(row.values[col_qty]) if col_qty != -1 else 1.0
                                if qty_val is None: qty_val = 1.0
                                
                                prc_val = parse_numeric(row.values[col_harga])
                                if prc_val is None: prc_val = 0.0
                                
                                v_str = str(row.values[col_vendor]).strip() if col_vendor != -1 else "-"
                                vendor_val = v_str if v_str.lower() not in ['nan', 'none', ''] else "CASH / TANPA NAMA"
                                
                                # V11.8 FIX: Kosongkan (Blank) jika PO tidak ada. Jangan pakai strip (-)
                                po_str = str(row.values[col_po_asli]).strip() if col_po_asli != -1 else ""
                                po_val = po_str if po_str.lower() not in ['nan', 'none', '-', ''] else ""

                                if prc_val == 0 and po_val == "": continue 
                                
                                tgl_val = "-"
                                if col_tgl != -1:
                                    tgl_str = str(row.values[col_tgl]).strip()
                                    if tgl_str.lower() not in ['nan', 'none', '']:
                                        if "00:00:00" in tgl_str: tgl_val = tgl_str.split(" ")[0]
                                        else: tgl_val = tgl_str
                                
                                if tgl_val == "-":
                                    for v in val_list:
                                        m = re.search(r'\d{1,2}-[a-zA-Z]{3}-?\d{0,4}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v)
                                        if m: tgl_val = m.group(0); break
                                
                                if tgl_val == "-" and global_date != "-":
                                    tgl_val = global_date
                                    
                                m_fpb = re.search(r'[A-Za-z]*(\d{2})(0[1-9]|1[0-2])[-/]', po_val)
                                if m_fpb:
                                    year_fpb = "20" + m_fpb.group(1)
                                    month_fpb = m_fpb.group(2)
                                    tgl_val = f"{year_fpb}-{month_fpb}-01"
                                            
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": po_val, "TANGGAL": tgl_val, "VENDOR": vendor_val,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "HARGA": prc_val
                                })
                            except Exception: pass

                elif format_type == "PUSAT":
                    curr_po, curr_tgl, curr_vendor, curr_money = "", "-", "-", "RP"
                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        line = " | ".join(val_list).upper()
                        
                        if not val_list or any(x in line for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line or "EXCLUDE" in line:
                            curr_po = val_list[0] if len(val_list)>0 else ""
                            for c in val_list: 
                                m = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', c)
                                if m: curr_tgl = m.group(0); break
                            curr_vendor = "-"
                            for c in val_list:
                                if " - " in c: curr_vendor = c.split(" - ")[-1].strip(); break
                            curr_money = "RP"
                            for m in ["USD", "EUR", "CNY", "JPY"]:
                                if m in line: curr_money = m; break
                            continue
                            
                        if curr_po != "-":
                            if len(val_list) >= 4:
                                nums = []
                                for v in reversed(val_list):
                                    n = parse_numeric(v)
                                    if n is not None: nums.insert(0, n)
                                
                                if len(nums) >= 2:
                                    names = []
                                    for v in val_list:
                                        v_str = str(v).strip()
                                        if parse_numeric(v_str) is not None: continue
                                        if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v_str): continue
                                        if re.match(r'^\d+\s+[A-Za-z]', v_str): continue 
                                        if v_str.upper() in ["RP", "USD", "EUR", "CNY", "IDR"]: continue
                                        names.append(v_str)
                                    
                                    item_name = max(names, key=len) if names else "Unknown"
                                    extracted_rows.append({
                                        "UNIT KERJA": "PUSAT", "NO PO": curr_po, "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                        "MATA UANG": curr_money, "ITEM_KOTOR": item_name, "QTY": nums[0], "HARGA": nums[-1]
                                    })

            if extracted_rows:
                st.success(f"✔️ Berhasil mengekstrak {len(extracted_rows)} baris data mentah yang valid dari seluruh Sheet!")
                final_draft = []
                for r in extracted_rows:
                    match = process.extractOne(str(r['ITEM_KOTOR']).upper(), search_list, scorer=fuzz.token_set_ratio)
                    if match and match[1] >= 75:
                        baku = lookup_to_baku_map[match[0]]; info = mapping_master_info.get(baku, {})
                        final_draft.append({
                            "❌ BUKAN SCOPE": False,
                            "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "TANGGAL": r['TANGGAL'], 
                            "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], 
                            "NAMA_BAKU": baku, "SKU": info.get('NOMOR SKU', '-'), 
                            "KATEGORI": info.get('KATEGORI', '-'),
                            "DETAIL KATEGORI": info.get('DETAIL KATEGORI', '-'),
                            "QTY": r['QTY'], "HARGA": r['HARGA']
                        })
                    else:
                        final_draft.append({
                            "❌ BUKAN SCOPE": False,
                            "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "TANGGAL": r['TANGGAL'], 
                            "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], 
                            "NAMA_BAKU": "⚠️ BARANG BARU", "SKU": "-", 
                            "KATEGORI": "", 
                            "DETAIL KATEGORI": "", 
                            "QTY": r['QTY'], "HARGA": r['HARGA']
                        })
                
                st.session_state['holding_draft'] = pd.DataFrame(final_draft)
                st.rerun()
            else:
                st.warning("⚠️ Data item kosong! Pastikan file Excel sesuai format pabrik yang Anda pilih.")

        except Exception as e: st.error(f"Error Mesin: {e}")

    if 'holding_draft' in st.session_state:
        st.markdown("### ⚠️ TAHAP REVIEW HOLDING (UNLOCKED)")
        st.info("💡 **INFO PENTING:** Semua kolom di bawah ini **BISA DIEDIT**. Baris yang kolom PO-nya kosong akan terlihat jelas. Anda bisa mengabaikannya jika akan menggunakan fitur filter otomatis di bawah.")
        
        edited_df = st.data_editor(
            st.session_state['holding_draft'], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "❌ BUKAN SCOPE": st.column_config.CheckboxColumn(
                    "❌ BUKAN SCOPE",
                    help="Centang untuk MEMBUANG barang ini dari laporan",
                    default=False,
                )
            }
        )
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; font-size:16px; margin-bottom:10px;'>🕒 Setup Penyimpanan</h4>", unsafe_allow_html=True)
        auto_time = st.checkbox("✅ Catat Waktu Rekap Secara Otomatis (Live Timestamp)", value=True)
        manual_date = st.date_input("📅 Set Tanggal Rekap Manual (Backdate):") if not auto_time else None
        
        # V11.8 FIX: CHECKBOX FILTER SMART UPLOAD
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        filter_po_kosong = st.checkbox("✅ HANYA SIMPAN & EXCEL-KAN DATA YANG SUDAH MEMILIKI NOMOR PO (Abaikan PO Kosong)", value=True, help="Jika dicentang, barang yang kolom PO-nya kosong tidak akan dimasukkan ke database.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 KONFIRMASI: Simpan ke DASHBOARD & WORKBOOK", type="primary", use_container_width=True):
                try:
                    with st.spinner("🚀 Menembakkan data ke Sheet 3 & Sheet 4..."):
                        tz_wib = datetime.timezone(datetime.timedelta(hours=7))
                        waktu_rekap = datetime.datetime.now(tz_wib).strftime("%Y-%m-%d %H:%M:%S") if auto_time else manual_date.strftime("%Y-%m-%d")
                        
                        df_to_save = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
                        
                        # V11.8 FIX: Logika Eksekusi Smart Filter PO Kosong
                        if filter_po_kosong:
                            df_to_save = df_to_save[df_to_save['PO'].astype(str).str.strip() != ""]
                            df_to_save = df_to_save[df_to_save['PO'].astype(str).str.strip() != "-"]
                        
                        client = get_gspread_client()
                        sheet_dash = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD))
                        sheet_sandbox = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_SANDBOX))
                        
                        data_to_push = []
                        for _, r in df_to_save.iterrows():
                            info = mapping_master_info.get(r['NAMA_BAKU'], {})
                            if r['NAMA_BAKU'] != "⚠️ BARANG BARU":
                                kat_final = info.get('KATEGORI', '-')
                                det_kat_final = info.get('DETAIL KATEGORI', '-')
                            else:
                                kat_final = str(r.get('KATEGORI', '-')).strip().upper()
                                det_kat_final = str(r.get('DETAIL KATEGORI', '-')).strip().upper()
                            
                            data_to_push.append([
                                r['UNIT'], r['PO'], r['TANGGAL'], r['VENDOR'], "RP", 
                                r['ITEM_ASLI'], r['NAMA_BAKU'], r['QTY'], 
                                info.get('SATUAN', '-'), r['HARGA'], 
                                kat_final, det_kat_final, r['SKU'],
                                waktu_rekap 
                            ])
                        
                        if data_to_push:
                            sheet_dash.append_rows(pd.DataFrame(data_to_push).fillna("-").values.tolist())
                            sheet_sandbox.append_rows(pd.DataFrame(data_to_push).fillna("-").values.tolist())
                            
                            st.balloons()
                            st.success(f"🔥 BERHASIL! {len(data_to_push)} Data (dengan PO Valid) terduplikasi aman di Sheet 3 & Sheet 4."); 
                            del st.session_state['holding_draft']; time.sleep(2); st.rerun()
                        else:
                            st.warning("Tidak ada data yang disimpan (Semua barang PO-nya kosong atau sudah dicentang 'Bukan Scope').")
                            
                except Exception as e: st.error(f"Simpan Gagal: {e}")
        with c2:
            if st.button("❌ Batalkan Semua", use_container_width=True): del st.session_state['holding_draft']; st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            df_to_export = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
            
            # V11.8 FIX: Export Excel juga mengikuti Smart Filter
            if filter_po_kosong:
                df_to_export = df_to_export[df_to_export['PO'].astype(str).str.strip() != ""]
                df_to_export = df_to_export[df_to_export['PO'].astype(str).str.strip() != "-"]
                
            if not df_to_export.empty:
                export_data = []
                tz_wib = datetime.timezone(datetime.timedelta(hours=7))
                waktu_sekarang = datetime.datetime.now(tz_wib)
                tgl_rekap_export = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S") if auto_time else manual_date.strftime("%Y-%m-%d")

                for _, r in df_to_export.iterrows():
                    info = mapping_master_info.get(r['NAMA_BAKU'], {})
                    if r['NAMA_BAKU'] != "⚠️ BARANG BARU":
                        kat_final = info.get('KATEGORI', '-')
                        det_kat_final = info.get('DETAIL KATEGORI', '-')
                    else:
                        kat_final = str(r.get('KATEGORI', '-')).strip().upper()
                        det_kat_final = str(r.get('DETAIL KATEGORI', '-')).strip().upper()
                    
                    export_data.append({
                        'UNIT KERJA': r['UNIT'], 'NOMOR PO': r['PO'], 'TANGGAL': r['TANGGAL'], 'NAMA VENDOR': r['VENDOR'], 
                        'MATA UANG': "RP", 'NAMA ITEM ASLI (KOTOR)': r['ITEM_ASLI'], 'NAMA BARANG (BAKU)': r['NAMA_BAKU'], 
                        'QTY': r['QTY'], 'UOM': info.get('SATUAN', '-'), 'HARGA SATUAN': r['HARGA'], 
                        'KATEGORI': kat_final, 'DETAIL KATEGORI': det_kat_final, 'SKU': r['SKU'],
                        'TANGGAL REKAP': tgl_rekap_export
                    })
                
                df_final_export = pd.DataFrame(export_data).fillna("-")
                buffer_clean = io.BytesIO()
                with pd.ExcelWriter(buffer_clean, engine='openpyxl') as writer:
                    df_final_export.to_excel(writer, index=False, sheet_name='Data Bersih')
                excel_clean_data = buffer_clean.getvalue()
                
                st.download_button(
                    label="📥 Download Hasil Pembersihan (Excel Rapi)", 
                    data=excel_clean_data, 
                    file_name=f"Data_Bersih_Holding_{datetime.date.today()}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Gagal menyiapkan tombol download: {e}")

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
                harga_live = harga_data.get('harga', 0)
                tgl_live = harga_data.get('tanggal', '-')
                res_list.append({"Match": f"{m[1]}%", "Nama Baku": baku, "SKU": info.get('NOMOR SKU', '-'), "Kategori": info.get('KATEGORI', '-'), "Est. Harga Live": format_rupiah(harga_live), "Tgl PO Terakhir": tgl_live})
        st.dataframe(pd.DataFrame(res_list), use_container_width=True)

# ==========================================
# MENU 3: E-CATALOG & STUDIO GAMBAR
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio (Update Gambar)"])
    
    with t_cat:
        col_s, col_f, col_sort = st.columns([2, 1, 1])
        with col_s: search_cat = st.text_input("🔍 Cari Produk:", placeholder="Ketik nama atau SKU...")
        with col_f:
            list_kat = ["Semua Kategori"] + sorted([k for k in df_master_clean['KATEGORI'].unique() if str(k).strip() != "" and str(k).strip() != "nan"])
            filter_cat = st.selectbox("📁 Filter Kategori:", list_kat)
        with col_sort:
            sort_by = st.selectbox("⬇️ Urutkan Berdasarkan:", ["Nama (A-Z)", "Nama (Z-A)"])

        missing_only = st.checkbox("⚠️ Tampilkan HANYA barang tanpa gambar (Missing Assets)")

        df_show = df_master_clean.copy()
        
        if filter_cat != "Semua Kategori": df_show = df_show[df_show['KATEGORI'] == filter_cat]
        if search_cat: df_show = df_show[df_show['NAMA BAKU'].astype(str).str.contains(search_cat, case=False) | df_show['NOMOR SKU'].astype(str).str.contains(search_cat, case=False)]
        if missing_only: df_show = df_show[df_show['LINK GAMBAR'].isna() | (df_show['LINK GAMBAR'] == '')]
        
        if sort_by == "Nama (A-Z)": df_show = df_show.sort_values(by='NAMA BAKU', ascending=True)
        elif sort_by == "Nama (Z-A)": df_show = df_show.sort_values(by='NAMA BAKU', ascending=False)
        
        st.markdown("---")
        
        if df_show.empty: 
            st.warning("Data tidak ditemukan.")
        else:
            html_content = f"<h2>Katalog Produk PT Panca Budi ({filter_cat})</h2><table border='1' style='border-collapse: collapse; width: 100%;'><tr><th>SKU</th><th>NAMA BARANG</th><th>HARGA TERBARU</th></tr>"
            for _, r in df_show.iterrows():
                harga_data = latest_price_map.get(str(r.get('NAMA BAKU','')).strip().upper(), {})
                harga_live_print = harga_data.get('harga', 0)
                tgl_live_print = harga_data.get('tanggal', '-')
                html_content += f"<tr><td>{r.get('NOMOR SKU', '-')}</td><td>{r.get('NAMA BAKU', '-')}</td><td>{format_rupiah(harga_live_print)} <small>({tgl_live_print})</small></td></tr>"
            html_content += "</table><br><p>Dicetak dari Sistem ERP Purchasing</p>"
            
            st.download_button("🖨️ Download Katalog PDF (HTML Print)", data=html_content, file_name=f"Katalog_{datetime.date.today()}.html", mime="text/html")
            st.write("")

            items_per_page = 20
            total_pages = max(1, (len(df_show) - 1) // items_per_page + 1)
            
            col_page, col_info = st.columns([1, 4])
            with col_page: page_number = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
            with col_info: st.write(f"Menampilkan halaman {page_number} dari {total_pages} (Total {len(df_show)} Produk)")
            
            start_idx = (page_number - 1) * items_per_page
            df_page = df_show.iloc[start_idx : start_idx + items_per_page]

            cols = st.columns(4)
            for idx, (_, row) in enumerate(df_page.iterrows()): 
                with cols[idx % 4]:
                    baku = row['NAMA BAKU']
                    
                    harga_data = latest_price_map.get(str(baku).strip().upper(), {})
                    harga_live = harga_data.get('harga', None)
                    tgl_live = harga_data.get('tanggal', '-')
                    
                    raw_link = str(row.get('LINK GAMBAR', '')).strip()
                    img_url = process_image_url(raw_link) 
                    
                    if img_url:
                        img_element = f"<img src='{img_url}' style='width:100%; height:160px; object-fit:contain; border-radius:8px; margin-bottom:12px;'>"
                    else:
                        img_element = f"<div style='background-color:#F1F5F9; height:160px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;'><span style='color:#94A3B8; font-weight:600;'>No Image Asset</span></div>"
                    
                    harga_display = f"<span style='color:#047857; font-weight:800; font-size:16px;'>{format_rupiah(harga_live)}</span><br><span style='font-size:9px; color:#64748B;'>Tgl PO Terakhir: {tgl_live}</span>" if harga_live else "<span style='color:#EF4444; font-size:11px; font-weight:600;'>Belum ada histori harga</span>"
                    badge_live = "<span style='background:#ECFDF5; border: 1px solid #A7F3D0; color:#047857; font-size:9px; padding:3px 8px; border-radius:12px; font-weight:700;'>LIVE PRICE</span>" if harga_live else ""

                    card_html = f"""
                    <div style='background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: 0.3s;'>
                        {img_element}
                        <h5 style='margin-top:0px; font-size:14px; font-weight:700; color:#0F172A; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;'>{baku}</h5>
                        <p style='font-size:11px; color:#64748B; margin:4px 0;'>SKU: {row.get('NOMOR SKU', '-')}</p>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px;'>
                            <div>{harga_display}</div>
                            <div>{badge_live}</div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

    with t_studio:
        if st.session_state.get('role') != "ADMIN":
            st.error("⛔ Akses Ditolak! Hanya jabatan ADMIN yang dapat menyuntikkan atau merubah Asset Gambar.")
        else:
            st.write("### 📸 Asset Studio (Injeksi Gambar)")
            
            if 'LINK GAMBAR' not in df_master.columns: df_master['LINK GAMBAR'] = ""
            
            studio_kat = st.selectbox("1. Filter Kategori Barang:", ["Semua Kategori"] + sorted([k for k in df_master_clean['KATEGORI'].unique() if str(k).strip() != "" and str(k).strip() != "nan"]))
            
            df_studio = df_master_clean.copy()
            if studio_kat != "Semua Kategori": df_studio = df_studio[df_studio['KATEGORI'] == studio_kat]
            
            all_unique_items = df_studio['NAMA BAKU'].tolist()
            
            if not all_unique_items: st.warning("Kategori ini Kosong.")
            else:
                barang_pilih = st.selectbox("2. Pilih Nama Produk yang Mau Diubah/Ditambah Gambarnya:", all_unique_items)
                
                current_row = df_studio[df_studio['NAMA BAKU'] == barang_pilih].iloc[-1]
                current_link = str(current_row.get('LINK GAMBAR', '')).strip()
                
                if current_link and current_link.lower() not in ['nan', 'none', '']:
                    st.warning("⚠️ **Barang ini sudah memiliki gambar.** Jika *upload* baru, gambar lama tertimpa.")
                    curr_preview = process_image_url(current_link)
                    if curr_preview: st.image(curr_preview, width=150, caption="Gambar Saat Ini")
                else:
                    st.success("✅ Barang ini belum memiliki gambar.")

                query_google = urllib.parse.quote(barang_pilih + " industri sparepart")
                st.markdown(f"<a href='https://www.google.com/search?tbm=isch&q={query_google}' target='_blank'><button style='background-color:#4285F4; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold; margin-bottom:15px; margin-top:5px;'>🔍 Cari '{barang_pilih}' di Google</button></a>", unsafe_allow_html=True)

                st.write("---")
                st.write("**OPSI 1: Paste Link URL Gambar (Cara Lama)**")
                link_input = st.text_input("Paste URL Link Gambar di sini:")
                
                st.write("**OPSI 2: Paste Gambar Fisik Langsung (Cara Cepat Ctrl+V)**")
                
                st.markdown("""
                <div style='background-color: #F0FDF4; border: 2px dashed #34D399; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;'>
                    <h4 style='color: #065F46; margin-top: 0;'>👇 AREA PASTE (CTRL + V) 👇</h4>
                    <p style='color: #047857; font-size: 14px; margin-bottom: 0;'><b>JANGAN KLIK TOMBOL UPLOAD/BROWSE!</b><br>Cukup klik KIRI sekali di kotak putih/abu-abu bawah ini, lalu langsung tekan <b>Ctrl + V</b>.</p>
                </div>
                """, unsafe_allow_html=True)
                
                file_upload = st.file_uploader("Area Paste", type=['png', 'jpg', 'jpeg', 'webp'], label_visibility="collapsed")

                img_to_save = None

                if file_upload is not None:
                    b64_string = image_to_base64(file_upload)
                    if b64_string:
                        st.image(file_upload, width=300, caption="Preview Upload (Siap Disimpan)")
                        img_to_save = b64_string
                    else:
                        st.error("Gagal membaca file gambar.")
                
                elif link_input:
                    if "shopee.co.id/" in link_input and "cf.shopee.co.id" not in link_input:
                        st.error("⚠️ Oops! Ini link Halaman Produk Shopee. Silakan 'Copy Image Address'.")
                    elif "tokopedia.com/" in link_input and "images.tokopedia.net" not in link_input:
                        st.error("⚠️ Oops! Ini link Halaman Produk Tokopedia. Silakan 'Copy Image Address'.")
                    else:
                        img_preview = process_image_url(link_input)
                        if img_preview:
                            try:
                                st.image(img_preview, width=300, caption="Preview Link (Siap Disimpan)")
                                img_to_save = link_input
                            except Exception:
                                st.warning("⚠️ Link tidak valid atau tidak bisa dibuka.")

                if img_to_save:
                    if st.button("💾 Simpan Gambar ke Database", type="primary"):
                        try:
                            with st.spinner("Membungkus data dan menembakkan ke Server Google..."):
                                client = get_gspread_client()
                                sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                                
                                all_data = sheet_master.get_all_values()
                                headers_upper = [str(h).strip().upper() for h in all_data[0]]
                                
                                if 'LINK GAMBAR' in headers_upper:
                                    col_link_idx = headers_upper.index('LINK GAMBAR') + 1 
                                    col_letter = col_num_to_letter(col_link_idx)
                                    
                                    matching_indices = df_master[df_master['NAMA BAKU'].astype(str).str.strip().str.upper() == barang_pilih.strip().upper()].index
                                    
                                    matching_rows = [idx + 2 for idx in matching_indices]
                                    
                                    if matching_rows:
                                        batch_data = []
                                        for r_idx in matching_rows:
                                            batch_data.append({
                                                'range': f"{col_letter}{r_idx}",
                                                'values': [[img_to_save]]
                                            })
                                            
                                        sheet_master.batch_update(batch_data)
                                            
                                        st.success(f"✅ Success! Gambar berhasil ditanam di {len(matching_rows)} histori transaksi.")
                                        time.sleep(1.5)
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("Barang tidak ditemukan di database.")
                                else:
                                    st.error("Kolom 'LINK GAMBAR' belum ada di baris pertama Master Anda.")
                        except Exception as e:
                            st.error(f"Error Database (Coba muat ulang halaman): {e}")

# ==========================================
# MENU 4: DATABASE VENDOR
# ==========================================
elif menu == "Database Vendor":
    st.markdown("<h2>🏢 Supplier Directory</h2>", unsafe_allow_html=True)
    keyword = st.text_input("Cari Vendor / PIC / Item:")
    
    try:
        df_v = load_data(GID_VENDOR)
        if not df_v.empty:
            df_v.columns = df_v.columns.str.strip().str.upper()
            if keyword:
                res = df_v[df_v.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)]
            else:
                res = df_v.head(100)
                
            for _, v in res.iterrows():
                with st.expander(f"🏢 {v.get('NAMA VENDOR', '-')} | Cat: {v.get('KATEGORI', '-')} | Level: {v.get('GRUP', '-')} "):
                    st.write(f"**Contact Person:** {v.get('PIC', '-')} 📞 {v.get('KONTAK', '-')}")
                    st.write(f"**Location Address:** {v.get('ALAMAT', '-')}")
        else:
            st.warning("Data Vendor Kosong di Spreadsheet.")
    except: 
        st.warning("Database Connection Error.")

# ==========================================
# MENU 5: DASHBOARD LAPORAN (EXECUTIVE FILTER)
# ==========================================
elif menu == "Dashboard Laporan":
    st.markdown("<h2>📊 Procurement Intelligence & Forecasting</h2>", unsafe_allow_html=True)
    
    try:
        client = get_gspread_client()
        data_dash = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD)).get_all_values()
        df_v = load_data(GID_VENDOR); df_v.columns = df_v.columns.str.strip().str.upper()
        
        if len(data_dash) > 1:
            df_d = pd.DataFrame(data_dash[1:], columns=data_dash[0])
            df_d.columns = df_d.columns.str.strip().str.upper()
            
            c_po = next((c for c in df_d.columns if 'PO' in c or 'BUKTI' in c), None)
            c_unit = next((c for c in df_d.columns if 'UNIT' in c or 'GRUP' in c), None)
            c_harga = next((c for c in df_d.columns if 'HARGA' in c), None)
            c_baku = next((c for c in df_d.columns if 'BAKU' in c), None)
            c_tgl = next((c for c in df_d.columns if ('TANGGAL' in c or 'TGL' in c or 'DATE' in c) and 'REKAP' not in c), None)
            
            df_d['H_NUM'] = df_d[c_harga].apply(parse_harga)
            df_d['Q_NUM'] = pd.to_numeric(df_d['QTY'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            df_d['TOTAL'] = df_d['H_NUM'] * df_d['Q_NUM']
            
            df_d['DATE_CLEAN'] = pd.to_datetime(df_d[c_tgl], errors='coerce')
            df_d = df_d.dropna(subset=['DATE_CLEAN'])
            
            if not df_d.empty:
                st.markdown("<h3 style='color:#0F172A; font-size:18px; margin-top:10px;'>🎛️ Executive Filter Panel</h3>", unsafe_allow_html=True)
                
                min_date = df_d['DATE_CLEAN'].min().date()
                max_date = df_d['DATE_CLEAN'].max().date()
                today = datetime.date.today()

                if 'start_date' not in st.session_state: st.session_state.start_date = min_date
                if 'end_date' not in st.session_state: st.session_state.end_date = max_date

                c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
                if c_btn1.button("♾️ Semua Waktu", use_container_width=True):
                    st.session_state.start_date = min_date; st.session_state.end_date = max_date; st.rerun()
                if c_btn2.button("📅 Tahun Ini", use_container_width=True):
                    st.session_state.start_date = datetime.date(today.year, 1, 1); st.session_state.end_date = today; st.rerun()
                if c_btn3.button("📆 Bulan Ini", use_container_width=True):
                    st.session_state.start_date = today.replace(day=1); st.session_state.end_date = today; st.rerun()
                if c_btn4.button("🗓️ Minggu Ini", use_container_width=True):
                    st.session_state.start_date = today - datetime.timedelta(days=today.weekday()); st.session_state.end_date = today; st.rerun()

                c_date, c_fac, c_export = st.columns([1.5, 1.5, 1])
                with c_date:
                    date_range = st.date_input("Pilih Rentang Tanggal:", value=(st.session_state.start_date, st.session_state.end_date))
                with c_fac:
                    list_unit = ["All Facilities"] + sorted([u for u in df_d[c_unit].unique() if str(u).strip() != ""])
                    filter_unit = st.selectbox("Pilih Lokasi Pabrik:", list_unit)

                if len(date_range) == 2:
                    start_dt, end_dt = date_range
                    df_filtered = df_d[(df_d['DATE_CLEAN'].dt.date >= start_dt) & (df_d['DATE_CLEAN'].dt.date <= end_dt)]
                else: df_filtered = df_d
                
                if filter_unit != "All Facilities":
                    df_filtered = df_filtered[df_filtered[c_unit] == filter_unit]
                
                with c_export:
                    st.write("") 
                    st.write("")
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_to_export = df_filtered.drop(columns=['H_NUM', 'Q_NUM', 'DATE_CLEAN'], errors='ignore')
                        df_to_export.to_excel(writer, index=False, sheet_name='Laporan Transaksi')
                    excel_data = buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Download Excel (.xlsx)", 
                        data=excel_data, 
                        file_name=f"Laporan_Holding_{filter_unit}_{st.session_state.start_date}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        use_container_width=True
                    )

                st.markdown("---")
                
                if df_filtered.empty:
                    st.warning("⚠️ Tidak ada transaksi yang ditemukan pada rentang tanggal dan pabrik tersebut.")
                else:
                    tab_summary, tab_item = st.tabs(["🌐 Corporate Overview", "🔎 Item Analytics & AI Forecast"])
                    
                    with tab_summary:
                        st.write("") 
                        col1, col2, col3 = st.columns(3)
                        with col1: st.markdown(create_metric_card("fa-solid fa-sack-dollar", "Total Procurement Value", format_rupiah(df_filtered['TOTAL'].sum())), unsafe_allow_html=True)
                        with col2: st.markdown(create_metric_card("fa-solid fa-file-invoice", "PO Transactions", f"{df_filtered[c_po].replace('', pd.NA).dropna().nunique()}"), unsafe_allow_html=True)
                        with col3: st.markdown(create_metric_card("fa-solid fa-industry", "Active Supply Facilities", f"{df_filtered[c_unit].nunique()}"), unsafe_allow_html=True)
                        st.write("")
                        st.write("")
                        
                        c_a, c_b = st.columns([1, 1.5])
                        with c_a:
                            st.markdown("<h4 style='font-size:16px; color:#334155; margin-bottom:15px;'>Budget Distribution</h4>", unsafe_allow_html=True)
                            if filter_unit == "All Facilities":
                                rekap_u = df_filtered.groupby(c_unit)['TOTAL'].sum().reset_index()
                                rekap_u = rekap_u[rekap_u[c_unit].str.strip() != ""] 
                                fig_pie = px.pie(rekap_u, names=c_unit, values='TOTAL', hole=0.6, color_discrete_sequence=['#047857', '#10B981', '#34D399', '#6EE7B7'])
                                fig_pie.update_traces(textposition='inside', textinfo='percent')
                                fig_pie.update_layout(font=dict(color='#0F172A'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                                st.plotly_chart(fig_pie, use_container_width=True, theme=None)
                            else: st.info(f"Viewing specialized data for **{filter_unit}**.")

                        with c_b:
                            st.markdown("<h4 style='font-size:16px; color:#334155; margin-bottom:15px;'>Top Procurement Items</h4>", unsafe_allow_html=True)
                            df_valid = df_filtered[~df_filtered[c_baku].str.contains('CEK MANUAL|BARANG BARU', case=False, na=False)]
                            if not df_valid.empty:
                                df_valid = df_valid[df_valid[c_baku].str.strip() != ""]
                                top_i = df_valid.groupby(c_baku)[c_po].nunique().reset_index()
                                top_i.columns = ['Nama Barang', 'Jumlah PO']
                                top_i = top_i.sort_values(by='Jumlah PO', ascending=False).head(8)
                                fig_bar = px.bar(top_i, x='Jumlah PO', y='Nama Barang', orientation='h', text='Jumlah PO', color_discrete_sequence=['#047857'])
                                fig_bar.update_layout(font=dict(color='#0F172A'), yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_bar, use_container_width=True, theme=None)
                    
                    with tab_item:
                        list_barang_histori = df_filtered.drop_duplicates(subset=[c_baku]).sort_values(by=c_baku)[c_baku].tolist()
                        barang_pilih = st.multiselect("Search Product Intelligence (Bisa pilih lebih dari 1 untuk perbandingan):", list_barang_histori, placeholder="Pilih barang untuk dianalisa...")
                        
                        if barang_pilih:
                            df_item_histori = df_filtered[df_filtered[c_baku].isin(barang_pilih)].sort_values(by='DATE_CLEAN')

                            if len(barang_pilih) == 1:
                                item_tunggal = barang_pilih[0]
                                info_master = df_master_clean[df_master_clean['NAMA BAKU'] == item_tunggal].tail(1)
                                kat_item = "NAN"
                                if not info_master.empty: kat_item = str(info_master.iloc[0].get('KATEGORI', '')).upper()

                                v_histori = sorted([str(v).strip() for v in df_item_histori['VENDOR'].unique() if str(v).strip() not in ['', '-', 'nan']])
                                v_database = []
                                if kat_item != "NAN" and not df_v.empty:
                                    v_match = df_v[df_v['KATEGORI'].astype(str).str.contains(kat_item, case=False, na=False)]
                                    v_database = sorted(v_match['NAMA VENDOR'].unique().tolist())

                                st.markdown("<br>", unsafe_allow_html=True)
                                c_img, c_meta = st.columns([1, 2.5])
                                with c_img:
                                    if not info_master.empty:
                                        img_url = process_image_url(str(info_master.iloc[0].get('LINK GAMBAR', '')).strip())
                                        if img_url: st.markdown(f"<div style='border:1px solid #E2E8F0; border-radius:12px; padding:10px; background:white;'><img src='{img_url}' width='100%' style='border-radius:8px;'></div>", unsafe_allow_html=True)
                                        else: st.info("🚫 No Asset")
                                with c_meta:
                                    st.markdown(f"<h3 style='margin-top:0; color:#0F172A;'>{item_tunggal}</h3>", unsafe_allow_html=True)
                                    if not info_master.empty:
                                        row_m = info_master.iloc[0]
                                        st.markdown(f"<p style='color:#64748B; font-weight:600; margin-bottom:15px;'>SKU: <span style='color:#047857;'>{row_m.get('NOMOR SKU', '-')}</span> &nbsp;|&nbsp; CAT: {kat_item} &nbsp;|&nbsp; UOM: {row_m.get('SATUAN', '-')}</p>", unsafe_allow_html=True)
                                        st.markdown("**🏭 Histori Supplier (Telah Digunakan):**")
                                        st.markdown(f"<div style='background-color:#F8FAFC; border:1px solid #E2E8F0; padding:10px; border-radius:8px; font-size:14px;'>{', '.join(v_histori) if v_histori else 'Belum ada transaksi'}</div>", unsafe_allow_html=True)
                                        st.markdown("<br>**💡 Rekomendasi Supplier (Database Match):**", unsafe_allow_html=True)
                                        st.markdown(f"<div style='background-color:#ECFDF5; border:1px solid #A7F3D0; padding:10px; border-radius:8px; font-size:14px; color:#065F46;'>{', '.join(v_database) if v_database else 'Tidak ada referensi di database'}</div>", unsafe_allow_html=True)
                                
                                st.markdown("<hr style='border:1px solid #E2E8F0; margin: 30px 0;'>", unsafe_allow_html=True)
                                
                                if not df_item_histori.empty:
                                    m1, m2, m3, m4 = st.columns(4)
                                    with m1: st.markdown(create_metric_card("fa-solid fa-money-bill-wave", "Item TCO (Total Cost)", format_rupiah(df_item_histori['TOTAL'].sum())), unsafe_allow_html=True)
                                    with m2: st.markdown(create_metric_card("fa-solid fa-cart-shopping", "Purchase Frequency", f"{df_item_histori[c_po].nunique()} Orders"), unsafe_allow_html=True)
                                    with m3: st.markdown(create_metric_card("fa-solid fa-tag", "Average Unit Price", format_rupiah(df_item_histori['H_NUM'].mean())), unsafe_allow_html=True)
                                    with m4: st.markdown(create_metric_card("fa-solid fa-handshake", "Supplier Count", f"{len(v_histori)} Vendors"), unsafe_allow_html=True)

                                    st.write("")
                                    st.write("")
                                    g_harga, g_qty = st.columns(2)
                                    with g_harga:
                                        fig_harga = px.line(df_item_histori, x='DATE_CLEAN', y='H_NUM', title="Price Volatility Trend", markers=True, color_discrete_sequence=['#F59E0B'])
                                        fig_harga.update_layout(font=dict(color='#0F172A'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Price (IDR)")
                                        st.plotly_chart(fig_harga, use_container_width=True, theme=None)
                                    with g_qty:
                                        df_monthly = df_item_histori.groupby(pd.Grouper(key='DATE_CLEAN', freq='ME'))['Q_NUM'].sum().reset_index()
                                        fig_qty = px.bar(df_monthly, x='DATE_CLEAN', y='Q_NUM', title="Procurement Volume by Month", color_discrete_sequence=['#3B82F6'])
                                        fig_qty.update_layout(font=dict(color='#0F172A'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Quantity")
                                        st.plotly_chart(fig_qty, use_container_width=True, theme=None)
                                    
                                    st.markdown("<hr style='border:1px solid #E2E8F0; margin: 30px 0;'>", unsafe_allow_html=True)
                                    st.markdown("<h3 style='color:#0F172A;'>🔮 AI Forecasting & Budget Projection</h3>", unsafe_allow_html=True)
                                    
                                    df_monthly_fc = df_item_histori.groupby(pd.Grouper(key='DATE_CLEAN', freq='ME'))['Q_NUM'].sum().reset_index()
                                    if len(df_monthly_fc) >= 1:
                                        avg_qty_per_month = df_monthly_fc['Q_NUM'].mean()
                                        latest_price = df_item_histori.sort_values(by='DATE_CLEAN').iloc[-1]['H_NUM']
                                        est_budget = avg_qty_per_month * latest_price
                                        
                                        uom = row_m.get('SATUAN', '-') if not info_master.empty else "Pcs"
                                        
                                        c_fc1, c_fc2, c_fc3 = st.columns(3)
                                        with c_fc1: st.markdown(create_metric_card("fa-solid fa-chart-line", "Rata-rata Kebutuhan / Bulan", f"{avg_qty_per_month:.0f} {uom}"), unsafe_allow_html=True)
                                        with c_fc2: st.markdown(create_metric_card("fa-solid fa-tags", "Patokan Harga Terakhir", format_rupiah(latest_price)), unsafe_allow_html=True)
                                        with c_fc3: st.markdown(create_metric_card("fa-solid fa-vault", "Estimasi Budget Bulan Depan", format_rupiah(est_budget)), unsafe_allow_html=True)
                                        st.write("")
                                        
                                        vendor_saran = v_histori[:2] if len(v_histori) > 0 else ["Vendor Baru"]
                                        str_vendor = " atau ".join(vendor_saran)
                                        
                                        st.info(f"💡 **Insight Manajerial:** Berdasarkan histori pada rentang tanggal terpilih, Holding diperkirakan akan membutuhkan sekitar **{avg_qty_per_month:.0f} {uom}** untuk item **{item_tunggal}** di bulan depan. Siapkan budget sekitar **{format_rupiah(est_budget)}** dan pertimbangkan untuk langsung melakukan negosiasi kuantiti bulanan dengan **{str_vendor}** untuk mendapatkan harga terbaik.")
                                    else:
                                        st.warning("Data histori belum cukup untuk melakukan kalkulasi Forecasting.")

                                    st.markdown("<br><h4 style='font-size:16px; color:#334155; margin-bottom:10px;'>Transaction Ledger</h4>", unsafe_allow_html=True)
                                    df_table = df_item_histori[[c_tgl, c_po, c_unit, 'VENDOR', 'QTY', 'H_NUM', 'TOTAL']].copy()
                                    df_table['H_NUM'] = df_table['H_NUM'].map(format_rupiah)
                                    df_table['TOTAL'] = df_table['TOTAL'].map(format_rupiah)
                                    st.dataframe(df_table, use_container_width=True, hide_index=True)

                            else:
                                st.markdown("<br><h3>⚖️ Multi-Item Comparative Analysis</h3>", unsafe_allow_html=True)
                                st.markdown("<hr style='border:1px solid #E2E8F0; margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
                                
                                if not df_item_histori.empty:
                                    m1, m2, m3, m4 = st.columns(4)
                                    with m1: st.markdown(create_metric_card("fa-solid fa-coins", "Combined TCO", format_rupiah(df_item_histori['TOTAL'].sum())), unsafe_allow_html=True)
                                    with m2: st.markdown(create_metric_card("fa-solid fa-cart-flatbed", "Total Transactions", f"{df_item_histori[c_po].nunique()} Orders"), unsafe_allow_html=True)
                                    with m3: st.markdown(create_metric_card("fa-solid fa-boxes-stacked", "Items Compared", f"{len(barang_pilih)} Items"), unsafe_allow_html=True)
                                    with m4: st.markdown(create_metric_card("fa-solid fa-users", "Total Vendors Involved", f"{df_item_histori['VENDOR'].nunique()} Vendors"), unsafe_allow_html=True)

                                    st.write("")
                                    st.write("")
                                    g_harga, g_qty = st.columns(2)
                                    with g_harga:
                                        fig_harga = px.line(df_item_histori, x='DATE_CLEAN', y='H_NUM', color=c_baku, title="Price Volatility Comparison", markers=True)
                                        fig_harga.update_layout(font=dict(color='#0F172A'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Price (IDR)", legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=""))
                                        st.plotly_chart(fig_harga, use_container_width=True, theme=None)
                                    with g_qty:
                                        df_monthly = df_item_histori.groupby([pd.Grouper(key='DATE_CLEAN', freq='ME'), c_baku])['Q_NUM'].sum().reset_index()
                                        fig_qty = px.bar(df_monthly, x='DATE_CLEAN', y='Q_NUM', color=c_baku, barmode='group', title="Volume Comparison by Month")
                                        fig_qty.update_layout(font=dict(color='#0F172A'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Quantity", legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=""))
                                        st.plotly_chart(fig_qty, use_container_width=True, theme=None)
                                    
                                    st.markdown("<h4 style='font-size:16px; color:#334155; margin-bottom:10px;'>Combined Transaction Ledger</h4>", unsafe_allow_html=True)
                                    df_table = df_item_histori[[c_tgl, c_po, c_baku, c_unit, 'VENDOR', 'QTY', 'H_NUM', 'TOTAL']].copy()
                                    df_table.rename(columns={c_baku: 'NAMA BARANG'}, inplace=True)
                                    df_table['H_NUM'] = df_table['H_NUM'].map(format_rupiah)
                                    df_table['TOTAL'] = df_table['TOTAL'].map(format_rupiah)
                                    st.dataframe(df_table, use_container_width=True, hide_index=True)
            else: st.warning("Data Transaksi Kosong di Spreadsheet.")
    except Exception as e: st.error(f"Engine Fault: {e}")

# ==========================================
# MENU 6: MAINTENANCE DATA
# ==========================================
elif menu == "Maintenance Data":
    st.markdown("<h2>🛠️ System Config & SKU Generator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Modul untuk injeksi SKU secara masif dan perawatan data.</p>", unsafe_allow_html=True)
    
    invalid_mask = df_master_clean['NOMOR SKU'].isna() | (df_master_clean['NOMOR SKU'].astype(str).str.strip().str.len() < 10)
    df_missing = df_master_clean[invalid_mask]
    
    if not df_missing.empty:
        st.warning(f"⚠️ Terdeteksi {len(df_missing)} item yang membutuhkan Nomor SKU.")
        
        if st.button("🔄 Generate Preview SKU", type="primary"):
            with st.spinner("Membuat draft SKU..."):
                try:
                    client = get_gspread_client()
                    sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                    all_data = sheet_master.get_all_values()
                    headers = [str(h).strip().upper() for h in all_data[0]]
                    df_m = pd.DataFrame(all_data[1:], columns=headers)
                    
                    c_s = next((c for c in headers if 'SKU' in c), None)
                    c_k = next((c for c in headers if 'KATEGORI' in c and 'DETAIL' not in c), None)
                    c_d = next((c for c in headers if 'DETAIL' in c), None)
                    c_tgl = next((c for c in headers if 'TANGGAL' in c or 'TGL' in c or 'DATE' in c), None) 
                    
                    if c_s and c_k and c_d:
                        preview_data = []
                        for idx, row in df_m.iterrows():
                            val = str(row[c_s]).strip()
                            if len(val) < 10 or val.upper() in ['NAN', 'NONE', 'NULL', '#N/A', '']: 
                                new_sku = generate_new_sku("001", row[c_k], row[c_d], df_m)
                                df_m.at[idx, c_s] = new_sku
                                
                                tgl_val = row[c_tgl] if c_tgl else "-"
                                
                                preview_data.append({
                                    "Baris Excel": idx + 2, 
                                    "TANGGAL": tgl_val,
                                    "NAMA BAKU": row.get('NAMA BAKU', '-'),
                                    "KATEGORI": row[c_k],
                                    "DETAIL KATEGORI": row[c_d],
                                    "SKU BARU": new_sku
                                })
                        
                        st.session_state['draft_sku_df'] = df_m
                        st.session_state['preview_sku_list'] = pd.DataFrame(preview_data)
                except Exception as e:
                    st.error(f"Error: {e}")

        if 'preview_sku_list' in st.session_state:
            st.info("💡 **Silakan review dan edit manual di kolom 'SKU BARU' pada tabel di bawah ini jika diperlukan.**")
            
            edited_preview = st.data_editor(
                st.session_state['preview_sku_list'],
                disabled=["Baris Excel", "NAMA BAKU", "KATEGORI", "DETAIL KATEGORI"],
                use_container_width=True,
                hide_index=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Konfirmasi & Tembak ke Master Data", type="primary", use_container_width=True):
                    with st.spinner("Menimpa ke Google Sheets..."):
                        try:
                            df_full = st.session_state['draft_sku_df']
                            c_s = next((c for c in df_full.columns if 'SKU' in c), None)
                            c_tgl = next((c for c in df_full.columns if 'TANGGAL' in c or 'TGL' in c or 'DATE' in c), None)
                            
                            for _, row in edited_preview.iterrows():
                                excel_idx = row["Baris Excel"] - 2
                                df_full.at[excel_idx, c_s] = row["SKU BARU"]
                                if c_tgl and "TANGGAL" in row:
                                    df_full.at[excel_idx, c_tgl] = row["TANGGAL"]
                                
                            client = get_gspread_client()
                            sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                            sheet_master.clear()
                            sheet_master.update(values=[df_full.columns.tolist()] + df_full.values.tolist())
                            
                            st.success("✔️ Berhasil! Master Data telah diupdate.")
                            del st.session_state['draft_sku_df']
                            del st.session_state['preview_sku_list']
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan: {e}")
            with col2:
                if st.button("❌ Batal", use_container_width=True):
                    del st.session_state['draft_sku_df']
                    del st.session_state['preview_sku_list']
                    st.rerun()
                    
    else: st.success("✔️ Database Sehat. Semua SKU terverifikasi.")

# ==============================================================================
# H. FOOTER SISTEM (LIVE TIMESTAMP)
# ==============================================================================
st.markdown("---")
sync_time = get_sync_time()
st.markdown(
    f"<p style='text-align: center; color: #94A3B8; font-size: 12px; line-height: 1.5;'>"
    f"ERP Purchasing System v11.8 | Proprietary of PT Panca Budi Idaman Tbk | Created with for Raihan Subakti<br>"
    f"<span style='color: #10B981; font-weight: 600;'>🟢 Live Database tersinkronisasi pada: {sync_time}</span>"
    f"</p>", 
    unsafe_allow_html=True
)