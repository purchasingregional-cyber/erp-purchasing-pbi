# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 16.0 (THE SPEEDSTER & MULTI-PLANT HYBRID VERSION)
# Fitur: Ultra Fast Loading, PGP PI Saldo Detector, Auto-Fill PCS, Unlocked Master
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
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp, .main, [data-testid="stAppViewContainer"] { background-color: #F8FAFC !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    [data-testid="stMarkdownContainer"] > p, [data-testid="stText"], label, .stSelectbox label { color: #334155 !important; }
    h1, h2, h3, h4, h5, h6 { color: #0F172A !important; }
    div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; color: #0F172A !important; }
    ul[data-baseweb="menu"] { background-color: #FFFFFF !important; }
    ul[data-baseweb="menu"] li { color: #0F172A !important; }
    div[data-testid="stExpander"] summary p { color: #047857 !important; font-weight: 700 !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
    footer { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    
    .stMetric { padding: 24px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); border: 1px solid rgba(128, 128, 128, 0.2) !important; background-color: transparent !important; transition: transform 0.2s ease-in-out; }
    .stMetric:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    
    div[data-testid="stButton"] button { border-radius: 10px !important; font-weight: 700 !important; letter-spacing: 0.5px !important; padding: 12px 0 !important; transition: all 0.3s ease !important; }
    div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, #064E3B 0%, #047857 100%) !important; color: white !important; border: none !important; box-shadow: 0 4px 6px rgba(4, 120, 87, 0.2) !important; }
    div[data-testid="stButton"] button[kind="primary"]:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 15px rgba(4, 120, 87, 0.3) !important; }
    div[data-testid="stButton"] button[kind="primary"] p { color: #FFFFFF !important; }
    div[data-testid="stButton"] button[kind="secondary"] { background-color: #FFFFFF !important; color: #334155 !important; border: 2px solid #E2E8F0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important; }
    div[data-testid="stButton"] button[kind="secondary"]:hover { background-color: #F8FAFC !important; border-color: #CBD5E1 !important; transform: translateY(-2px) !important; box-shadow: 0 8px 15px rgba(0,0,0,0.05) !important; }
    div[data-testid="stTextInput"] input:focus { border-color: #047857 !important; box-shadow: 0 0 0 4px rgba(4, 120, 87, 0.15) !important; }
    div[data-testid="stForm"] { border: none !important; background: transparent !important; padding: 0 !important; }
    div[data-testid="stExpander"] { border-radius: 12px !important; border: 1px solid #E2E8F0 !important; background-color: #FFFFFF !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; }
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
        months_map = { 'JANUARI': 1, 'FEBRUARI': 2, 'PEBRUARI': 2, 'MARET': 3, 'APRIL': 4, 'MEI': 5, 'JUNI': 6, 'JULI': 7, 'AGUSTUS': 8, 'SEPTEMBER': 9, 'OKTOBER': 10, 'NOVEMBER': 11, 'DESEMBER': 12, 'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MEI': 5, 'JUN': 6, 'JUL': 7, 'AGU': 8, 'SEP': 9, 'OKT': 10, 'NOV': 11, 'DES': 12 }
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
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e: return None

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
                    latest_price_map[str(row[c_baku_h]).strip().upper()] = {
                        'harga': row['PRICE_TEMP'],
                        'tanggal': str(row[c_tgl_h]).strip()
                    }

    df_master['AI_LOOKUP'] = df_master['NAMA BAKU'].astype(str).str.upper()
    if 'NAMA ITEM' in df_master.columns: df_master['AI_LOOKUP'] += " " + df_master['NAMA ITEM'].fillna("").astype(str).str.upper()
        
    search_list = df_master['AI_LOOKUP'].tolist()
    lookup_to_baku_map = dict(zip(df_master['AI_LOOKUP'], df_master['NAMA BAKU']))
    
    df_master_clean = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last').copy()
    mapping_master_info = df_master_clean.set_index('NAMA BAKU').to_dict('index')

except Exception as e:
    st.error(f"⚠️ Gagal Load Database Utama: {e}"); st.stop()

# ==========================================
# 5. SISTEM KEAMANAN LUXURY (2 PINTU LOGIN)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

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
            """)
    
    st.markdown("<div style='margin-bottom: 2.5vh;'></div>", unsafe_allow_html=True)
    col_space1, col_tamu, col_gap, col_admin, col_space2 = st.columns([1.5, 2.5, 0.3, 2.5, 1.5])
    
    with col_tamu:
        st.markdown("""
            <div style="text-align: center; padding: 20px 15px 15px 15px; background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 100%; margin-bottom: 15px;">
                <div style="font-size: 40px; margin-bottom: 10px;">🏢</div>
                <h3 style="color: #0F172A; font-weight: 800; font-size: 18px; margin-bottom: 8px;">Guest Access</h3>
                <p style="color: #64748B; font-size: 12px; line-height: 1.4; margin-bottom: 5px; padding: 0 10px;">Jelajahi E-Catalog, spesifikasi SKU, dan direktori Vendor tanpa otorisasi.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Masuk Sebagai Tamu", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = True; st.session_state['role'] = "VIEWER"; st.session_state['nama'] = "Tamu Pabrik"; st.rerun()

    with col_admin:
        st.markdown("""
            <div style="text-align: center; padding: 20px 15px 15px 15px; background-color: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 16px; box-shadow: 0 4px 6px rgba(4,120,87,0.05); height: 100%; margin-bottom: 15px;">
                <div style="font-size: 40px; margin-bottom: 10px;">🛡️</div>
                <h3 style="color: #064E3B; font-weight: 800; font-size: 18px; margin-bottom: 8px;">Admin Portal</h3>
                <p style="color: #047857; font-size: 12px; line-height: 1.4; margin-bottom: 5px; padding: 0 10px;">Akses penuh ke modul pembersihan data, laporan, dan master maintenance.</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("form_admin"):
            input_pass = st.text_input("Kode Akses", type="password", placeholder="••••••••", label_visibility="collapsed")
            btn_login = st.form_submit_button("Otorisasi Akses", use_container_width=True, type="primary")
            
            if btn_login:
                if input_pass == PASSWORD_ADMIN:
                    st.session_state['logged_in'] = True; st.session_state['role'] = "ADMIN"; st.session_state['nama'] = "Admin Purchasing"; st.rerun()
                else: st.error("❌ Akses Ditolak: Kode Sandi Tidak Valid")
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
    
    if st.button("🔄 Sync Database", use_container_width=True): st.cache_data.clear(); st.rerun()
        
    st.markdown(f"""
        <div style='background-color:#F1F5F9; padding:10px; border-radius:8px; margin-bottom:15px; text-align:center;'>
            <p style='margin:0; font-size:12px; color:#64748B;'>Login sebagai:</p>
            <p style='margin:0; font-weight:800; color:#0F172A; font-size:14px;'>👤 {st.session_state['nama']}</p>
            <span style='background-color:{"#047857" if st.session_state['role'] == "ADMIN" else "#64748B"}; color:white; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;'>{st.session_state['role']}</span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout / Keluar", use_container_width=True):
        st.session_state['logged_in'] = False; st.session_state.clear(); st.rerun()
    st.write("---")
    
    user_role = st.session_state.get('role', 'VIEWER')
    
    if user_role == "ADMIN":
        menu_options = ["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"]
        menu_icons = ["magic", "search", "images", "shop", "bar-chart-line", "tools"]
    else: 
        menu_options = ["Pencarian Barang", "E-Catalog & Studio", "Database Vendor"]
        menu_icons = ["search", "images", "shop"]
    
    menu = option_menu(
        menu_title="", options=menu_options, icons=menu_icons, default_index=0, 
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
                                     ["Plant RA (Auto-Detect Format)", "Plant PGP (Auto-Detect Format)",
                                      "Plant Tangerang (Auto-Detect Format)", "Plant Pemalang (Auto-Detect Format)",
                                      "Plant Solo (Auto-Detect Format)", "Plant PIHC (Rekap Formulir Permintaan)",
                                      "ERP Pusat (Include/Exclude)"])

    with st.form("upload_holding"):
        file_raw = st.file_uploader("📥 Upload Excel Mentah (Drag & Drop di sini):", type=["xlsx", "xls"])
        btn_proses = st.form_submit_button("🚀 Mulai Ekstraksi & AI Matching", type="primary")

    if btn_proses and file_raw:
        try:
            dict_df = pd.read_excel(file_raw, sheet_name=None, header=None)
            extracted_rows = []
            master_format_type = None

            for sheet_name, df_input in dict_df.items():
                format_type = ""
                detected_plant = ""

                if "ERP Pusat" in pilihan_format: format_type = "PUSAT"; detected_plant = "PUSAT"
                elif "PIHC" in pilihan_format: format_type = "NEW"; detected_plant = "PIHC"
                else:
                    if "Plant RA" in pilihan_format: detected_plant = "RA"
                    elif "Plant PGP" in pilihan_format: detected_plant = "PGP"
                    elif "Plant Tangerang" in pilihan_format: detected_plant = "TANGERANG"
                    elif "Plant Pemalang" in pilihan_format: detected_plant = "PEMALANG"
                    elif "Plant Solo" in pilihan_format: detected_plant = "SOLO"
                    
                    is_new = False
                    is_laporan_po = False
                    is_laporan_pi_saldo = False
                    
                    # SCANNER FORMAT MASIF DENGAN KINERJA TINGGI
                    sample_text = " ".join([str(df_input.iloc[r].values).strip().upper() for r in range(min(20, len(df_input)))])
                    
                    if "LAPORAN PO PER PEMASOK" in sample_text: is_laporan_po = True
                    elif "LAPORAN PI SALDO PER PEMASOK" in sample_text: is_laporan_pi_saldo = True
                    elif any(x in sample_text for x in ["REKAP FORMULIR", "PENUNJUKKAN VENDOR", "FORMULIR PERMINTAAN"]): is_new = True
                            
                    if is_laporan_po: format_type = "LAPORAN_PO"
                    elif is_laporan_pi_saldo: format_type = "LAPORAN_PI_SALDO"
                    elif is_new: format_type = "NEW" 
                    else: format_type = "RA_OLD" if "Plant RA" in pilihan_format else "OLD"

                if master_format_type is None: master_format_type = format_type
                else: format_type = master_format_type

                col_nama = col_bahan = col_qty = col_harga = col_vendor = col_po_asli = col_fpb = col_tgl = col_ppn = col_ket = col_sat = -1
                start_idx = 0
                global_date = "-"
                current_solo_month = ""

                # ===================================================================
                # LOGIKA 1: LAPORAN PO (TANGERANG & PEMALANG)
                # ===================================================================
                if format_type == "LAPORAN_PO":
                    col_no_bukti = -1
                    col_t_terima = -1
                    
                    for idx, row in df_input.head(20).iterrows():
                        row_upper = [str(c).strip().upper() for c in row.values]
                        if "NO BUKTI" in row_upper or "T. TERIMA" in row_upper:
                            for i, x in enumerate(row_upper):
                                if "NO BUKTI" in x: col_no_bukti = i
                                elif "T. TERIMA" in x: col_t_terima = i
                                elif "NAMA BARANG" in x: col_nama = i
                                elif "NAMA BAHAN" in x: col_bahan = i
                                elif "QTY1" in x or "QTY" in x: col_qty = i
                                elif "HARGA" in x: col_harga = i
                                elif "PPN" in x and "PPH" not in x: col_ppn = i
                            start_idx = idx; break
                            
                    if col_no_bukti != -1 and (col_nama != -1 or col_bahan != -1):
                        curr_vendor = "CASH / TANPA NAMA"
                        for idx, row in df_input.iloc[start_idx+1:].iterrows():
                            val_list = [str(c).strip() for c in row.values if pd.notna(c) and str(c).strip() != '']
                            if not val_list: continue
                            line_text = " | ".join(val_list).upper()
                            
                            if any(x in line_text for x in ["JUMLAH", "TOTAL", "LAPORAN PO", "HALAMAN"]): continue
                            
                            val_bukti = str(row.values[col_no_bukti]).strip() if pd.notna(row.values[col_no_bukti]) else ""
                            val_tgl = str(row.values[col_t_terima]).strip() if col_t_terima != -1 and pd.notna(row.values[col_t_terima]) else ""
                            
                            # Vendor Auto-Memory
                            if val_bukti != "" and val_tgl == "":
                                if val_bukti.upper() not in ["EUR", "RP", "USD", "IDR"]: curr_vendor = val_bukti
                                continue
                                
                            # Baris Barang
                            if val_bukti != "" and val_tgl != "":
                                item_val1 = str(row.values[col_nama]).strip() if col_nama != -1 and pd.notna(row.values[col_nama]) else ""
                                item_val2 = str(row.values[col_bahan]).strip() if col_bahan != -1 and pd.notna(row.values[col_bahan]) else ""
                                item_name = item_val1 if (item_val1 != "" and "NAN" not in item_val1.upper()) else item_val2
                                    
                                if item_name.lower() in ['', 'nan', 'none']: continue
                                
                                qty_val = parse_numeric(row.values[col_qty]) if col_qty != -1 else 1.0
                                if qty_val is None: qty_val = 1.0
                                
                                prc_val = parse_numeric(row.values[col_harga]) if col_harga != -1 else 0.0
                                if prc_val is None: prc_val = 0.0
                                
                                ppn_num = parse_numeric(row.values[col_ppn]) if col_ppn != -1 else 0.0
                                ppn_val = "PPN" if ppn_num and ppn_num > 0 else "NON PPN"
                                
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": val_bukti, "NO FPB": "", "TANGGAL": val_tgl, "VENDOR": curr_vendor,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "SATUAN": "PCS", "HARGA": prc_val, "STATUS_PPN": ppn_val
                                })

                # ===================================================================
                # LOGIKA 2: LAPORAN PI SALDO (NEW PGP FORMAT DETECTOR) - V16.0 ADDED
                # ===================================================================
                elif format_type == "LAPORAN_PI_SALDO":
                    col_tgl_lpb = -1
                    col_no_po = -1
                    
                    for idx, row in df_input.head(20).iterrows():
                        row_upper = [str(c).strip().upper() for c in row.values]
                        if "TGL.LPB" in row_upper or "NO.PO" in row_upper:
                            for i, x in enumerate(row_upper):
                                if "TGL.LPB" in x: col_tgl_lpb = i
                                elif "NO.PO" in x: col_no_po = i
                                elif "NAMA BARANG" in x: col_nama = i
                                elif "NAMA BAHAN" in x: col_bahan = i
                                elif "QTY1 BELI" in x or "QTY" in x: col_qty = i
                                elif "HARGA" in x: col_harga = i
                                elif "PPN" in x and "PPH" not in x: col_ppn = i
                                elif "SATUA" in x: col_sat = i
                            start_idx = idx; break
                            
                    if col_no_po != -1 and (col_nama != -1 or col_bahan != -1):
                        curr_vendor = "CASH / TANPA NAMA"
                        for idx, row in df_input.iloc[start_idx+1:].iterrows():
                            val_po = str(row.values[col_no_po]).strip() if col_no_po != -1 and pd.notna(row.values[col_no_po]) else ""
                            val_tgl_raw = str(row.values[col_tgl_lpb]).strip() if col_tgl_lpb != -1 and pd.notna(row.values[col_tgl_lpb]) else ""
                            
                            if val_po == "" and val_tgl_raw == "":
                                # Cek Vendor Biru di baris kosong
                                potensi_vendor = [str(c).strip() for c in row.values if pd.notna(c) and str(c).strip() != '']
                                if potensi_vendor:
                                    kandidat = potensi_vendor[0].upper()
                                    if kandidat not in ["EUR", "RP", "USD", "IDR"] and "JUMLAH" not in kandidat and "TOTAL" not in kandidat and "S/D" not in kandidat:
                                        curr_vendor = potensi_vendor[0]
                                continue
                                
                            if val_po != "" and val_tgl_raw != "":
                                item_val1 = str(row.values[col_nama]).strip() if col_nama != -1 and pd.notna(row.values[col_nama]) else ""
                                item_val2 = str(row.values[col_bahan]).strip() if col_bahan != -1 and pd.notna(row.values[col_bahan]) else ""
                                item_name = item_val1 if (item_val1 != "" and "NAN" not in item_val1.upper()) else item_val2
                                if item_name.lower() in ['', 'nan', 'none']: continue
                                
                                tgl_clean = val_tgl_raw.split(" ")[0] if " " in val_tgl_raw else val_tgl_raw
                                qty_val = parse_numeric(row.values[col_qty]) if col_qty != -1 else 1.0
                                sat_val = str(row.values[col_sat]).strip() if col_sat != -1 and pd.notna(row.values[col_sat]) else "PCS"
                                if sat_val.upper() in ['NAN', 'NONE', '']: sat_val = "PCS"
                                prc_val = parse_numeric(row.values[col_harga]) if col_harga != -1 else 0.0
                                ppn_num = parse_numeric(row.values[col_ppn]) if col_ppn != -1 else 0.0
                                ppn_val = "PPN" if ppn_num and ppn_num > 0 else "NON PPN"
                                
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": val_po, "NO FPB": "", "TANGGAL": tgl_clean, "VENDOR": curr_vendor,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val if qty_val else 1.0, "SATUAN": sat_val, "HARGA": prc_val if prc_val else 0.0, "STATUS_PPN": ppn_val
                                })

                # ===================================================================
                # LOGIKA 3: RA OLD
                # ===================================================================
                elif format_type == "RA_OLD":
                    curr_po, curr_tgl, curr_vendor = "", "-", "-"
                    for idx, row in df_input.iterrows():
                        row_upper = [str(c).strip().upper() for c in row.values]
                        if "NAMA BARANG" in row_upper and "HARGA" in row_upper:
                            col_nama = row_upper.index("NAMA BARANG")
                            col_harga = row_upper.index("HARGA")
                            for i, x in enumerate(row_upper):
                                if 'QTY' in x: col_qty = i; break
                            for i, x in enumerate(row_upper):
                                if 'SATUAN' in x: col_sat = i; break
                            break 
                            
                    if col_nama != -1 and col_harga != -1 and col_qty != -1:
                        for idx, row in df_input.iterrows():
                            val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                            if not val_list: continue
                            line_text = " | ".join(val_list).upper()
                            if any(x in line_text for x in ["SUBTOTAL", "TOTAL :", "LAP.PEMBELIAN", "PAGE"]): continue
                            
                            date_m = next((v for v in val_list if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v)), None)
                            po_m = next((v for v in val_list if len(v) >= 4 and re.search(r'\d', v) and not re.match(r'^[-0-9.,]+$', v)), None)
                            
                            if date_m:
                                curr_tgl = date_m.split(" ")[0]; curr_po = po_m if po_m else "" 
                                curr_po = re.sub(r'^[\s:]+', '', curr_po) 
                                potensi_vendor = [v for v in val_list if v != date_m and v != po_m and not re.match(r'^[-0-9.,]+$', v) and "00/01/1900" not in v]
                                curr_vendor = max(potensi_vendor, key=len).replace("00/01/1900", "").strip() if potensi_vendor else "CASH / TANPA NAMA"
                                continue
                                
                            if curr_po != "-": 
                                if col_nama < len(row.values) and col_qty < len(row.values) and col_harga < len(row.values):
                                    item_name = str(row.values[col_nama]).strip()
                                    if item_name.lower() in ['', 'nan', 'none', 'nama barang', 'subtotal', 'subtotal :']: continue
                                    qty_val = parse_numeric(row.values[col_qty])
                                    prc_val = parse_numeric(row.values[col_harga])
                                    sat_val = str(row.values[col_sat]).strip() if col_sat != -1 and pd.notna(row.values[col_sat]) else "PCS"
                                    if sat_val.upper() in ['NAN', 'NONE', '']: sat_val = "PCS"
                                    
                                    if qty_val is not None and prc_val is not None:
                                        extracted_rows.append({
                                            "UNIT KERJA": detected_plant, "NO PO": curr_po, "NO FPB": "", "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                            "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "SATUAN": sat_val, "HARGA": prc_val, "STATUS_PPN": "NON PPN"
                                        })

                # ===================================================================
                # LOGIKA 4: OLD FORMAT (UMUM)
                # ===================================================================
                elif format_type == "OLD":
                    curr_po, curr_tgl, curr_vendor, curr_money = "", "-", "-", "RP"
                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        if not val_list: continue
                        line_text = " | ".join(val_list).upper()
                        if any(x in line_text for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line_text or "EXCLUDE" in line_text:
                            curr_po = val_list[0] if len(val_list) > 0 else ""
                            if curr_po.upper() in ["INCLUDE", "EXCLUDE"]: curr_po = "" 
                            curr_po = re.sub(r'^[\s:]+', '', curr_po) 
                            for c in val_list: 
                                m = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', c)
                                if m: curr_tgl = m.group(0); break
                            potensi_vendor = [v for v in val_list if " - " in v]
                            if potensi_vendor: curr_vendor = potensi_vendor[-1].split(" - ")[-1].strip()
                            else: curr_vendor = "CASH / TANPA NAMA"
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
                                    if len(v_clean) >= 8 and " " not in v_clean and re.search(r'\d', v_clean): continue 
                                    names.append(v_str)
                                item_name = max(names, key=len) if names else "Unknown"
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": curr_po, "NO FPB": "", "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                    "MATA UANG": curr_money, "ITEM_KOTOR": item_name, "QTY": nums[1] if len(nums) > 1 else nums[0], "SATUAN": "PCS", "HARGA": nums[2] if len(nums) > 2 else 0.0, "STATUS_PPN": "NON PPN"
                                })

                # ===================================================================
                # LOGIKA 5: NEW (FORMULIR PERMINTAAN)
                # ===================================================================
                elif format_type == "NEW":
                    for idx_g, row_g in df_input.head(15).iterrows():
                        text_g = " ".join([str(c).strip().upper() for c in row_g.values if pd.notna(c)])
                        m_g = re.search(r'\d{1,2}\s+[A-Z]+\s+\d{4}|\d{1,2}-[A-Z]{3}-?\d{0,4}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', text_g)
                        if m_g and ("TANGGAL" in text_g or "DATE" in text_g or "TGL" in text_g): global_date = m_g.group(0); break

                    for idx, row in df_input.head(30).iterrows():
                        for i, c in enumerate(row.values):
                            if pd.isna(c): continue
                            x_clean = re.sub(r'\s+', ' ', str(c).strip().upper())
                            if ('JENIS BARANG' in x_clean or 'NAMA BARANG' in x_clean) and col_nama == -1: col_nama = i; start_idx = max(start_idx, idx)
                            elif 'HARGA' in x_clean and 'PER' not in x_clean and 'UPDATE' not in x_clean and col_harga == -1: col_harga = i; start_idx = max(start_idx, idx)
                            elif 'VENDOR' in x_clean and 'PENUNJUKKAN' not in x_clean and col_vendor == -1: col_vendor = i; start_idx = max(start_idx, idx)
                            elif ('QTY' in x_clean) and col_qty == -1: col_qty = i
                            elif ('SATUAN' in x_clean) and col_sat == -1: col_sat = i
                            elif ('NO PO' in x_clean or 'NOMOR PO' in x_clean or 'NO. PO' in x_clean) and 'STATUS' not in x_clean: col_po_asli = i
                            elif ('NO FPB' in x_clean or 'NO. FPB' in x_clean or 'NO PB' in x_clean): col_fpb = i
                            elif ('PENYELESAIAN' in x_clean or 'TGL EMAIL' in x_clean or 'DATANG' in x_clean) and col_tgl == -1: col_tgl = i
                            elif ('PPN' in x_clean) and col_ppn == -1: col_ppn = i
                            elif ('KETERANGAN' in x_clean) and col_ket == -1: col_ket = i

                    if col_ppn == -1 and col_ket != -1: col_ppn = col_ket
                                
                    if col_nama != -1 and col_harga != -1:
                        for idx, row in df_input.iloc[start_idx+1:].iterrows():
                            val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                            if not val_list: continue
                            line_text = " | ".join(val_list).upper()
                            
                            if detected_plant == "SOLO":
                                for v in val_list:
                                    v_up = str(v).strip().upper()
                                    if v_up in ['JANUARI', 'FEBRUARI', 'MARET', 'APRIL', 'MEI', 'JUNI', 'JULI', 'AGUSTUS', 'SEPTEMBER', 'OKTOBER', 'NOVEMBER', 'DESEMBER']: current_solo_month = v_up; break
                            if any(x in line_text for x in ["SUBTOTAL", "TOTAL", "REKAP FORMULIR"]): continue
                            
                            try:
                                item_name = str(row.values[col_nama]).strip()
                                if item_name.lower() in ['', 'nan', 'none']: continue
                                qty_val = parse_numeric(row.values[col_qty]) if col_qty != -1 else 1.0
                                sat_val = str(row.values[col_sat]).strip() if col_sat != -1 and pd.notna(row.values[col_sat]) else "PCS"
                                if sat_val.upper() in ['NAN', 'NONE', '']: sat_val = "PCS"
                                prc_val = parse_numeric(row.values[col_harga]) if prc_val is None else 0.0
                                
                                v_str = str(row.values[col_vendor]).strip() if col_vendor != -1 else "-"
                                vendor_val = v_str if v_str.lower() not in ['nan', 'none', ''] else "CASH / TANPA NAMA"
                                po_val = re.sub(r'^[\s:]+', '', str(row.values[col_po_asli]).strip()) if col_po_asli != -1 else ""
                                fpb_val = str(row.values[col_fpb]).strip() if col_fpb != -1 else ""
                                if prc_val == 0 and po_val == "" and fpb_val == "": continue 
                                
                                tgl_val = "-"
                                if col_tgl != -1:
                                    tgl_str = str(row.values[col_tgl]).strip()
                                    if tgl_str.lower() not in ['nan', 'none', '']: tgl_val = tgl_str.split(" ")[0] if "00:00:00" in tgl_str else tgl_str
                                if tgl_val == "-":
                                    for v in val_list:
                                        m = re.search(r'\d{1,2}-[a-zA-Z]{3}-?\d{0,4}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v)
                                        if m: tgl_val = m.group(0); break
                                if detected_plant == "SOLO" and current_solo_month != "":
                                    year_m = re.search(r'\b(20\d{2})\b', global_date)
                                    tgl_val = f"1 {current_solo_month} {year_m.group(1) if year_m else '2026'}"
                                elif tgl_val == "-" and global_date != "-": tgl_val = global_date
                                    
                                m_fpb_date = re.search(r'[A-Za-z]*(\d{2})(0[1-9]|1[0-2])[-/]', po_val)
                                if m_fpb_date: tgl_val = f"20{m_fpb_date.group(1)}-{m_fpb_date.group(2)}-01"
                                ppn_raw = str(row.values[col_ppn]).strip().upper() if col_ppn != -1 else "NON PPN"
                                            
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": po_val, "NO FPB": fpb_val, "TANGGAL": tgl_val, "VENDOR": vendor_val,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val if qty_val else 1.0, "SATUAN": sat_val, "HARGA": prc_val, "STATUS_PPN": "PPN" if ppn_raw == "PPN" else "NON PPN"
                                })
                            except Exception: pass

                # ===================================================================
                # LOGIKA 6: PUSAT
                # ===================================================================
                elif format_type == "PUSAT":
                    curr_po, curr_tgl, curr_vendor, curr_money = "", "-", "-", "RP"
                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        line = " | ".join(val_list).upper()
                        if not val_list or any(x in line for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line or "EXCLUDE" in line:
                            curr_po = re.sub(r'^[\s:]+', '', val_list[0]) if len(val_list)>0 else ""
                            for c in val_list: 
                                m = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', c)
                                if m: curr_tgl = m.group(0); break
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
                                        if parse_numeric(v_str) is not None or re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v_str) or v_str.upper() in ["RP", "USD", "EUR", "CNY", "IDR"]: continue
                                        names.append(v_str)
                                    extracted_rows.append({
                                        "UNIT KERJA": "PUSAT", "NO PO": curr_po, "NO FPB": "", "TANGGAL": curr_tgl, "VENDOR": curr_vendor,
                                        "MATA UANG": curr_money, "ITEM_KOTOR": max(names, key=len) if names else "Unknown", "QTY": nums[0], "SATUAN": "PCS", "HARGA": nums[-1], "STATUS_PPN": "NON PPN"
                                    })

            # VECTORIZED AI MATCHING (PERFORMA EKSTREM)
            if extracted_rows:
                st.success(f"✔️ Berhasil mengekstrak {len(extracted_rows)} baris data!")
                final_draft = []
                for r in extracted_rows:
                    match = process.extractOne(str(r['ITEM_KOTOR']).upper(), search_list, scorer=fuzz.token_set_ratio)
                    if match and match[1] >= 75:
                        baku = lookup_to_baku_map[match[0]]; info = mapping_master_info.get(baku, {})
                        uom_final = r.get('SATUAN', '')
                        if uom_final == 'PCS' and str(info.get('SATUAN', '')).upper() not in ['NAN', 'NONE', '', 'PCS']: uom_final = info.get('SATUAN', 'PCS')

                        final_draft.append({
                            "❌ BUKAN SCOPE": False, "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "NO FPB": r.get('NO FPB', ''), "TANGGAL": r['TANGGAL'], 
                            "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], "NAMA_BAKU": baku, "QTY": r['QTY'], "SATUAN": uom_final, "HARGA": r['HARGA'], "STATUS PPN": r['STATUS_PPN'],
                            "KATEGORI": info.get('KATEGORI', '-'), "DETAIL KATEGORI": info.get('DETAIL KATEGORI', '-'), "SKU": info.get('NOMOR SKU', '-')
                        })
                    else:
                        final_draft.append({
                            "❌ BUKAN SCOPE": False, "UNIT": r['UNIT KERJA'], "PO": r['NO PO'], "NO FPB": r.get('NO FPB', ''), "TANGGAL": r['TANGGAL'], 
                            "VENDOR": r['VENDOR'], "ITEM_ASLI": r['ITEM_KOTOR'], "NAMA_BAKU": "⚠️ BARANG BARU", "QTY": r['QTY'], "SATUAN": r.get('SATUAN', 'PCS'), "HARGA": r['HARGA'], "STATUS PPN": r['STATUS_PPN'],
                            "KATEGORI": "", "DETAIL KATEGORI": "", "SKU": "-"
                        })
                
                cols_order = ["❌ BUKAN SCOPE", "UNIT", "PO", "NO FPB", "TANGGAL", "VENDOR", "ITEM_ASLI", "NAMA_BAKU", "QTY", "SATUAN", "HARGA", "STATUS PPN", "KATEGORI", "DETAIL KATEGORI", "SKU"]
                st.session_state['holding_draft'] = pd.DataFrame(final_draft)[cols_order]
                st.rerun()
            else: st.warning("⚠️ Data item kosong! Periksa file Excel Anda.")
        except Exception as e: st.error(f"Error Mesin: {e}")

    if 'holding_draft' in st.session_state:
        st.markdown("### ⚠️ TAHAP REVIEW HOLDING (UNLOCKED)")
        edited_df = st.data_editor(st.session_state['holding_draft'], use_container_width=True, hide_index=True,
            column_config={
                "❌ BUKAN SCOPE": st.column_config.CheckboxColumn("❌ BUKAN SCOPE", default=False),
                "STATUS PPN": st.column_config.SelectboxColumn("STATUS PPN", options=["PPN", "NON PPN"], required=True)
            })
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; font-size:16px; margin-bottom:10px;'>🕒 Setup Penyimpanan</h4>", unsafe_allow_html=True)
        auto_time = st.checkbox("✅ Catat Waktu Rekap Secara Otomatis", value=True)
        manual_date = st.date_input("📅 Set Tanggal Manual (Backdate):") if not auto_time else None
        filter_dokumen_valid = st.checkbox("✅ HANYA SIMPAN DATA BERDOKUMEN VALID (Abaikan PO/FPB Kosong)", value=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 KONFIRMASI: Simpan ke DASHBOARD", type="primary", use_container_width=True):
                try:
                    with st.spinner("🚀 Menembakkan data..."):
                        tz_wib = datetime.timezone(datetime.timedelta(hours=7))
                        waktu_rekap = datetime.datetime.now(tz_wib).strftime("%Y-%m-%d %H:%M:%S") if auto_time else manual_date.strftime("%Y-%m-%d")
                        df_to_save = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
                        
                        if filter_dokumen_valid:
                            df_to_save = df_to_save[(df_to_save['PO'].astype(str).str.strip() != "") | (df_to_save['NO FPB'].astype(str).str.strip() != "")]
                        
                        client = get_gspread_client()
                        sheet_dash = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD))
                        sheet_sandbox = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_SANDBOX))
                        
                        data_to_push = []
                        for _, r in df_to_save.iterrows():
                            info = mapping_master_info.get(r['NAMA_BAKU'], {})
                            kat_final = info.get('KATEGORI', '-') if r['NAMA_BAKU'] != "⚠️ BARANG BARU" else str(r.get('KATEGORI', '-')).strip().upper()
                            det_kat_final = info.get('DETAIL KATEGORI', '-') if r['NAMA_BAKU'] != "⚠️ BARANG BARU" else str(r.get('DETAIL KATEGORI', '-')).strip().upper()
                            
                            data_to_push.append([
                                r['UNIT'], r['PO'], r['NO FPB'], r['TANGGAL'], r['VENDOR'], "RP", 
                                r['ITEM_ASLI'], r['NAMA_BAKU'], r['QTY'], r['SATUAN'], r['HARGA'], r['STATUS PPN'],
                                kat_final, det_kat_final, r['SKU'], waktu_rekap 
                            ])
                        
                        if data_to_push:
                            sheet_dash.append_rows(data_to_push)
                            sheet_sandbox.append_rows(data_to_push)
                            st.balloons(); st.success(f"🔥 BERHASIL! {len(data_to_push)} Data tersimpan."); 
                            del st.session_state['holding_draft']; time.sleep(1.5); st.rerun()
                        else: st.warning("Tidak ada data valid untuk disimpan.")
                except Exception as e: st.error(f"Simpan Gagal: {e}")
        with c2:
            if st.button("❌ Batalkan", use_container_width=True): del st.session_state['holding_draft']; st.rerun()
            
        try:
            df_to_export = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
            if filter_dokumen_valid: df_to_export = df_to_export[(df_to_export['PO'].astype(str).str.strip() != "") | (df_to_export['NO FPB'].astype(str).str.strip() != "")]
            if not df_to_export.empty:
                buffer_clean = io.BytesIO()
                with pd.ExcelWriter(buffer_clean, engine='openpyxl') as writer: df_to_export.to_excel(writer, index=False, sheet_name='Data Bersih')
                st.download_button("📥 Download Hasil (Excel Rapi)", data=buffer_clean.getvalue(), file_name=f"Data_Bersih_{datetime.date.today()}.xlsx", use_container_width=True)
        except: pass

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
# MENU 3: E-CATALOG & STUDIO
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio"])
    
    with t_cat:
        col_s, col_f, col_sort = st.columns([2, 1, 1])
        with col_s: search_cat = st.text_input("🔍 Cari Produk:")
        with col_f: filter_cat = st.selectbox("📁 Filter Kategori:", ["Semua Kategori"] + sorted([k for k in df_master_clean['KATEGORI'].unique() if str(k).strip() != "" and str(k).strip() != "nan"]))
        with col_sort: sort_by = st.selectbox("⬇️ Urutkan:", ["Nama (A-Z)", "Nama (Z-A)"])
        missing_only = st.checkbox("⚠️ Tampilkan HANYA barang tanpa gambar")

        df_show = df_master_clean.copy()
        if filter_cat != "Semua Kategori": df_show = df_show[df_show['KATEGORI'] == filter_cat]
        if search_cat: df_show = df_show[df_show['NAMA BAKU'].astype(str).str.contains(search_cat, case=False) | df_show['NOMOR SKU'].astype(str).str.contains(search_cat, case=False)]
        if missing_only: df_show = df_show[df_show['LINK GAMBAR'].isna() | (df_show['LINK GAMBAR'] == '')]
        df_show = df_show.sort_values(by='NAMA BAKU', ascending=(sort_by == "Nama (A-Z)"))
        
        st.markdown("---")
        if df_show.empty: st.warning("Data tidak ditemukan.")
        else:
            items_per_page = 20
            total_pages = max(1, (len(df_show) - 1) // items_per_page + 1)
            col_page, col_info = st.columns([1, 4])
            with col_page: page_number = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
            df_page = df_show.iloc[(page_number - 1) * items_per_page : page_number * items_per_page]

            cols = st.columns(4)
            for idx, (_, row) in enumerate(df_page.iterrows()): 
                with cols[idx % 4]:
                    baku = row['NAMA BAKU']
                    harga_data = latest_price_map.get(str(baku).strip().upper(), {})
                    harga_live = harga_data.get('harga', None)
                    img_url = process_image_url(str(row.get('LINK GAMBAR', '')).strip())
                    
                    img_element = f"<img src='{img_url}' style='width:100%; height:160px; object-fit:contain; border-radius:8px; margin-bottom:12px;'>" if img_url else f"<div style='background-color:#F1F5F9; height:160px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;'><span style='color:#94A3B8; font-weight:600;'>No Image Asset</span></div>"
                    harga_display = f"<span style='color:#047857; font-weight:800; font-size:16px;'>{format_rupiah(harga_live)}</span><br><span style='font-size:9px; color:#64748B;'>Tgl: {harga_data.get('tanggal', '-')}</span>" if harga_live else "<span style='color:#EF4444; font-size:11px; font-weight:600;'>Belum ada histori</span>"
                    
                    st.markdown(f"""
                    <div style='background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                        {img_element}
                        <h5 style='margin-top:0px; font-size:14px; font-weight:700; color:#0F172A; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;'>{baku}</h5>
                        <p style='font-size:11px; color:#64748B; margin:4px 0;'>SKU: {row.get('NOMOR SKU', '-')}</p>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px;'><div>{harga_display}</div></div>
                    </div>""", unsafe_allow_html=True)

    with t_studio:
        if st.session_state.get('role') != "ADMIN": st.error("⛔ Akses Ditolak!")
        else:
            st.write("### 📸 Asset Studio")
            studio_kat = st.selectbox("1. Filter Kategori:", ["Semua Kategori"] + sorted([k for k in df_master_clean['KATEGORI'].unique() if str(k).strip() != "" and str(k).strip() != "nan"]))
            df_studio = df_master_clean.copy() if studio_kat == "Semua Kategori" else df_master_clean[df_master_clean['KATEGORI'] == studio_kat]
            all_unique_items = df_studio['NAMA BAKU'].tolist()
            
            if all_unique_items:
                barang_pilih = st.selectbox("2. Pilih Nama Produk:", all_unique_items)
                curr_link = str(df_studio[df_studio['NAMA BAKU'] == barang_pilih].iloc[-1].get('LINK GAMBAR', '')).strip()
                if curr_link and curr_link.lower() not in ['nan', 'none', '']:
                    st.warning("⚠️ Barang sudah memiliki gambar.")
                    if process_image_url(curr_link): st.image(process_image_url(curr_link), width=150)
                else: st.success("✅ Barang belum memiliki gambar.")

                query_google = urllib.parse.quote(barang_pilih + " industri sparepart")
                st.markdown(f"<a href='https://www.google.com/search?tbm=isch&q={query_google}' target='_blank'><button style='background-color:#4285F4; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold;'>🔍 Cari di Google</button></a>", unsafe_allow_html=True)
                
                st.write("---")
                link_input = st.text_input("Paste URL Link Gambar:")
                file_upload = st.file_uploader("Area Paste", type=['png', 'jpg', 'jpeg', 'webp'])

                img_to_save = None
                if file_upload:
                    b64 = image_to_base64(file_upload)
                    if b64: st.image(file_upload, width=300); img_to_save = b64
                elif link_input:
                    prev = process_image_url(link_input)
                    if prev: st.image(prev, width=300); img_to_save = link_input

                if img_to_save and st.button("💾 Simpan Gambar", type="primary"):
                    with st.spinner("Menyimpan..."):
                        try:
                            client = get_gspread_client()
                            sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                            all_data = sheet_master.get_all_values()
                            headers_upper = [str(h).strip().upper() for h in all_data[0]]
                            if 'LINK GAMBAR' in headers_upper:
                                col_letter = col_num_to_letter(headers_upper.index('LINK GAMBAR') + 1)
                                matching_rows = [idx + 2 for idx in df_master[df_master['NAMA BAKU'].astype(str).str.strip().str.upper() == barang_pilih.strip().upper()].index]
                                if matching_rows:
                                    sheet_master.batch_update([{'range': f"{col_letter}{r}", 'values': [[img_to_save]]} for r in matching_rows])
                                    st.success(f"✅ Success!"); time.sleep(1.0); st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

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
            res = df_v[df_v.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)] if keyword else df_v.head(100)
            for _, v in res.iterrows():
                with st.expander(f"🏢 {v.get('NAMA VENDOR', '-')} | Cat: {v.get('KATEGORI', '-')} "):
                    st.write(f"**PIC:** {v.get('PIC', '-')} 📞 {v.get('KONTAK', '-')}")
                    st.write(f"**Alamat:** {v.get('ALAMAT', '-')}")
    except: st.warning("Database Error.")

