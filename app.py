# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 6.1 (EXECUTIVE EDITION + PGP Smart Auto-Detect & Multi-Sheet)
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
    
    .main { background-color: #F8FAFC; }
    
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
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    
    .stButton>button { border-radius: 8px; font-weight: 600; letter-spacing: 0.5px; transition: all 0.3s; background-color: #059669; color: white; border: none; }
    .stButton>button:hover { background-color: #047857; color: white; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SISTEM KONEKSI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1EJnbmhufaKfKEQmAmkQFYvJZ9_Kx_vJ7C1HvcyzK4WQ"
GID_MASTER = "0"          
GID_VENDOR = "168217676"  
GID_DASHBOARD = "1722600044" 

def get_gspread_client():
    key_dict = json.loads(st.secrets["google_json"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300) 
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    return pd.read_csv(url)

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
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url_str)
    if match: return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800"
    return url_str

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

# ==========================================
# 4. LOAD & PERSIAPAN MASTER DATA
# ==========================================
try:
    df_master = load_data(GID_MASTER)
    df_master.columns = df_master.columns.str.strip().str.upper()
    df_master = df_master.dropna(subset=['NAMA BAKU'])
    
    if 'KATEGORI' in df_master.columns: df_master['KATEGORI'] = df_master['KATEGORI'].ffill().astype(str).str.strip().str.upper()
    if 'DETAIL KATEGORI' in df_master.columns: df_master['DETAIL KATEGORI'] = df_master['DETAIL KATEGORI'].ffill().astype(str).str.strip().str.upper()
    
    df_master['AI_LOOKUP'] = df_master['NAMA BAKU'].astype(str).str.upper()
    if 'NAMA ITEM' in df_master.columns: df_master['AI_LOOKUP'] += " " + df_master['NAMA ITEM'].fillna("").astype(str).str.upper()
        
    df_master_unique = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')
    mapping_master = df_master_unique.set_index('NAMA BAKU').to_dict('index')
    search_list = df_master['AI_LOOKUP'].tolist()
    lookup_to_baku_map = dict(zip(df_master['AI_LOOKUP'], df_master['NAMA BAKU']))
except Exception as e:
    st.error(f"⚠️ Gagal Load Master Data: {e}"); st.stop()

# ==========================================
# 5. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;'>
            <h1 style='color: #047857; font-weight: 800; margin: 0; font-size: 32px; letter-spacing: -1px;'>PANCA BUDI</h1>
            <p style='color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 2px; margin: 0;'>HOLDING PURCHASING</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Sync Database", use_container_width=True):
        st.cache_data.clear(); st.rerun()
        
    st.write("") 
    
    menu = option_menu(
        menu_title="", 
        options=["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"],
        icons=["magic", "search", "images", "shop", "bar-chart-line", "tools"], 
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
        # PERUBAHAN V6.1: PGP DISATUKAN DENGAN SMART AUTO-DETECT
        pilihan_format = st.selectbox("🏢 Pilih Asal Laporan / Format Pabrik:", 
                                     ["Plant RA (ra pembelian.xls)", 
                                      "Plant PGP (Auto-Detect Format)",
                                      "Plant Ceper (Laporan PO per Bukti)", 
                                      "Plant Pemalang (Laporan PO per Bukti)",
                                      "Plant PIHC (Rekap Formulir Permintaan)",
                                      "ERP Pusat (Include/Exclude)"])

    with st.form("upload_holding"):
        file_raw = st.file_uploader("📥 Upload Excel Mentah (Drag & Drop di sini):", type=["xlsx", "xls"])
        btn_proses = st.form_submit_button("🚀 Mulai Ekstraksi & AI Matching", type="primary")

    if btn_proses and file_raw:
        try:
            dict_df = pd.read_excel(file_raw, sheet_name=None, header=None)
            extracted_rows = []
            
            # --- TAMPILKAN INFO STATUS MESIN ---
            if "Plant RA" in pilihan_format:
                st.info("🤖 Mesin Khusus RA memindai seluruh sheet secara dinamis...")
            elif "Plant PGP" in pilihan_format:
                st.info("🤖 Mesin Smart-Detect PGP sedang memindai format (Lama/Baru) pada seluruh sheet...")
            elif "Ceper" in pilihan_format or "Pemalang" in pilihan_format:
                detected_plant = "CEPER" if "Ceper" in pilihan_format else "PEMALANG"
                st.info(f"🤖 Mesin Traktor bekerja untuk format Laporan PO per Bukti ({detected_plant}) pada seluruh sheet...")
            elif "PIHC" in pilihan_format:
                st.info("🤖 Mata Pisau Khusus PIHC menjahit kolom beda baris di seluruh sheet...")
            elif "ERP Pusat" in pilihan_format:
                st.info("🤖 Mesin ERP Pusat membaca seluruh sheet...")

            # --- LOOPING SEMUA SHEET (JAN-1, JAN-2, dst) ---
            for sheet_name, df_input in dict_df.items():
                format_type = ""
                detected_plant = ""

                # --- PENENTUAN FORMAT SECARA DINAMIS ---
                if "Plant RA" in pilihan_format:
                    format_type = "RA"
                    detected_plant = "RA"
                elif "ERP Pusat" in pilihan_format:
                    format_type = "PUSAT"
                    detected_plant = "PUSAT"
                elif "Ceper" in pilihan_format:
                    format_type = "OLD"
                    detected_plant = "CEPER"
                elif "Pemalang" in pilihan_format:
                    format_type = "OLD"
                    detected_plant = "PEMALANG"
                elif "PIHC" in pilihan_format:
                    format_type = "NEW"
                    detected_plant = "PIHC"
                elif "Plant PGP" in pilihan_format:
                    detected_plant = "PGP"
                    is_new = False
                    # Auto-detect PGP: Cari kata JENIS BARANG dan HARGA di 30 baris awal
                    for idx, row in df_input.head(30).iterrows():
                        teks_sebaris = " ".join([str(c).strip().upper().replace('\n', ' ') for c in row.values])
                        if "JENIS BARANG" in teks_sebaris and "HARGA" in teks_sebaris:
                            is_new = True
                            break
                    format_type = "NEW" if is_new else "OLD"

                # =======================================
                # EKSEKUSI BERDASARKAN FORMAT YANG TERDETEKSI
                # =======================================
                
                # --- 1. LOGIKA PLANT RA ---
                if format_type == "RA":
                    curr_po, curr_tgl, curr_vendor = "-", "-", "-"
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
                            
                            date_m = next((v for v in val_list if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v)), None)
                            po_m = next((v for v in val_list if "PB" in v.upper() and len(v) > 5 and re.search(r'\d', v)), None)
                            
                            if date_m and po_m:
                                curr_tgl = date_m.split(" ")[0]
                                curr_po = po_m
                                potensi_vendor = [v for v in val_list if v != date_m and v != po_m and not re.match(r'^[-0-9.,]+$', v) and "00/01/1900" not in v]
                                curr_vendor = max(potensi_vendor, key=len).replace("00/01/1900", "").strip() if potensi_vendor else "CASH / TANPA NAMA"
                                continue
                                
                            if curr_po != "-":
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

                # --- 2. LOGIKA OLD (PGP LAMA, CEPER, PEMALANG) ---
                elif format_type == "OLD":
                    curr_po, curr_tgl, curr_vendor, curr_money = "-", "-", "-", "RP"

                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        if not val_list: continue
                        line_text = " | ".join(val_list).upper()

                        if any(x in line_text for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line_text or "EXCLUDE" in line_text:
                            curr_po = val_list[0]
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

                # --- 3. LOGIKA NEW (PIHC & PGP BARU) ---
                elif format_type == "NEW":
                    col_nama = col_qty = col_harga = col_vendor = col_po = col_tgl = -1
                    start_idx = 0
                    
                    for idx, row in df_input.head(30).iterrows():
                        row_upper = [str(c).strip().upper().replace('\n', ' ') for c in row.values]
                        
                        for i, x in enumerate(row_upper):
                            if 'JENIS BARANG' in x and col_nama == -1: 
                                col_nama = i; start_idx = max(start_idx, idx)
                            elif 'HARGA' in x and 'PER' not in x and 'UPDATE' not in x and col_harga == -1: 
                                col_harga = i; start_idx = max(start_idx, idx)
                            elif 'VENDOR' in x and 'PENUNJUKKAN' not in x and col_vendor == -1: 
                                col_vendor = i; start_idx = max(start_idx, idx)
                            elif ('QTY' in x) and col_qty == -1: 
                                col_qty = i
                            elif 'NO PO' in x and col_po == -1: 
                                col_po = i
                            elif ('PENYELESAIAN' in x or 'TGL EMAIL' in x) and col_tgl == -1: 
                                col_tgl = i
                                
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
                                prc_val = parse_numeric(row.values[col_harga])
                                
                                if prc_val is None or prc_val == 0: continue 
                                
                                v_str = str(row.values[col_vendor]).strip() if col_vendor != -1 else "-"
                                vendor_val = v_str if v_str.lower() not in ['nan', 'none', ''] else "CASH / TANPA NAMA"
                                
                                po_str = str(row.values[col_po]).strip() if col_po != -1 else "-"
                                po_val = po_str if po_str.lower() not in ['nan', 'none', ''] else "-"
                                
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
                                            
                                extracted_rows.append({
                                    "UNIT KERJA": detected_plant, "NO PO": po_val, "TANGGAL": tgl_val, "VENDOR": vendor_val,
                                    "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty_val, "HARGA": prc_val
                                })
                            except Exception: pass

                # --- 4. LOGIKA ERP PUSAT ---
                elif format_type == "PUSAT":
                    curr_po, curr_tgl, curr_vendor, curr_money = "-", "-", "-", "RP"
                    for idx, row in df_input.iterrows():
                        val_list = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                        line = " | ".join(val_list).upper()
                        
                        if not val_list or any(x in line for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO", "NO TRANS"]): continue

                        if "INCLUDE" in line or "EXCLUDE" in line:
                            curr_po = val_list[0]
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

            # --- AI MATCHING & DRAFT PREPARATION ---
            if extracted_rows:
                st.success(f"✔️ Berhasil mengekstrak {len(extracted_rows)} baris data mentah yang valid dari seluruh Sheet!")
                final_draft = []
                for r in extracted_rows:
                    match = process.extractOne(str(r['ITEM_KOTOR']).upper(), search_list, scorer=fuzz.token_set_ratio)
                    if match and match[1] >= 75:
                        baku = lookup_to_baku_map[match[0]]; info = mapping_master.get(baku, {})
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
        st.markdown("### ⚠️ TAHAP REVIEW HOLDING")
        st.info("💡 **INFO:** Centang kotak **❌ BUKAN SCOPE** untuk membuang barang yang bukan wewenang Anda (ATK, dll). Anda juga bisa mengetik `KATEGORI` untuk **⚠️ BARANG BARU**.")
        
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
            },
            disabled=["UNIT", "PO", "TANGGAL", "VENDOR", "ITEM_ASLI", "QTY", "HARGA"] 
        )
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 KONFIRMASI: Simpan ke Dashboard Induk", type="primary", use_container_width=True):
                try:
                    with st.spinner("Tembak data ke Google Sheets..."):
                        df_to_save = edited_df[edited_df["❌ BUKAN SCOPE"] == False]
                        client = get_gspread_client()
                        sheet = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD))
                        
                        data_to_push = []
                        for _, r in df_to_save.iterrows():
                            info = mapping_master.get(r['NAMA_BAKU'], {})
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
                                kat_final, det_kat_final, r['SKU']
                            ])
                        
                        if data_to_push:
                            sheet.append_rows(pd.DataFrame(data_to_push).fillna("-").values.tolist())
                            st.balloons(); st.success(f"🔥 {len(data_to_push)} Data bersih berhasil masuk ke Dashboard!"); del st.session_state['holding_draft']; time.sleep(2); st.rerun()
                        else:
                            st.warning("Tidak ada data yang disimpan (semua dicentang sebagai bukan scope).")
                            
                except Exception as e: st.error(f"Simpan Gagal: {e}")
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
                baku = lookup_to_baku_map[m[0]]; info = mapping_master.get(baku, {})
                res_list.append({"Match": f"{m[1]}%", "Nama Baku": baku, "SKU": info.get('NOMOR SKU', '-'), "Kategori": info.get('KATEGORI', '-'), "Est. Harga": format_rupiah(info.get('HARGA', 0)), "Last Vendor": info.get('VENDOR', '-')})
        st.dataframe(pd.DataFrame(res_list), use_container_width=True)

