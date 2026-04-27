# ==============================================================================
# SISTEM ERP PURCHASING - PT PANCA BUDI IDAMAN TBK
# Developer Helper: Gemini AI
# User: Raihan Subakti (Regional Purchasing)
# Versi: 3.1.0 (Full Version - LPB RA Fix & Anti-Error Excel)
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
import io
import time
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from streamlit_option_menu import option_menu
import plotly.express as px

# ------------------------------------------------------------------------------
# A. KONFIGURASI DASAR & TEMA (LIGHT MODE)
# ------------------------------------------------------------------------------
st.set_page_config(
    layout="wide", 
    page_title="ERP Purchasing PBI | Management System", 
    page_icon="🏢"
)

# Pengaturan Style CSS 
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #F1F5F9;
    }

    .stMetric {
        background-color: #FFFFFF !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #059669;
        color: white;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #047857;
        border: none;
        color: white;
    }

    h1, h2, h3 {
        color: #1E293B !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# B. DATABASE & KONEKSI API (INTEGRASI GOOGLE SHEETS)
# ------------------------------------------------------------------------------
SHEET_ID = "1EJnbmhufaKfKEQmAmkQFYvJZ9_Kx_vJ7C1HvcyzK4WQ"

GID_MASTER    = "0"           # Tab: DATABASE MASTER
GID_VENDOR    = "168217676"   # Tab: DATABASE VENDOR
GID_DASHBOARD = "1722600044"  # Tab: DATA TRANSAKSI (DASHBOARD)

def get_gspread_connection():
    """Membangun koneksi aman ke Google Sheets."""
    try:
        secret_data = json.loads(st.secrets["google_json"])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        kredensial = Credentials.from_service_account_info(secret_data, scopes=scope)
        return gspread.authorize(kredensial)
    except Exception as e:
        st.error(f"❌ Koneksi API Gagal: {str(e)}")
        return None

@st.cache_data(ttl=300) 
def fetch_spreadsheet_data(gid_id):
    """Mengambil data dari Google Sheets."""
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid_id}"
        data_frame = pd.read_csv(csv_url)
        return data_frame
    except Exception as e:
        st.error(f"⚠️ Gagal menarik data GID {gid_id}: {str(e)}")
        return pd.DataFrame()

# ------------------------------------------------------------------------------
# C. FUNGSI PENDUKUNG (DATA CLEANING & FORMATTING)
# ------------------------------------------------------------------------------
def idr_format(nominal):
    try:
        if pd.isna(nominal) or nominal == "": return "Rp 0"
        clean_num = re.sub(r'[^0-9]', '', str(nominal))
        if clean_num == "": return "Rp 0"
        return f"Rp {int(clean_num):,}".replace(',', '.')
    except:
        return "Rp 0"

def parse_numeric(value):
    try:
        if pd.isna(value) or str(value).strip() == "": return 0.0
        s = str(value).strip()
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'): s = s.replace('.', '').replace(',', '.')
            else: s = s.replace(',', '')
        elif ',' in s: s = s.replace(',', '.')
        else: pass 
        return float(s)
    except:
        return 0.0

def get_thumbnail_url(drive_url):
    if not isinstance(drive_url, str) or drive_url.strip() == "": return ""
    file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_url)
    if file_id_match:
        return f"https://drive.google.com/thumbnail?id={file_id_match.group(1)}&sz=w800"
    return drive_url

# ------------------------------------------------------------------------------
# D. PROSES LOADING MASTER DATA 
# ------------------------------------------------------------------------------
with st.spinner("Sedang Sinkronisasi Database Panca Budi..."):
    master_raw = fetch_spreadsheet_data(GID_MASTER)
    
    if not master_raw.empty:
        master_raw.columns = master_raw.columns.str.strip().str.upper()
        master_data = master_raw.dropna(subset=['NAMA BAKU']).copy()
        
        if 'KATEGORI' in master_data.columns:
            master_data['KATEGORI'] = master_data['KATEGORI'].ffill()
        
        master_data['AI_LOOKUP'] = master_data['NAMA BAKU'].astype(str).str.upper()
        if 'NAMA ITEM' in master_data.columns:
            master_data['AI_LOOKUP'] += " " + master_data['NAMA ITEM'].fillna("").astype(str).str.upper()
        
        master_unique = master_data.drop_duplicates(subset=['NAMA BAKU'], keep='last')
        mapping_master = master_unique.set_index('NAMA BAKU').to_dict('index')
        
        search_list = master_data['AI_LOOKUP'].tolist()
        lookup_to_baku_map = dict(zip(master_data['AI_LOOKUP'], master_data['NAMA BAKU']))
    else:
        st.error("Database Master Kosong! Periksa Google Sheets Anda.")
        st.stop()

