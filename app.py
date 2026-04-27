import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import io
import time
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN & TAMPILAN ERP INTERNASIONAL
# ==========================================
st.set_page_config(layout="wide", page_title="ERP Purchasing | Panca Budi", page_icon="🏢")

# --- CUSTOM CSS MODERN SAAS / ERP ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main { background-color: #F8FAFC; }
    
    .stMetric { 
        background-color: #FFFFFF; 
        padding: 24px; 
        border-radius: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid #E2E8F0;
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
    
    .stButton>button { border-radius: 8px; font-weight: 600; letter-spacing: 0.5px; transition: all 0.3s; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SISTEM KONEKSI GOOGLE SHEETS (ID BARU)
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

# --- MESIN PENYEDOT DATA ANTI LAG (CACHE 5 MENIT) ---
@st.cache_data(ttl=300) 
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    return df

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def format_rupiah(angka):
    try:
        val = str(angka).strip()
        if val.upper() in ['NAN', 'NONE', '']: return "Rp 0"
        num_str = re.sub(r'[^0-9]', '', val)
        if num_str: return f"Rp {int(num_str):,}".replace(',', '.')
        return val
    except:
        return "Rp 0"

def parse_numeric(value):
    try:
        if pd.isna(value) or str(value).strip() == "": return 0.0
        s = str(value).strip()
        if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', s): return 0.0
        if not re.match(r'^[-0-9.,]+$', s): return 0.0
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'): s = s.replace('.', '').replace(',', '.')
            else: s = s.replace(',', '')
        elif ',' in s: s = s.replace(',', '.')
        return float(s)
    except: return 0.0

def convert_gdrive_link(url):
    if not isinstance(url, str) or str(url).strip().lower() in ['nan', 'none', '']: return ""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', str(url))
    if match: return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800"
    return str(url)

def extract_code(text):
    try: return text.split('(')[1].split(')')[0].strip().zfill(3) 
    except: return "000"

def generate_new_sku(prefix_val, kat_full, det_full, current_df):
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

# ==========================================
# 4. LOAD & PERSIAPAN MASTER DATA
# ==========================================
try:
    df_master = load_data(GID_MASTER)
    df_master.columns = df_master.columns.str.strip().str.upper()
    df_master = df_master.dropna(subset=['NAMA BAKU'])
    
    if 'KATEGORI' in df_master.columns: df_master['KATEGORI'] = df_master['KATEGORI'].ffill().astype(str).str.strip().str.upper()
    if 'DETAIL KATEGORI' in df_master.columns: df_master['DETAIL KATEGORI'] = df_master['DETAIL KATEGORI'].ffill().astype(str).str.strip().str.upper()
    
    df_master['LOOKUP'] = df_master['NAMA BAKU'].astype(str).str.upper()
    if 'NAMA ITEM' in df_master.columns: df_master['LOOKUP'] += " " + df_master['NAMA ITEM'].fillna("").astype(str).str.upper()
        
    df_master_unique = df_master.drop_duplicates(subset=['NAMA BAKU'], keep='last')
    master_map = df_master_unique.set_index('NAMA BAKU').to_dict('index')
    list_lookup = df_master['LOOKUP'].tolist()
    lookup_to_baku = dict(zip(df_master['LOOKUP'], df_master['NAMA BAKU']))
except Exception as e:
    st.error(f"⚠️ Gagal Load Master Data: {e}"); st.stop()

# ==========================================
# 5. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;'>
            <h1 style='color: #047857; font-weight: 800; margin: 0; font-size: 32px; letter-spacing: -1px;'>PANCA BUDI</h1>
            <p style='color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 2px; margin: 0;'>PURCHASING SYSTEM</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Sync Database", use_container_width=True):
        st.cache_data.clear(); st.rerun()
        
    st.write("") 
    
    menu = option_menu(
        menu_title="", 
        options=["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"],
        icons=["magic", "search", "images", "shop", "bar-chart-line", "tools"], 
        default_index=5,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#64748B", "font-size": "18px"}, 
            "nav-link": {"color": "#334155", "font-weight": "500", "font-size": "15px", "text-align": "left", "margin":"4px 0", "--hover-color": "#F1F5F9", "border-radius": "8px"},
            "nav-link-selected": {"background-color": "#047857", "color": "white", "icon-color": "white", "font-weight": "600"},
        }
    )

# ==========================================
# MENU 1: PEMBERSIHAN PO
# ==========================================
if menu == "Pembersihan PO":
    st.markdown("<h2>✨ Pembersihan Data PO</h2>", unsafe_allow_html=True)
    st.write("Upload laporan mentah dari ERP untuk diproses secara otomatis.")
    
    col_u, col_f = st.columns(2)
    with col_u:
        input_unit = st.selectbox("🏢 Unit Kerja (Default):", ["PBI CPR", "PBI PML", "PBI MAUK", "PP CUP", "PIH", "RA", "PGP", "OFFICE PUSAT"])
    with col_f:
        tipe_format = st.radio("⚙️ Tipe Dokumen:", ["Format ERP (Laporan per No Bukti)", "Format Standar (Tabel Biasa)"])
        
    with st.form("form_upload_erp"):
        uploaded_file = st.file_uploader("📥 Upload File Laporan ERP (.xlsx atau .xls)", type=["xlsx", "xls"])
        btn_proses = st.form_submit_button("🚀 Proses Data Laporan (Enter)", type="primary")

    if btn_proses and uploaded_file:
        try:
            with st.spinner("Mesin sedang membaca tabel Excel..."):
                raw_excel = pd.read_excel(uploaded_file, header=None)
                extracted_rows = []
                
                temp_po, temp_tgl, temp_vendor, temp_curr = "-", "-", "-", "RP"
                
                for idx, row in raw_excel.iterrows():
                    cells = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                    line_text = " | ".join(cells).upper()

                    if not cells or any(x in line_text for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO"]): continue

                    if "INCLUDE" in line_text or "EXCLUDE" in line_text:
                        temp_po = cells[0]
                        for c in cells:
                            date_match = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', c)
                            if date_match: temp_tgl = date_match.group(0); break
                        
                        temp_vendor = "-"
                        for c in cells:
                            if " - " in c: temp_vendor = c.split(" - ")[-1].strip(); break
                        
                        temp_curr = "RP"
                        for m in ["USD", "EUR", "CNY", "JPY"]:
                            if m in line_text: temp_curr = m; break
                        continue

                    if temp_po != "-":
                        val_list = [str(x) for x in row.values if str(x) != 'nan' and str(x).strip() != '']
                        if len(val_list) >= 4:
                            numeric_finds = []
                            for v in reversed(val_list):
                                n = parse_numeric(v)
                                if n is not None and n > 0: numeric_finds.insert(0, n)
                            
                            if len(numeric_finds) >= 2:
                                q_val = numeric_finds[0]
                                p_val = numeric_finds[-1] 
                                
                                item_raw_name = "TIDAK TERBACA"
                                potensi_nama = []
                                for v in val_list:
                                    v_str = str(v).strip()
                                    if re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', v_str): continue
                                    if re.match(r'^[-0-9.,]+$', v_str): continue
                                    if v_str.upper() in ["RP", "USD", "EUR", "CNY", "IDR"]: continue
                                    potensi_nama.append(v_str)
                                
                                if potensi_nama:
                                    item_raw_name = max(potensi_nama, key=len)
                                
                                final_unit = input_unit
                                if "ceper" in uploaded_file.name.lower(): final_unit = "PBI CPR"
                                elif "pemalang" in uploaded_file.name.lower(): final_unit = "PBI PML"
                                elif "ra " in uploaded_file.name.lower() or "royal" in uploaded_file.name.lower(): final_unit = "RA"
                                
                                extracted_rows.append({
                                    "UNIT KERJA": final_unit, "NO PO": temp_po, "TANGGAL": temp_tgl,
                                    "VENDOR": temp_vendor, "MATA UANG": temp_curr, "ITEM_KOTOR": item_raw_name,
                                    "QTY": q_val, "HARGA": p_val
                                })

                df_final_clean = pd.DataFrame(extracted_rows)
                
                if not df_final_clean.empty:
                    st.session_state['df_mentah'] = df_final_clean
                    if 'matched_df' in st.session_state: del st.session_state['matched_df']
                else:
                    st.warning("⚠️ Data kosong! Mesin gagal mendeteksi format ERP Panca Budi (Pastikan ada keterangan INCLUDE/EXCLUDE di file Excel).")
                    if 'df_mentah' in st.session_state: del st.session_state['df_mentah']

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan sistem saat membaca file: {str(e)}")

    if 'df_mentah' in st.session_state and 'matched_df' not in st.session_state:
        df_view_mentah = st.session_state['df_mentah']
        st.success(f"✔️ Berhasil mengekstrak {len(df_view_mentah)} baris item barang.")
        st.write("### 📋 Preview Data Mentah")
        st.dataframe(df_view_mentah, use_container_width=True)
        
        if st.button("🤖 Jalankan AI Matching (Sinkronkan ke Master Barang)", type="primary"):
            with st.spinner("AI sedang mencocokkan nama barang..."):
                matched_results = []
                progress_bar = st.progress(0)
                total_count = len(df_view_mentah)

                for i, r in df_view_mentah.iterrows():
                    progress_bar.progress((i + 1) / total_count)
                    
                    item_to_search = str(r['ITEM_KOTOR']).upper()
                    hasil_match = process.extractOne(item_to_search, search_list, scorer=fuzz.token_set_ratio)
                    
                    if hasil_match and hasil_match[1] >= 75:
                        nama_baku_ketemu = lookup_to_baku_map[hasil_match[0]]
                        info_master = mapping_master.get(nama_baku_ketemu, {})
                        
                        matched_results.append({
                            "UNIT KERJA": r['UNIT KERJA'], "NO PO": r['NO PO'], "TANGGAL": r['TANGGAL'],
                            "VENDOR": r['VENDOR'], "MATA UANG": r['MATA UANG'], "NAMA ASLI": r['ITEM_KOTOR'],
                            "NAMA BAKU": nama_baku_ketemu, "QTY": r['QTY'], 
                            "SATUAN": info_master.get('SATUAN', '-'), "HARGA": r['HARGA'],
                            "KATEGORI": info_master.get('KATEGORI', '-'),
                            "SKU": info_master.get('NOMOR SKU', '-')
                        })
                    else:
                        matched_results.append({
                            "UNIT KERJA": r['UNIT KERJA'], "NO PO": r['NO PO'], "TANGGAL": r['TANGGAL'],
                            "VENDOR": r['VENDOR'], "MATA UANG": r['MATA UANG'], "NAMA ASLI": r['ITEM_KOTOR'],
                            "NAMA BAKU": "⚠️ BARANG BARU (BELUM ADA DI MASTER)", "QTY": r['QTY'], 
                            "SATUAN": "-", "HARGA": r['HARGA'], "KATEGORI": "-", "SKU": "-"
                        })
                
                st.session_state['matched_df'] = pd.DataFrame(matched_results)
                st.rerun()

    if 'matched_df' in st.session_state:
        df_view_final = st.session_state['matched_df']
        st.write("---")
        st.write("### 📑 Review Final & Simpan")
        st.dataframe(df_view_final, use_container_width=True)
        
        c_save, c_cancel = st.columns(2)
        
        with c_save:
            if st.button("💾 Simpan ke Database Transaksi (Google Sheets)", type="primary", use_container_width=True):
                try:
                    with st.spinner("Mengirim data ke awan..."):
                        gc = get_gspread_connection()
                        spread = gc.open_by_key(SHEET_ID)
                        worksheet = spread.get_worksheet_by_id(int(GID_DASHBOARD))
                        
                        data_to_push = df_view_final.fillna("-").values.tolist()
                        worksheet.append_rows(data_to_push)
                        
                        st.balloons()
                        st.success("🔥 BERHASIL! Data sudah masuk ke Database Induk.")
                        del st.session_state['matched_df'] 
                        del st.session_state['df_mentah']
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal Simpan: {e}")
        
        with c_cancel:
            if st.button("❌ Batalkan Semua", use_container_width=True):
                del st.session_state['matched_df']
                if 'df_mentah' in st.session_state: del st.session_state['df_mentah']
                st.rerun()

# ==========================================
# MENU 2: PENCARIAN BARANG
# ==========================================
elif menu == "Pencarian Barang":
    st.markdown("<h2>🔍 Global Search Engine</h2>", unsafe_allow_html=True)
    kata_cari = st.text_input("Ketik Kata Kunci (Nama Barang / SKU):")
    if kata_cari:
        hasil = process.extract(kata_cari, list_lookup, scorer=fuzz.token_set_ratio, limit=10)
        res_list = []
        for m in hasil:
            if m[1] >= 40:
                baku = lookup_to_baku[m[0]]; info = master_map.get(baku, {})
                res_list.append({"Match": f"{m[1]}%", "Nama Baku": baku, "SKU": info.get('NOMOR SKU', '-'), "Kategori": info.get('KATEGORI', '-'), "Est. Harga": format_rupiah(info.get('HARGA', 0)), "Last Vendor": info.get('VENDOR', '-')})
        st.dataframe(pd.DataFrame(res_list), use_container_width=True)

# ==========================================
# MENU 3: E-CATALOG & STUDIO GAMBAR
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio"])
    
    with t_cat:
        col_s, col_f = st.columns([2, 1])
        with col_s: search_cat = st.text_input("🔍 Cari Produk:")
        with col_f:
            list_kat = ["All Categories"] + sorted([k for k in df_master_unique['KATEGORI'].unique() if str(k).strip() != ""])
            filter_cat = st.selectbox("📁 Kategori:", list_kat)
        
        df_show = df_master_unique.copy()
        if filter_cat != "All Categories": df_show = df_show[df_show['KATEGORI'] == filter_cat]
        if search_cat: df_show = df_show[df_show['NAMA BAKU'].astype(str).str.contains(search_cat, case=False) | df_show['NOMOR SKU'].astype(str).str.contains(search_cat, case=False)]
        
        st.markdown("---")
        if df_show.empty: st.warning("Data tidak ditemukan.")
        else:
            cols = st.columns(4)
            for idx, (_, row) in enumerate(df_show.iterrows()):
                with cols[idx % 4]:
                    raw_link = str(row.get('LINK GAMBAR', '')).strip()
                    img_url = convert_gdrive_link(raw_link)
                    
                    if img_url and "drive.google" in img_url:
                        img_element = f"<img src='{img_url}' style='width:100%; height:160px; object-fit:contain; border-radius:8px; margin-bottom:12px;'>"
                    else:
                        img_element = f"<div style='background-color:#F1F5F9; height:160px; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:12px;'><span style='color:#94A3B8; font-weight:600;'>No Image Asset</span></div>"
                    
                    card_html = f"""
                    <div style='background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: 0.3s;'>
                        {img_element}
                        <h5 style='margin-top:0px; font-size:14px; font-weight:700; color:#0F172A; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;'>{row['NAMA BAKU']}</h5>
                        <p style='font-size:11px; color:#64748B; margin:4px 0;'>SKU: {row['NOMOR SKU']}</p>
                        <p style='font-size:15px; font-weight:800; color:#047857; margin-top:8px; margin-bottom:0px;'>{format_rupiah(row.get('HARGA', 0))}</p>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

    with t_studio:
        st.write("### 📸 Inject Image Asset")
        if 'LINK GAMBAR' not in df_master_unique.columns: df_master_unique['LINK GAMBAR'] = ""
            
        empty_mask = df_master_unique['LINK GAMBAR'].isna() | df_master_unique['LINK GAMBAR'].astype(str).str.strip().str.lower().isin(['', 'nan', 'none'])
        df_no_pic = df_master_unique[empty_mask]
        
        if df_no_pic.empty: st.success("Semua aset visual sudah lengkap.")
        else:
            barang_pilih = st.selectbox("Pilih Produk:", df_no_pic['NAMA BAKU'].tolist())
            link_input = st.text_input("G-Drive Link:")
            if link_input:
                st.image(convert_gdrive_link(link_input), width=300)
                if st.button("💾 Upload & Bind", type="primary"):
                    try:
                        with st.spinner("Binding asset..."):
                            client = get_gspread_client(); sheet_master = client.open_by_key(SHEET_ID).get_worksheet(0)
                            cell = sheet_master.find(barang_pilih, in_column=2)
                            if cell:
                                headers = sheet_master.row_values(1)
                                if 'LINK GAMBAR' in headers:
                                    col_link_idx = headers.index('LINK GAMBAR') + 1
                                    sheet_master.update_cell(cell.row, col_link_idx, link_input)
                                    st.success(f"Success!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                                else: st.error("Kolom 'LINK GAMBAR' belum ada di baris pertama Sheet 1 Anda.")
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
# MENU 5: DASHBOARD LAPORAN (MULTI-ITEM COMPARISON)
# ==========================================
elif menu == "Dashboard Laporan":
    st.markdown("<h2>📊 Procurement Intelligence</h2>", unsafe_allow_html=True)
    
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
            
            df_d['H_NUM'] = pd.to_numeric(df_d[c_harga].astype(str).str.upper().str.replace('RP', '').str.replace(r'[^0-9]', '', regex=True), errors='coerce').fillna(0)
            df_d['Q_NUM'] = pd.to_numeric(df_d['QTY'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            df_d['TOTAL'] = df_d['H_NUM'] * df_d['Q_NUM']
            df_d['DATE_CLEAN'] = pd.to_datetime(df_d[c_tgl], errors='coerce')
            df_d = df_d.dropna(subset=['DATE_CLEAN'])
            
            tab_summary, tab_item = st.tabs(["🌐 Corporate Overview", "🔎 Item Analytics (Multi-Select)"])
            
            with tab_summary:
                list_unit = ["All Facilities"] + sorted([u for u in df_d[c_unit].unique() if str(u).strip() != ""])
                filter_unit = st.selectbox("📍 Select Facility:", list_unit)
                df_filtered = df_d[df_d[c_unit] == filter_unit] if filter_unit != "All Facilities" else df_d
                
                st.write("") 
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Procurement Value", format_rupiah(df_filtered['TOTAL'].sum()))
                col2.metric("PO Transactions", f"{df_filtered[c_po].replace('', pd.NA).dropna().nunique()}")
                col3.metric("Active Supply Facilities", f"{df_filtered[c_unit].nunique()}")
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
                list_barang_histori = df_d.drop_duplicates(subset=[c_baku]).sort_values(by=c_baku)[c_baku].tolist()
                
                barang_pilih = st.multiselect("Search Product Intelligence (Bisa pilih lebih dari 1 untuk perbandingan):", list_barang_histori, placeholder="Pilih barang untuk dianalisa...")
                
                if barang_pilih:
                    df_item_histori = df_d[df_d[c_baku].isin(barang_pilih)].sort_values(by='DATE_CLEAN')

                    if len(barang_pilih) == 1:
                        item_tunggal = barang_pilih[0]
                        info_master = df_master_unique[df_master_unique['NAMA BAKU'] == item_tunggal]
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
                                img_url = convert_gdrive_link(str(info_master.iloc[0].get('LINK GAMBAR', '')).strip())
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
                            m1.metric("Item TCO (Total Cost)", format_rupiah(df_item_histori['TOTAL'].sum()))
                            m2.metric("Purchase Frequency", f"{df_item_histori[c_po].nunique()} Orders")
                            m3.metric("Average Unit Price", format_rupiah(df_item_histori['H_NUM'].mean()))
                            m4.metric("Supplier Count", f"{len(v_histori)} Vendors")

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
                            
                            st.markdown("<h4 style='font-size:16px; color:#334155; margin-bottom:10px;'>Transaction Ledger</h4>", unsafe_allow_html=True)
                            df_table = df_item_histori[[c_tgl, c_po, c_unit, 'VENDOR', 'QTY', 'H_NUM', 'TOTAL']].copy()
                            df_table['H_NUM'] = df_table['H_NUM'].map(format_rupiah)
                            df_table['TOTAL'] = df_table['TOTAL'].map(format_rupiah)
                            st.dataframe(df_table, use_container_width=True, hide_index=True)

                    else:
                        st.markdown("<br><h3>⚖️ Multi-Item Comparative Analysis</h3>", unsafe_allow_html=True)
                        st.markdown("<hr style='border:1px solid #E2E8F0; margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
                        
                        if not df_item_histori.empty:
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Combined TCO", format_rupiah(df_item_histori['TOTAL'].sum()))
                            m2.metric("Total Transactions", f"{df_item_histori[c_po].nunique()} Orders")
                            m3.metric("Items Compared", f"{len(barang_pilih)} Items")
                            m4.metric("Total Vendors Involved", f"{df_item_histori['VENDOR'].nunique()} Vendors")

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

        else: st.warning("Data Repository Empty.")
            
    except Exception as e: st.error(f"Engine Fault: {e}")

# ==========================================
# MENU 6: MAINTENANCE DATA
# ==========================================
elif menu == "Maintenance Data":
    st.markdown("<h2>🛠️ System Config & SKU Generator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Modul untuk injeksi SKU secara masif dan perawatan data.</p>", unsafe_allow_html=True)
    
    invalid_mask = df_master_unique['NOMOR SKU'].isna() | (df_master_unique['NOMOR SKU'].astype(str).str.strip().str.len() < 10)
    df_missing = df_master_unique[invalid_mask]
    
    if not df_missing.empty:
        st.warning(f"⚠️ Terdeteksi {len(df_missing)} item yang membutuhkan Nomor SKU.")
        
        # TOMBOL GENERATE PREVIEW
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
                    
                    if c_s and c_k and c_d:
                        preview_data = []
                        for idx, row in df_m.iterrows():
                            val = str(row[c_s]).strip()
                            if len(val) < 10 or val.upper() in ['NAN', 'NONE', 'NULL', '#N/A', '']: 
                                new_sku = generate_new_sku("001", row[c_k], row[c_d], df_m)
                                df_m.at[idx, c_s] = new_sku
                                preview_data.append({
                                    "Baris Excel": idx + 2, 
                                    "NAMA BAKU": row['NAMA BAKU'],
                                    "KATEGORI": row[c_k],
                                    "DETAIL KATEGORI": row[c_d],
                                    "SKU BARU": new_sku
                                })
                        
                        st.session_state['draft_sku_df'] = df_m
                        st.session_state['preview_sku_list'] = pd.DataFrame(preview_data)
                except Exception as e:
                    st.error(f"Error: {e}")

        # MENAMPILKAN TABEL EDITOR
        if 'preview_sku_list' in st.session_state:
            st.info("💡 **Silakan review dan edit manual di kolom 'SKU BARU' pada tabel di bawah ini jika diperlukan. (Misal: menyamakan SKU untuk barang yang sama).**")
            
            edited_preview = st.data_editor(
                st.session_state['preview_sku_list'],
                disabled=["Baris Excel", "NAMA BAKU", "KATEGORI", "DETAIL KATEGORI"],
                use_container_width=True,
                hide_index=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Konfirmasi & Tembak ke Master Data", type="primary", use_container_width=True):
                    with st.spinner("Menyimpan ke Google Sheets..."):
                        try:
                            df_full = st.session_state['draft_sku_df']
                            c_s = next((c for c in df_full.columns if 'SKU' in c), None)
                            
                            for _, row in edited_preview.iterrows():
                                excel_idx = row["Baris Excel"] - 2
                                df_full.at[excel_idx, c_s] = row["SKU BARU"]
                                
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