# ==========================================
# MENU 5: DASHBOARD LAPORAN
# ==========================================
elif menu == "Dashboard Laporan":
    st.markdown("<h2>📊 Procurement Intelligence & Forecasting</h2>", unsafe_allow_html=True)
    try:
        data_dash = get_gspread_client().open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD)).get_all_values()
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
            df_d['DATE_CLEAN'] = df_d[c_tgl].apply(convert_to_standard_date)
            
            if not df_d.empty:
                min_date, max_date = df_d['DATE_CLEAN'].min().date(), df_d['DATE_CLEAN'].max().date()
                today = datetime.date.today()

                if 'start_date' not in st.session_state: st.session_state.start_date = min_date
                if 'end_date' not in st.session_state: st.session_state.end_date = max_date

                c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
                if c_btn1.button("♾️ Semua Waktu", use_container_width=True): st.session_state.start_date = min_date; st.session_state.end_date = max_date; st.rerun()
                if c_btn2.button("📅 Tahun Ini", use_container_width=True): st.session_state.start_date = datetime.date(today.year, 1, 1); st.session_state.end_date = today; st.rerun()
                if c_btn3.button("📆 Bulan Ini", use_container_width=True): st.session_state.start_date = today.replace(day=1); st.session_state.end_date = today; st.rerun()
                if c_btn4.button("🗓️ Minggu Ini", use_container_width=True): st.session_state.start_date = today - datetime.timedelta(days=today.weekday()); st.session_state.end_date = today; st.rerun()

                c_date, c_fac, c_export = st.columns([1.5, 1.5, 1])
                with c_date: date_range = st.date_input("Rentang Tanggal:", value=(st.session_state.start_date, st.session_state.end_date))
                with c_fac: filter_unit = st.selectbox("Lokasi Pabrik:", ["All Facilities"] + sorted([u for u in df_d[c_unit].unique() if str(u).strip() != ""]))

                df_filtered = df_d[(df_d['DATE_CLEAN'].dt.date >= date_range[0]) & (df_d['DATE_CLEAN'].dt.date <= date_range[1])] if len(date_range) == 2 else df_d
                if filter_unit != "All Facilities": df_filtered = df_filtered[df_filtered[c_unit] == filter_unit]
                
                with c_export:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_filtered.drop(columns=['H_NUM', 'Q_NUM', 'DATE_CLEAN'], errors='ignore').to_excel(writer, index=False)
                    st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name=f"Laporan_{filter_unit}.xlsx", use_container_width=True)

                st.markdown("---")
                if df_filtered.empty: st.warning("⚠️ Tidak ada transaksi.")
                else:
                    tab_summary, tab_item = st.tabs(["🌐 Corporate Overview", "🔎 Item Analytics & AI Forecast"])
                    with tab_summary:
                        st.write("") 
                        col1, col2, col3 = st.columns(3)
                        with col1: st.markdown(create_metric_card("fa-solid fa-sack-dollar", "Total Value", format_rupiah(df_filtered['TOTAL'].sum())), unsafe_allow_html=True)
                        with col2: st.markdown(create_metric_card("fa-solid fa-file-invoice", "PO Transactions", f"{df_filtered[c_po].replace('', pd.NA).dropna().nunique()}"), unsafe_allow_html=True)
                        with col3: st.markdown(create_metric_card("fa-solid fa-industry", "Active Facilities", f"{df_filtered[c_unit].nunique()}"), unsafe_allow_html=True)
                        
                        c_a, c_b = st.columns([1, 1.5])
                        with c_a:
                            st.markdown("<h4 style='font-size:16px; margin-top:15px;'>Budget Distribution</h4>", unsafe_allow_html=True)
                            if filter_unit == "All Facilities":
                                rekap_u = df_filtered.groupby(c_unit)['TOTAL'].sum().reset_index()
                                fig_pie = px.pie(rekap_u[rekap_u[c_unit].str.strip() != ""], names=c_unit, values='TOTAL', hole=0.6, color_discrete_sequence=['#047857', '#10B981', '#34D399', '#6EE7B7'])
                                st.plotly_chart(fig_pie, use_container_width=True, theme=None)
                            else: st.info(f"Viewing specialized data for **{filter_unit}**.")

                        with c_b:
                            st.markdown("<h4 style='font-size:16px; margin-top:15px;'>Top Procurement Items</h4>", unsafe_allow_html=True)
                            df_valid = df_filtered[~df_filtered[c_baku].str.contains('CEK MANUAL|BARANG BARU', case=False, na=False)]
                            if not df_valid.empty:
                                top_i = df_valid[df_valid[c_baku].str.strip() != ""].groupby(c_baku)[c_po].nunique().reset_index()
                                top_i.columns = ['Nama Barang', 'Jumlah PO']
                                fig_bar = px.bar(top_i.sort_values(by='Jumlah PO', ascending=False).head(8), x='Jumlah PO', y='Nama Barang', orientation='h', color_discrete_sequence=['#047857'])
                                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                                st.plotly_chart(fig_bar, use_container_width=True, theme=None)
                    
                    with tab_item:
                        barang_pilih = st.multiselect("Search Product Intelligence:", df_filtered.drop_duplicates(subset=[c_baku]).sort_values(by=c_baku)[c_baku].tolist())
                        if barang_pilih:
                            df_item_histori = df_filtered[df_filtered[c_baku].isin(barang_pilih)].sort_values(by='DATE_CLEAN')
                            if len(barang_pilih) == 1:
                                item_tunggal = barang_pilih[0]
                                info_master = df_master_clean[df_master_clean['NAMA BAKU'] == item_tunggal].tail(1)
                                kat_item = str(info_master.iloc[0].get('KATEGORI', '')).upper() if not info_master.empty else "NAN"
                                v_histori = sorted([str(v).strip() for v in df_item_histori['VENDOR'].unique() if str(v).strip() not in ['', '-', 'nan']])
                                v_database = sorted(df_v[df_v['KATEGORI'].astype(str).str.contains(kat_item, case=False, na=False)]['NAMA VENDOR'].unique().tolist()) if kat_item != "NAN" and not df_v.empty else []

                                st.markdown("<br>", unsafe_allow_html=True)
                                c_img, c_meta = st.columns([1, 2.5])
                                with c_img:
                                    if not info_master.empty:
                                        img_url = process_image_url(str(info_master.iloc[0].get('LINK GAMBAR', '')).strip())
                                        if img_url: st.markdown(f"<img src='{img_url}' width='100%' style='border-radius:8px;'>", unsafe_allow_html=True)
                                with c_meta:
                                    st.markdown(f"<h3 style='margin-top:0;'>{item_tunggal}</h3>", unsafe_allow_html=True)
                                    if not info_master.empty:
                                        st.markdown(f"**SKU:** {info_master.iloc[0].get('NOMOR SKU', '-')} | **CAT:** {kat_item} | **UOM:** {info_master.iloc[0].get('SATUAN', '-')}")
                                        st.write(f"**Histori Supplier:** {', '.join(v_histori)}")
                                        st.write(f"**Rekomendasi Supplier:** {', '.join(v_database)}")
                                
                                st.markdown("---")
                                if not df_item_histori.empty:
                                    m1, m2, m3, m4 = st.columns(4)
                                    with m1: st.markdown(create_metric_card("fa-solid fa-money-bill-wave", "Total Cost", format_rupiah(df_item_histori['TOTAL'].sum())), unsafe_allow_html=True)
                                    with m2: st.markdown(create_metric_card("fa-solid fa-cart-shopping", "Transactions", f"{df_item_histori[c_po].nunique()}"), unsafe_allow_html=True)
                                    with m3: st.markdown(create_metric_card("fa-solid fa-tag", "Avg Price", format_rupiah(df_item_histori['H_NUM'].mean())), unsafe_allow_html=True)
                                    with m4: st.markdown(create_metric_card("fa-solid fa-handshake", "Suppliers", f"{len(v_histori)}"), unsafe_allow_html=True)

                                    g_harga, g_qty = st.columns(2)
                                    with g_harga: st.plotly_chart(px.line(df_item_histori, x='DATE_CLEAN', y='H_NUM', title="Price Volatility", markers=True), use_container_width=True)
                                    with g_qty: st.plotly_chart(px.bar(df_item_histori.groupby(pd.Grouper(key='DATE_CLEAN', freq='ME'))['Q_NUM'].sum().reset_index(), x='DATE_CLEAN', y='Q_NUM', title="Procurement Volume"), use_container_width=True)
                                    
                                    st.markdown("---")
                                    st.markdown("<h3>🔮 AI Forecasting & Budget Projection</h3>", unsafe_allow_html=True)
                                    df_monthly_fc = df_item_histori.groupby(pd.Grouper(key='DATE_CLEAN', freq='ME'))['Q_NUM'].sum().reset_index()
                                    if len(df_monthly_fc) >= 1:
                                        avg_qty = df_monthly_fc['Q_NUM'].mean()
                                        latest_price = df_item_histori.sort_values(by='DATE_CLEAN').iloc[-1]['H_NUM']
                                        uom = info_master.iloc[0].get('SATUAN', 'Pcs') if not info_master.empty else "Pcs"
                                        
                                        c_fc1, c_fc2, c_fc3 = st.columns(3)
                                        with c_fc1: st.markdown(create_metric_card("fa-solid fa-chart-line", "Rata-rata Kebutuhan", f"{avg_qty:.0f} {uom}"), unsafe_allow_html=True)
                                        with c_fc2: st.markdown(create_metric_card("fa-solid fa-tags", "Patokan Harga", format_rupiah(latest_price)), unsafe_allow_html=True)
                                        with c_fc3: st.markdown(create_metric_card("fa-solid fa-vault", "Estimasi Budget", format_rupiah(avg_qty * latest_price)), unsafe_allow_html=True)
                            else:
                                st.markdown("<h3>⚖️ Multi-Item Comparison</h3>", unsafe_allow_html=True)
                                st.plotly_chart(px.line(df_item_histori, x='DATE_CLEAN', y='H_NUM', color=c_baku, title="Price Comparison", markers=True), use_container_width=True)
    except Exception as e: st.error(f"Dashboard Error: {e}")