# ------------------------------------------------------------------------------
# E. SIDEBAR & MENU NAVIGASI
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: #059669; margin:0;'>PANCA BUDI</h1>
            <p style='color: #64748B; font-weight: bold; letter-spacing: 2px;'>ERP PURCHASING</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🔄 Paksa Sinkron Data"):
        st.cache_data.clear()
        st.rerun()
    
    selected_menu = option_menu(
        menu_title=None,
        options=["Pembersihan PO", "Pencarian Barang", "E-Catalog & Studio", "Database Vendor", "Dashboard Laporan", "Maintenance Data"],
        icons=["stars", "search", "grid", "truck", "graph-up", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#E2E8F0"},
            "nav-link-selected": {"background-color": "#059669", "color": "white"},
        }
    )
    
    st.divider()
    st.info(f"**User Active:**\n{st.session_state.get('user_name', 'Raihan Subakti')}\n\n**Role:**\nRegional Purchasing")

# ------------------------------------------------------------------------------
# F. LOGIKA MODUL - MENU 1: PEMBERSIHAN PO 
# ------------------------------------------------------------------------------
if selected_menu == "Pembersihan PO":
    st.markdown("## ✨ Pembersihan Data PO & LPB")
    st.write("Ubah laporan mentah dari ERP menjadi data bersih yang siap masuk database.")
    
    box_1, box_2 = st.columns(2)
    with box_1:
        input_unit = st.selectbox(
            "🏢 Pilih Unit Kerja:", 
            ["PBI CPR", "PBI PML", "PBI MAUK", "PP CUP", "PIH", "RA", "PGP", "OFFICE PUSAT"],
            help="Tentukan unit asal data jika sistem tidak mendeteksi otomatis."
        )
        
    with box_2:
        input_format = st.radio(
            "⚙️ Jenis Laporan Excel:",
            ["Format ERP (Laporan per No Bukti)", "Format LPB (Laporan Pembelian/RA)"],
            horizontal=True
        )

    uploaded_file = st.file_uploader("📥 Upload File Laporan (.xlsx atau .xls)", type=["xlsx", "xls"])

    if uploaded_file:
        try:
            raw_excel = pd.read_excel(uploaded_file, header=None)
            extracted_rows = []
            
            # --- LOGIKA A: FORMAT ERP STANDAR ---
            if input_format == "Format ERP (Laporan per No Bukti)":
                st.info("Memproses dengan Mesin ERP Standar...")
                
                temp_po, temp_tgl, temp_vendor, temp_curr = "-", "-", "-", "RP"
                
                for idx, row in raw_excel.iterrows():
                    cells = [str(c).strip() for c in row.values if str(c).strip() not in ['nan', 'None', '']]
                    line_text = " | ".join(cells).upper()

                    if not cells or any(x in line_text for x in ["SUBTOTAL", "GRAND TOTAL", "LAPORAN PO"]):
                        continue

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
                        val_list = [str(x) for x in row.values if str(x) != 'nan']
                        if len(val_list) >= 4:
                            item_raw_name = val_list[1] if len(val_list) > 1 else val_list[0]
                            
                            numeric_finds = []
                            for v in reversed(val_list):
                                try:
                                    n = parse_numeric(v)
                                    if n > 0: numeric_finds.insert(0, n)
                                except: pass
                            
                            if len(numeric_finds) >= 2:
                                q_val = numeric_finds[0]
                                p_val = numeric_finds[-1] 
                                
                                final_unit = input_unit
                                if "ceper" in uploaded_file.name.lower(): final_unit = "PBI CPR"
                                elif "pemalang" in uploaded_file.name.lower(): final_unit = "PBI PML"
                                
                                extracted_rows.append({
                                    "UNIT KERJA": final_unit, "NO PO": temp_po, "TANGGAL": temp_tgl,
                                    "VENDOR": temp_vendor, "MATA UANG": temp_curr, "ITEM_KOTOR": item_raw_name,
                                    "QTY": q_val, "HARGA": p_val
                                })

            # --- LOGIKA B: FORMAT LPB / RA ---
            elif input_format == "Format LPB (Laporan Pembelian/RA)":
                st.info("Memproses dengan Mesin LPB Khusus RA...")
                
                temp_po, temp_tgl, temp_vendor = "-", "-", "-"
                
                final_unit = input_unit
                if "ra" in uploaded_file.name.lower() or "royal" in uploaded_file.name.lower():
                    final_unit = "RA"
                    st.success("✅ Terdeteksi File Unit RA")

                for idx, row in raw_excel.iterrows():
                    row_data = [str(x).strip() for x in row.values]
                    
                    if len(row_data) < 5: continue 

                    val_b = row_data[1] if len(row_data) > 1 else ""
                    val_c = row_data[2] if len(row_data) > 2 else ""
                    val_e = row_data[4] if len(row_data) > 4 else ""

                    # 1. DETEKSI HEADER
                    is_date_header = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', val_b)
                    if is_date_header and val_c not in ["nan", ""]:
                        temp_tgl = val_b.split(" ")[0] 
                        temp_po = val_c
                        
                        temp_vendor = "CASH / TANPA NAMA"
                        if len(row_data) > 10:
                            for v in row_data[10:]: 
                                if v not in ["nan", "", "0", "0,00", "00/01/1900"]:
                                    if re.search(r'[A-Za-z]', v):
                                        temp_vendor = v
                                        break
                        continue

                    # 2. DETEKSI ITEM BARANG
                    if re.match(r'^\d+', val_b) and val_e not in ["nan", ""]:
                        if "subtotal" in val_e.lower() or "total" in val_e.lower():
                            continue
                            
                        # Mencegah Error jika kolom harganya kepotong
                        qty_raw = row_data[8] if len(row_data) > 8 else "1"
                        prc_raw = row_data[13] if len(row_data) > 13 else "0"
                        
                        try:
                            real_qty = parse_numeric(qty_raw)
                            real_prc = parse_numeric(prc_raw)
                            
                            extracted_rows.append({
                                "UNIT KERJA": final_unit, "NO PO": temp_po, "TANGGAL": temp_tgl,
                                "VENDOR": temp_vendor, "MATA UANG": "RP", "ITEM_KOTOR": val_e,
                                "QTY": real_qty, "HARGA": real_prc
                            })
                        except Exception as e:
                            st.warning(f"Error membaca angka di baris Excel ke-{idx}")

            # --- PROSES VALIDASI & AI MATCHING ---
            df_final_clean = pd.DataFrame(extracted_rows)
            
            if not df_final_clean.empty:
                st.write(f"### 📋 Preview Data Mentah ({len(df_final_clean)} Baris)")
                st.dataframe(df_final_clean, use_container_width=True)
                
                if st.button("🚀 Jalankan AI Matching (Sinkronkan ke Master Barang)", type="primary"):
                    st.write("---")
                    st.write("### 🤖 Hasil Analisis AI")
                    
                    matched_results = []
                    progress_bar = st.progress(0)
                    total_count = len(df_final_clean)

                    for i, r in df_final_clean.iterrows():
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
                    st.success("✅ AI Selesai Menganalisis!")
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan sistem saat membaca file: {str(e)}")

    if 'matched_df' in st.session_state:
        df_view = st.session_state['matched_df']
        st.write("---")
        st.write("### 📑 Review Final & Simpan")
        st.dataframe(df_view, use_container_width=True)
        
        c_save, c_cancel = st.columns(2)
        
        with c_save:
            if st.button("💾 Simpan ke Database Transaksi (Google Sheets)", type="primary"):
                try:
                    with st.spinner("Mengirim data ke awan..."):
                        gc = get_gspread_connection()
                        spread = gc.open_by_key(SHEET_ID)
                        worksheet = spread.get_worksheet_by_id(int(GID_DASHBOARD))
                        
                        data_to_push = df_view.fillna("-").values.tolist()
                        worksheet.append_rows(data_to_push)
                        
                        st.balloons()
                        st.success("🔥 BERHASIL! Data sudah masuk ke Database Induk.")
                        del st.session_state['matched_df'] 
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal Simpan: {e}")
        
        with c_cancel:
            if st.button("🗑️ Batalkan Semua"):
                del st.session_state['matched_df']
                st.rerun()

