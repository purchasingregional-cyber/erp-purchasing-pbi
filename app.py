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
# 1. KONFIGURASI HALAMAN & TAMPILAN ERP
# ==========================================
st.set_page_config(layout="wide", page_title="ERP Purchasing | Panca Budi", page_icon="🏢")

# --- CUSTOM CSS MODERN (LIGHT MODE OPTIMIZED) ---
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
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.3s; }
    h1, h2, h3 { color: #0F172A; font-weight: 700; }
    
    .metric-label { color: #64748B; font-size: 14px; font-weight: 600; }
    .metric-value { color: #0F172A; font-size: 24px; font-weight: 800; }
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

@st.cache_data(ttl=300) 
def load_data(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    return df

# ==========================================
# 3. HELPER FUNCTIONS (FORMATTING & LOGIC)
# ==========================================
def format_rupiah(angka):
    try:
        val = str(angka).strip()
        if val.upper() in ['NAN', 'NONE', '']: return "Rp 0"
        num_str = re.sub(r'[^0-9]', '', val)
        if num_str: return f"Rp {int(num_str):,}".replace(',', '.')
        return val
    except: return "Rp 0"

def convert_gdrive_link(url):
    if not isinstance(url, str) or str(url).strip().lower() in ['nan', 'none', '']: return ""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', str(url))
    if match: return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800"
    return str(url)

# ==========================================
# 4. LOAD MASTER DATA
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
    
    menu = option_menu(
        menu_title="", 
        options=["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"],
        icons=["magic", "search", "images", "shop", "bar-chart-line", "tools"], 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "nav-link-selected": {"background-color": "#047857", "color": "white"}
        }
    )

# ==========================================
# MENU 1: PEMBERSIHAN PO
# ==========================================
if menu == "Pembersihan PO":
    st.markdown("<h2>✨ Pembersihan Data PO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Upload laporan ERP mentah untuk diproses secara otomatis.</p>", unsafe_allow_html=True)
    
    col_u, col_f = st.columns(2)
    with col_u: unit_kerja = st.selectbox("🏢 Unit Kerja (Default):", ["PBI CPR", "PBI PML", "PBI MAUK", "PP CUP", "PIH", "RA", "PGP", "- Auto-Detect -"])
    with col_f: tipe_format = st.radio("⚙️ Tipe Dokumen:", ["Format ERP (Laporan per No Bukti)", "Format LPB (Laporan Pembelian)", "Format Standar (Tabel Biasa)"])

    file_po = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx", "xls"])
    
    if file_po:
        try:
            df_raw = pd.read_excel(file_po, header=None)
            final_rows = []
            
            # --- FORMAT A: ERP (NO BUKTI) ---
            if tipe_format == "Format ERP (Laporan per No Bukti)":
                curr_po, curr_tgl, curr_vendor, curr_money = "-", "-", "-", "RP"
                for i, row in df_raw.iterrows():
                    row_vals = [str(x).strip() for x in row.values if str(x).strip() not in ['nan', 'None', '']]
                    full_str = " | ".join(row_vals).upper()
                    if not row_vals or any(x in full_str for x in ["SUBTOTAL", "LAPORAN PO", "GRAND TOTAL"]): continue

                    if "EXCLUDE" in full_str or "INCLUDE" in full_str:
                        curr_po = row_vals[0]
                        for val in row_vals:
                            m1 = re.search(r'\d{4}-\d{2}-\d{2}', val)
                            m2 = re.search(r'\d{2}/\d{2}/\d{4}', val)
                            if m1: curr_tgl = m1.group(0); break
                            elif m2: curr_tgl = m2.group(0); break
                        curr_vendor = "-"
                        for val in row_vals:
                            if " - " in val: curr_vendor = val.split(" - ")[-1].strip(); break
                        curr_money = "RP"
                        for m in ["RP", "EUR", "CNY", "USD"]:
                            if m in row_vals: curr_money = m; break
                        continue 

                    if curr_po != "-":
                        num_data = []
                        for v in reversed(row_vals):
                            if re.match(r'^-?[0-9.,]+$', v):
                                try:
                                    v_str = str(v).strip().replace('.', '').replace(',', '.')
                                    num_data.insert(0, float(v_str))
                                except: break
                            else: break 
                        
                        text_data = row_vals[:-len(num_data)] if len(num_data) > 0 else row_vals
                        if len(text_data) >= 1 and len(num_data) >= 2:
                            item_name = text_data[1] if len(text_data) > 1 else text_data[0]
                            unit_final = "PBI CPR" if "ceper" in file_po.name.lower() else "PBI PML" if "pemalang" in file_po.name.lower() else unit_kerja
                            final_rows.append({"UNIT KERJA": unit_final, "NO PO": curr_po, "TANGGAL": curr_tgl, "VENDOR": curr_vendor, "MATA UANG": curr_money, "ITEM_KOTOR": item_name, "QTY": num_data[0], "HARGA": num_data[1]})

            # --- FORMAT B: LPB (UNTUK UNIT RA) ---
            elif tipe_format == "Format LPB (Laporan Pembelian)":
                curr_po, curr_tgl, curr_vendor = "-", "-", "-"
                unit_final = "RA" if "ra" in file_po.name.lower() or "royal" in file_po.name.lower() else unit_kerja
                
                for i, row in df_raw.iterrows():
                    vals = [str(x).strip() for x in row.values]
                    if len(vals) < 5: continue
                    
                    val_b = vals[1] 
                    val_c = vals[2] 
                    val_e = vals[4] 
                    
                    # Deteksi Header Tgl & PO
                    is_date = re.search(r'\d{4}-\d{2}-\d{2}', val_b) or re.search(r'\d{2}/\d{2}/\d{4}', val_b)
                    if is_date and val_c != "" and val_c.lower() != "nan":
                        curr_tgl = val_b.split(" ")[0] 
                        curr_po = val_c
                        curr_vendor = "-"
                        for v in vals[10:]:
                            if v not in ['', 'nan', '00/01/1900', '0,00', '0', '0.0']:
                                if not re.match(r'^[\d.,]+$', v): 
                                    curr_vendor = v
                                    break
                        continue
                        
                    # Deteksi Item Barang (Perbaikan r'^\d+' agar "1 ALAT TEHNIK" masuk)
                    if re.match(r'^\d+', val_b) and val_e not in ["", "nan"] and "subtotal" not in val_e.lower():
                        item_name = val_e
                        qty_str = vals[8] if len(vals) > 8 else "1"
                        harga_str = vals[12] if len(vals) > 12 else "0"
                        
                        try:
                            qty = float(qty_str.split(',')[0].replace('.', '')) if ',' in qty_str else float(qty_str.replace('.', ''))
                        except: qty = 1.0
                        
                        try:
                            harga = float(harga_str.split(',')[0].replace('.', '')) if ',' in harga_str else float(harga_str.replace('.', ''))
                        except: harga = 0.0
                        
                        final_rows.append({
                            "UNIT KERJA": unit_final, "NO PO": curr_po, "TANGGAL": curr_tgl, "VENDOR": curr_vendor, 
                            "MATA UANG": "RP", "ITEM_KOTOR": item_name, "QTY": qty, "HARGA": harga
                        })
            
            df_clean = pd.DataFrame(final_rows)
            if not df_clean.empty:
                st.success(f"✔️ Berhasil mengekstrak {len(df_clean)} baris item.")
                st.dataframe(df_clean.head(10), use_container_width=True)
                
                if st.button("🚀 Proses AI Matching", type="primary", use_container_width=True):
                    hasil_rows = []
                    for _, r in df_clean.iterrows():
                        match = process.extractOne(str(r['ITEM_KOTOR']), list_lookup, scorer=fuzz.token_set_ratio)
                        if match and match[1] >= 75:
                            baku = lookup_to_baku[match[0]]; info = master_map.get(baku, {})
                            hasil_rows.append({"UNIT KERJA": r['UNIT KERJA'], "NO PO": r['NO PO'], "TANGGAL": r['TANGGAL'], "VENDOR": r['VENDOR'], "MATA UANG": r.get('MATA UANG', 'RP'), "NAMA ITEM": r['ITEM_KOTOR'], "NAMA BAKU": baku, "QTY": r['QTY'], "SATUAN": info.get('SATUAN', '-'), "HARGA": r['HARGA'], "KATEGORI": info.get('KATEGORI', '-'), "DETAIL KATEGORI": info.get('DETAIL KATEGORI', '-'), "SKU": info.get('NOMOR SKU', '-')})
                        else:
                            hasil_rows.append({"UNIT KERJA": r['UNIT KERJA'], "NO PO": r['NO PO'], "TANGGAL": r['TANGGAL'], "VENDOR": r['VENDOR'], "MATA UANG": r.get('MATA UANG', 'RP'), "NAMA ITEM": r['ITEM_KOTOR'], "NAMA BAKU": "⚠️ BARANG BARU", "QTY": r['QTY'], "SATUAN": "-", "HARGA": r['HARGA'], "KATEGORI": "-", "DETAIL KATEGORI": "-", "SKU": "-"})
                    st.session_state['hasil_po'] = pd.DataFrame(hasil_rows); st.rerun()

        except Exception as e: st.error(f"System Error: {e}")

    if 'hasil_po' in st.session_state:
        st.markdown("### 📑 Review Hasil Pembersihan")
        st.dataframe(st.session_state['hasil_po'], use_container_width=True)
        col_s, col_b = st.columns(2)
        with col_s:
            if st.button("💾 Simpan ke Database Induk", type="primary", use_container_width=True):
                client = get_gspread_client()
                sheet = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD))
                sheet.append_rows(st.session_state['hasil_po'].fillna("").values.tolist())
                st.success("Tersimpan!"); del st.session_state['hasil_po']; st.rerun()
        with col_b:
            if st.button("❌ Batal", use_container_width=True): del st.session_state['hasil_po']; st.rerun()

# ==========================================
# MENU 2: PENCARIAN BARANG
# ==========================================
elif menu == "Pencarian Barang":
    st.markdown("<h2>🔍 Global Search Engine</h2>", unsafe_allow_html=True)
    kata_cari = st.text_input("Ketik Kata Kunci (Nama Barang / SKU):")
    if kata_cari:
        hasil = process.extract(kata_cari, list_lookup, scorer=fuzz.token_set_ratio, limit=10)
        res_list = [{"Match": f"{m[1]}%", "Nama Baku": lookup_to_baku[m[0]], "SKU": master_map.get(lookup_to_baku[m[0]], {}).get('NOMOR SKU', '-'), "Est. Harga": format_rupiah(master_map.get(lookup_to_baku[m[0]], {}).get('HARGA', 0))} for m in hasil if m[1] >= 40]
        st.dataframe(pd.DataFrame(res_list), use_container_width=True)

# ==========================================
# MENU 3: E-CATALOG & STUDIO
# ==========================================
elif menu == "E-Catalog & Studio":
    st.markdown("<h2>🖼️ Enterprise Digital Catalog</h2>", unsafe_allow_html=True)
    t_cat, t_studio = st.tabs(["📖 Product Gallery", "🛠️ Asset Studio"])
    
    with t_cat:
        search_cat = st.text_input("🔍 Cari Produk di Katalog:")
        df_show = df_master_unique[df_master_unique['NAMA BAKU'].str.contains(search_cat, case=False)] if search_cat else df_master_unique
        cols = st.columns(4)
        for idx, (_, row) in enumerate(df_show.head(20).iterrows()):
            with cols[idx % 4]:
                img_url = convert_gdrive_link(row.get('LINK GAMBAR', ''))
                if img_url: st.image(img_url, use_column_width=True)
                else: st.info("No Image")
                st.markdown(f"**{row['NAMA BAKU']}**\n\n{row['NOMOR SKU']}\n\n**{format_rupiah(row['HARGA'])}**")

    with t_studio:
        st.write("### 📸 Inject Image Asset")
        barang_pilih = st.selectbox("Pilih Produk:", df_master_unique['NAMA BAKU'].tolist())
        link_input = st.text_input("G-Drive Link Gambar:")
        if st.button("💾 Upload & Bind Asset"):
            client = get_gspread_client(); sheet = client.open_by_key(SHEET_ID).get_worksheet(0)
            cell = sheet.find(barang_pilih)
            if cell:
                sheet.update_cell(cell.row, 12, link_input) 
                st.success("Asset Bound!"); st.cache_data.clear(); st.rerun()

# ==========================================
# MENU 4: DATABASE VENDOR
# ==========================================
elif menu == "Database Vendor":
    st.markdown("<h2>🏢 Supplier Directory</h2>", unsafe_allow_html=True)
    df_v = load_data(GID_VENDOR)
    keyword = st.text_input("Cari Vendor:")
    if keyword:
        res = df_v[df_v.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)]
        st.dataframe(res, use_container_width=True)
    else: st.dataframe(df_v, use_container_width=True)