# ==========================================
# MENU 6: MAINTENANCE DATA
# ==========================================
elif menu == "Maintenance Data":
    st.markdown("<h2>🛠️ System Config & SKU Generator</h2>", unsafe_allow_html=True)
    invalid_mask = df_master_clean['NOMOR SKU'].isna() | (df_master_clean['NOMOR SKU'].astype(str).str.strip().str.len() < 10)
    df_missing = df_master_clean[invalid_mask]
    
    if not df_missing.empty:
        st.warning(f"⚠️ Terdeteksi {len(df_missing)} item yang membutuhkan Nomor SKU.")
        if st.button("🔄 Generate Preview SKU", type="primary"):
            with st.spinner("Membuat draft..."):
                try:
                    sheet_master = get_gspread_client().open_by_key(SHEET_ID).get_worksheet(0)
                    all_data = sheet_master.get_all_values()
                    headers = [str(h).strip().upper() for h in all_data[0]]
                    df_m = pd.DataFrame(all_data[1:], columns=headers)
                    
                    c_s = next((c for c in headers if 'SKU' in c), None)
                    c_k = next((c for c in headers if 'KATEGORI' in c and 'DETAIL' not in c and 'LEVEL' not in c), None)
                    c_d = next((c for c in headers if 'DETAIL' in c), None)
                    c_tgl = next((c for c in headers if 'TANGGAL' in c or 'TGL' in c or 'DATE' in c), None) 
                    c_lvl = next((c for c in headers if 'LEVEL' in c or 'KELOMPOK' in c), None)
                    
                    if c_s and c_k and c_d:
                        preview_data = []
                        for idx, row in df_m.iterrows():
                            val = str(row[c_s]).strip()
                            if len(val) < 10 or val.upper() in ['NAN', 'NONE', 'NULL', '#N/A', '']: 
                                prefix_val = extract_code(str(row[c_lvl])) if c_lvl else "001"
                                if not prefix_val.isdigit(): prefix_val = "001"
                                new_sku = generate_new_sku(prefix_val, row[c_k], row[c_d], df_m)
                                df_m.at[idx, c_s] = new_sku
                                preview_data.append({
                                    "Baris Excel": idx + 2, "TANGGAL": row[c_tgl] if c_tgl else "-",
                                    "NAMA BAKU": row.get('NAMA BAKU', '-'), "LEVEL": row[c_lvl] if c_lvl else "-",
                                    "KATEGORI": row[c_k], "DETAIL KATEGORI": row[c_d], "SKU BARU": new_sku
                                })
                        st.session_state['draft_sku_df'] = df_m
                        st.session_state['preview_sku_list'] = pd.DataFrame(preview_data)
                except Exception as e: st.error(f"Error: {e}")

        if 'preview_sku_list' in st.session_state:
            st.info("💡 **Silakan edit 'LEVEL', 'KATEGORI', 'DETAIL KATEGORI', atau 'SKU BARU' langsung di tabel ini sebelum disimpan.**")
            edited_preview = st.data_editor(st.session_state['preview_sku_list'], disabled=["Baris Excel", "NAMA BAKU"], use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Konfirmasi & Tembak ke Master Data", type="primary", use_container_width=True):
                    with st.spinner("Menimpa ke Google Sheets..."):
                        try:
                            df_full = st.session_state['draft_sku_df']
                            c_s = next((c for c in df_full.columns if 'SKU' in c), None)
                            c_tgl = next((c for c in df_full.columns if 'TANGGAL' in c or 'TGL' in c or 'DATE' in c), None)
                            c_k = next((c for c in df_full.columns if 'KATEGORI' in c and 'DETAIL' not in c and 'LEVEL' not in c), None)
                            c_d = next((c for c in df_full.columns if 'DETAIL' in c), None)
                            c_lvl = next((c for c in df_full.columns if 'LEVEL' in c or 'KELOMPOK' in c), None)
                            
                            for _, row in edited_preview.iterrows():
                                excel_idx = row["Baris Excel"] - 2
                                if c_s: df_full.at[excel_idx, c_s] = row["SKU BARU"]
                                if c_tgl and "TANGGAL" in row: df_full.at[excel_idx, c_tgl] = row["TANGGAL"]
                                if c_k and "KATEGORI" in row: df_full.at[excel_idx, c_k] = row["KATEGORI"]
                                if c_d and "DETAIL KATEGORI" in row: df_full.at[excel_idx, c_d] = row["DETAIL KATEGORI"]
                                if c_lvl and "LEVEL" in row: df_full.at[excel_idx, c_lvl] = row["LEVEL"]
                                
                            sheet_master = get_gspread_client().open_by_key(SHEET_ID).get_worksheet(0)
                            sheet_master.clear()
                            sheet_master.update(values=[df_full.columns.tolist()] + df_full.values.tolist())
                            
                            st.success("✔️ Berhasil! Master Data telah diupdate."); del st.session_state['draft_sku_df']; del st.session_state['preview_sku_list']
                            time.sleep(1.0); st.rerun()
                        except Exception as e: st.error(f"Gagal menyimpan: {e}")
            with c2:
                if st.button("❌ Batal", use_container_width=True): del st.session_state['draft_sku_df']; del st.session_state['preview_sku_list']; st.rerun()
    else: st.success("✔️ Database Sehat. Semua SKU terverifikasi.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #94A3B8; font-size: 12px;'>ERP Purchasing System v16.0 | Proprietary of PT Panca Budi Idaman Tbk | Created with for Raihan Subakti<br><span style='color: #10B981; font-weight: 600;'>🟢 Live Database tersinkronisasi pada: {get_sync_time()}</span></p>", unsafe_allow_html=True)