# ------------------------------------------------------------------------------
# G. MODUL LAIN 
# ------------------------------------------------------------------------------
elif selected_menu == "Pencarian Barang":
    st.markdown("## 🔍 Mesin Pencari Barang Global")
    keyword = st.text_input("Ketik Nama Sparepart atau Kode SKU:", placeholder="Contoh: Accu, V-Belt, 001-...")
    
    if keyword:
        results = process.extract(keyword.upper(), search_list, limit=15, scorer=fuzz.token_set_ratio)
        
        final_search = []
        for res in results:
            if res[1] >= 30: 
                baku = lookup_to_baku_map[res[0]]
                info = mapping_master.get(baku, {})
                final_search.append({
                    "Match": f"{int(res[1])}%",
                    "Nama Barang": baku,
                    "SKU": info.get('NOMOR SKU', '-'),
                    "Kategori": info.get('KATEGORI', '-'),
                    "Last Price": idr_format(info.get('HARGA', 0)),
                    "Satuan": info.get('SATUAN', '-')
                })
        
        if final_search:
            st.table(pd.DataFrame(final_search))
        else:
            st.warning("Barang tidak ditemukan.")

elif selected_menu == "Dashboard Laporan":
    st.markdown("## 📊 Procurement Intelligence Dashboard")
    
    df_trans = fetch_spreadsheet_data(GID_DASHBOARD)
    
    if not df_trans.empty:
        df_trans['HARGA_N'] = pd.to_numeric(df_trans['HARGA'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        df_trans['QTY_N'] = pd.to_numeric(df_trans['QTY'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        df_trans['TOTAL'] = df_trans['HARGA_N'] * df_trans['QTY_N']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spending", idr_format(df_trans['TOTAL'].sum()))
        m2.metric("Total Transaksi", f"{len(df_trans)} Baris")
        m3.metric("Vendor Aktif", f"{df_trans['VENDOR'].nunique()}")
        m4.metric("Item Terdaftar", f"{df_trans['NAMA BAKU'].nunique()}")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        
        with c1:
            fig_unit = px.pie(df_trans, values='TOTAL', names='UNIT KERJA', title="Distribusi Spending per Plant", hole=0.4)
            st.plotly_chart(fig_unit, use_container_width=True)
            
        with c2:
            top_v = df_trans.groupby('VENDOR')['TOTAL'].sum().reset_index().sort_values('TOTAL', ascending=False).head(10)
            fig_v = px.bar(top_v, x='TOTAL', y='VENDOR', orientation='h', title="Top 10 Vendor (By Volume Spending)", color='TOTAL', color_continuous_scale='Greens')
            st.plotly_chart(fig_v, use_container_width=True)
            
        st.write("### 📜 Histori Transaksi Terakhir")
        st.dataframe(df_trans.tail(50), use_container_width=True)
        
    else:
        st.info("Belum ada data transaksi tersimpan di Database Induk.")

elif selected_menu == "E-Catalog & Studio":
    st.markdown("## 🖼️ Enterprise Digital Catalog")
    
    t_gallery, t_upload = st.tabs(["📖 Galeri Produk", "🛠️ Asset Studio (Update Gambar)"])
    
    with t_gallery:
        search_cat = st.text_input("🔍 Filter Katalog:", placeholder="Cari nama barang...")
        
        df_cat = master_unique.copy()
        if search_cat:
            df_cat = df_cat[df_cat['NAMA BAKU'].str.contains(search_cat, case=False)]
            
        rows_cat = df_cat.head(40)
        cols = st.columns(4)
        
        for i, (idx, row) in enumerate(rows_cat.iterrows()):
            with cols[i % 4]:
                st.markdown(f"""
                <div style='background: white; padding: 10px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;'>
                    <img src='{get_thumbnail_url(row.get('LINK GAMBAR', ''))}' style='width:100%; border-radius: 5px; height: 150px; object-fit: cover; margin-bottom: 10px;' onerror="this.src='https://via.placeholder.com/150?text=No+Image';">
                    <p style='font-size: 13px; font-weight: bold; margin-bottom: 2px; height: 40px; overflow: hidden;'>{row['NAMA BAKU']}</p>
                    <p style='font-size: 11px; color: #666; margin-bottom: 8px;'>{row.get('NOMOR SKU', '-')}</p>
                    <p style='font-size: 14px; color: #059669; font-weight: bold;'>{idr_format(row.get('HARGA', 0))}</p>
                </div>
                """, unsafe_allow_html=True)

    with t_upload:
        st.write("### 🛠️ Hubungkan Gambar dari Google Drive")
        st.write("Cukup masukkan Link Share Google Drive, robot akan otomatis mengupdate katalog.")
        
        with st.form("form_asset"):
            pilih_barang = st.selectbox("Pilih Barang yang mau diupdate:", master_unique['NAMA BAKU'].tolist())
            link_drive = st.text_input("Paste Link G-Drive di sini:")
            btn_submit = st.form_submit_button("Simpan Perubahan")
            
            if btn_submit:
                try:
                    gc = get_gspread_connection()
                    sh = gc.open_by_key(SHEET_ID).get_worksheet(0) 
                    
                    cell = sh.find(pilih_barang)
                    if cell:
                        sh.update_cell(cell.row, 12, link_drive) 
                        st.success(f"Berhasil! Gambar {pilih_barang} telah diperbarui.")
                        st.cache_data.clear()
                    else:
                        st.error("Barang tidak ditemukan di spreadsheet.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ------------------------------------------------------------------------------
# H. FOOTER SISTEM
# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #94A3B8; font-size: 12px;'>"
    "ERP Purchasing System v3.1 | Proprietary of PT Panca Budi Idaman Tbk | Created with ❤️ for Raihan Subakti"
    "</p>", 
    unsafe_allow_html=True
)