# ==========================================
# MENU 3: E-CATALOG & STUDIO GAMBAR
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio (Update Gambar)"])
    
    with t_cat:
        col_s, col_f = st.columns([2, 1])
        with col_s: search_cat = st.text_input("🔍 Cari Produk:")
        with col_f:
            list_kat = ["All Categories"] + sorted([k for k in df_master['KATEGORI'].unique() if str(k).strip() != "" and str(k).strip() != "nan"])
            filter_cat = st.selectbox("📁 Kategori:", list_kat)
        
        df_show = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last').copy()
        if filter_cat != "All Categories": df_show = df_show[df_show['KATEGORI'] == filter_cat]
        if search_cat: df_show = df_show[df_show['NAMA BAKU'].astype(str).str.contains(search_cat, case=False) | df_show['NOMOR SKU'].astype(str).str.contains(search_cat, case=False)]
        
        st.markdown("---")
        if df_show.empty: st.warning("Data tidak ditemukan.")
        else:
            cols = st.columns(4)
            for idx, (_, row) in enumerate(df_show.head(40).iterrows()): 
                with cols[idx % 4]:
                    raw_link = str(row.get('LINK GAMBAR', '')).strip()
                    img_url = process_image_url(raw_link) 
                    
                    if img_url:
                        img_element = f"<img src='{img_url}' style='width:100%; height:160px; object-fit:contain; border-radius:8px; margin-bottom:12px;'>"
                    else:
                        img_element = f"<div style='background-color:#F1F5F9; height:160px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;'><span style='color:#94A3B8; font-weight:600;'>No Image Asset</span></div>"
                    
                    card_html = f"""
                    <div style='background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: 0.3s;'>
                        {img_element}
                        <h5 style='margin-top:0px; font-size:14px; font-weight:700; color:#0F172A; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;'>{row['NAMA BAKU']}</h5>
                        <p style='font-size:11px; color:#64748B; margin:4px 0;'>SKU: {row.get('NOMOR SKU', '-')}</p>
                        <p style='font-size:15px; font-weight:800; color:#047857; margin-top:8px; margin-bottom:0px;'>{format_rupiah(row.get('HARGA', 0))}</p>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

    with t_studio:
        st.write("### 📸 Inject / Update Image Asset")
        st.info("💡 **TIPS BARU:** Anda bisa mengisi gambar barang baru, ATAU **menimpa gambar barang yang sudah ada** jika salah. Cari gambar di Google, Klik Kanan -> **Copy Image Address** -> Paste di kotak bawah.")
        
        if 'LINK GAMBAR' not in df_master.columns: df_master['LINK GAMBAR'] = ""
        
        all_unique_items = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')['NAMA BAKU'].tolist()
        
        if not all_unique_items: st.success("Database Kosong.")
        else:
            barang_pilih = st.selectbox("Ketik Nama Produk yang Mau Diubah/Ditambah Gambarnya:", all_unique_items)
            
            current_row = df_master[df_master['NAMA BAKU'] == barang_pilih].iloc[-1]
            current_link = str(current_row.get('LINK GAMBAR', '')).strip()
            
            if current_link and current_link.lower() not in ['nan', 'none', '']:
                st.warning("⚠️ **Barang ini sudah memiliki gambar.** Jika Anda meng-upload link baru, gambar lama akan ditimpa (overwrite).")
                curr_preview = process_image_url(current_link)
                if curr_preview:
                    st.image(curr_preview, width=150, caption="Preview Gambar Saat Ini")
            else:
                st.success("✅ Barang ini belum memiliki gambar. Silakan upload.")

            query_google = urllib.parse.quote(barang_pilih + " industri sparepart")
            st.markdown(f"""
            <a href="https://www.google.com/search?tbm=isch&q={query_google}" target="_blank">
                <button style="background-color:#4285F4; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-weight:bold; margin-bottom:15px; margin-top:10px;">
                    🔍 Buka Google Images untuk "{barang_pilih}"
                </button>
            </a>
            """, unsafe_allow_html=True)

            link_input = st.text_input("Paste Link Gambar (G-Drive ATAU Link Internet Bebas) di sini:")
            if link_input:
                if "shopee.co.id/" in link_input and "cf.shopee.co.id" not in link_input:
                    st.error("⚠️ Oops! Ini link Halaman Produk Shopee. Silakan kembali ke Google Images, klik kanan tepat di fotonya, lalu pilih 'Copy Image Address' (Salin Alamat Gambar).")
                elif "tokopedia.com/" in link_input and "images.tokopedia.net" not in link_input:
                    st.error("⚠️ Oops! Ini link Halaman Produk Tokopedia. Silakan kembali ke Google Images, klik kanan tepat di fotonya, lalu pilih 'Copy Image Address' (Salin Alamat Gambar).")
                else:
                    img_preview = process_image_url(link_input)
                    if img_preview:
                        is_valid = True
                        try:
                            st.image(img_preview, width=300, caption="Preview Gambar BARU")
                        except Exception:
                            st.warning("⚠️ Gambar gagal dimuat! Pastikan link yang dimasukkan berakhiran seperti .jpg / .png, atau link Google Drive yang valid.")
                            is_valid = False
                            
                        if is_valid:
                            if st.button("💾 Upload / Update Gambar", type="primary"):
                                try:
                                    with st.spinner("Menimpa gambar ke database..."):
                                        client = get_gspread_client()
                                        sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                                        cell = sheet_master.find(barang_pilih, in_column=2)
                                        if cell:
                                            headers = sheet_master.row_values(1)
                                            if 'LINK GAMBAR' in headers:
                                                col_link_idx = headers.index('LINK GAMBAR') + 1
                                                sheet_master.update_cell(cell.row, col_link_idx, link_input)
                                                st.success("✅ Success! Gambar berhasil diperbarui.")
                                                time.sleep(1)
                                                st.cache_data.clear()
                                                st.rerun()
                                            else:
                                                st.error("Kolom 'LINK GAMBAR' belum ada di baris pertama Sheet 1 Anda.")
                                except Exception as e:
                                    st.error(f"Error: {e}")

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
            c_tgl = next((c for c in df_d.columns if 'TANGGAL' in c or 'TGL' in c or 'DATE' in c), None)
            
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
                                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                                st.plotly_chart(fig_pie, use_container_width=True)
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
                                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_bar, use_container_width=True)
                    
                    with tab_item:
                        list_barang_histori = df_filtered.drop_duplicates(subset=[c_baku]).sort_values(by=c_baku)[c_baku].tolist()
                        barang_pilih = st.multiselect("Search Product Intelligence (Bisa pilih lebih dari 1 untuk perbandingan):", list_barang_histori, placeholder="Pilih barang untuk dianalisa...")
                        
                        if barang_pilih:
                            df_item_histori = df_filtered[df_filtered[c_baku].isin(barang_pilih)].sort_values(by='DATE_CLEAN')

                            if len(barang_pilih) == 1:
                                item_tunggal = barang_pilih[0]
                                info_master = df_master[df_master['NAMA BAKU'] == item_tunggal].tail(1)
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
                                        fig_harga.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Price (IDR)")
                                        st.plotly_chart(fig_harga, use_container_width=True)
                                    with g_qty:
                                        df_monthly = df_item_histori.groupby(pd.Grouper(key='DATE_CLEAN', freq='ME'))['Q_NUM'].sum().reset_index()
                                        fig_qty = px.bar(df_monthly, x='DATE_CLEAN', y='Q_NUM', title="Procurement Volume by Month", color_discrete_sequence=['#3B82F6'])
                                        fig_qty.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Quantity")
                                        st.plotly_chart(fig_qty, use_container_width=True)
                                    
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
                                        fig_harga.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Price (IDR)", legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=""))
                                        st.plotly_chart(fig_harga, use_container_width=True)
                                    with g_qty:
                                        df_monthly = df_item_histori.groupby([pd.Grouper(key='DATE_CLEAN', freq='ME'), c_baku])['Q_NUM'].sum().reset_index()
                                        fig_qty = px.bar(df_monthly, x='DATE_CLEAN', y='Q_NUM', color=c_baku, barmode='group', title="Volume Comparison by Month")
                                        fig_qty.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Quantity", legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=""))
                                        st.plotly_chart(fig_qty, use_container_width=True)
                                    
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
    
    invalid_mask = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')['NOMOR SKU'].isna() | (df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')['NOMOR SKU'].astype(str).str.strip().str.len() < 10)
    df_missing = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')[invalid_mask]
    
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
            st.info("💡 **Silakan review dan edit manual di kolom 'SKU BARU' dan 'TANGGAL' pada tabel di bawah ini jika diperlukan.**")
            
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
# H. FOOTER SISTEM
# ==============================================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #94A3B8; font-size: 12px;'>"
    "ERP Purchasing System v6.1 | Proprietary of PT Panca Budi Idaman Tbk | Created with for Raihan Subakti"
    "</p>", 
    unsafe_allow_html=True
)