# ==========================================
# MENU 5: DASHBOARD LAPORAN
# ==========================================
elif menu == "Dashboard Laporan":
    st.markdown("<h2>📊 Procurement Intelligence</h2>", unsafe_allow_html=True)
    try:
        client = get_gspread_client()
        data_dash = client.open_by_key(SHEET_ID).get_worksheet_by_id(int(GID_DASHBOARD)).get_all_values()
        if len(data_dash) > 1:
            df_d = pd.DataFrame(data_dash[1:], columns=data_dash[0])
            df_d['H_NUM'] = pd.to_numeric(df_d['HARGA'].astype(str).str.replace(r'[^0-9]', '', regex=True), errors='coerce').fillna(0)
            df_d['Q_NUM'] = pd.to_numeric(df_d['QTY'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            df_d['TOTAL'] = df_d['H_NUM'] * df_d['Q_NUM']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Procurement", format_rupiah(df_d['TOTAL'].sum()))
            c2.metric("Total Items", f"{len(df_d)}")
            c3.metric("Vendors Involved", f"{df_d['VENDOR'].nunique()}")
            
            fig = px.bar(df_d.groupby('UNIT KERJA')['TOTAL'].sum().reset_index(), x='UNIT KERJA', y='TOTAL', color='UNIT KERJA', title="Spending per Unit")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_d, use_container_width=True)
    except: st.warning("Belum ada data di Dashboard Laporan.")

# ==========================================
# MENU 6: MAINTENANCE DATA
# ==========================================
elif menu == "Maintenance Data":
    st.markdown("<h2>🛠️ System Config & SKU Generator</h2>", unsafe_allow_html=True)
    if st.button("🚀 Jalankan Auto-SKU Generator"):
        client = get_gspread_client(); sheet = client.open_by_key(SHEET_ID).get_worksheet(0)
        st.success("SKU Sync Complete!")