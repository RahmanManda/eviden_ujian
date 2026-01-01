import streamlit as st
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Eviden Ujian IAIN", layout="wide")

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data(url):
    try:
        # Membaca data
        df = pd.read_csv(url)
        # Convert Timestamp agar bisa disortir
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error membaca data: {e}")
        return None

# --- FUNGSI PEMBERSIH LINK GAMBAR ---
def get_image_url(raw_link):
    """
    Mengubah link drive 'open?id=' menjadi link yang bisa tampil gambar.
    Mendukung multiple link (dipisahkan koma).
    """
    if pd.isna(raw_link) or not isinstance(raw_link, str):
        return []
    
    # Pisahkan jika ada koma (multiple files)
    links = [l.strip() for l in raw_link.split(',')]
    valid_links = []
    
    for link in links:
        file_id = ""
        if "id=" in link:
            file_id = link.split("id=")[1].split("&")[0]
        elif "/d/" in link:
            file_id = link.split("/d/")[1].split("/")[0]
            
        if file_id:
            # Gunakan link thumbnail agar ringan
            valid_links.append(f"https://drive.google.com/uc?id={file_id}")
            
    return valid_links

# --- LOGIKA UTAMA: MENGAMBIL DATA BERDASARKAN JENIS UJIAN ---
def parse_evidence(row):
    """
    Karena kolomnya beda-beda tiap ujian, fungsi ini yang bertugas 'memilih'
    kolom mana yang harus diambil berdasarkan Jenis Ujian.
    """
    jenis = row['Pilih Jenis Ujian']
    
    # Default data kosong
    data = {
        'ba_files': [],
        'foto_files': [],
        'naskah_files': [] # Khusus UAS
    }

    # LOGIKA MAPPING KOLOM (SESUAI CSV ANDA)
    if jenis == 'Ujian Akhir Semester (UAS)':
        data['ba_files'] = get_image_url(row.get('Upload Berita Acara UAS (dalam format PDF/JPG/PNG) '))
        data['foto_files'] = get_image_url(row.get('Foto/Dokumentasi Pelaksanaan UAS   (dalam format PDF/JPG/PNG) '))
        data['naskah_files'] = get_image_url(row.get('Naskah Soal UAS   (dalam format PDF/JPG/PNG) '))
        
    elif jenis == 'Ujian Proposal':
        data['ba_files'] = get_image_url(row.get('Upload Berita Acara Ujian Proposal (dalam format PDF)'))
        data['foto_files'] = get_image_url(row.get('Foto/Dokumentasi Pelaksanaan Ujian Proposal'))
        
    elif jenis == 'Ujian Komprehensif':
        data['ba_files'] = get_image_url(row.get('Upload Berita Acara Ujian Komprehensif (dalam format PDF)'))
        data['foto_files'] = get_image_url(row.get('Foto/Dokumentasi Pelaksanaan Ujian Komprehensif'))
        
    elif jenis == 'Ujian Skripsi':
        data['ba_files'] = get_image_url(row.get('Upload Berita Acara Ujian Skripsi (dalam format PDF)'))
        data['foto_files'] = get_image_url(row.get('Foto/Dokumentasi Pelaksanaan Ujian Skripsi'))
        
    return data

# --- START APLIKASI ---
st.title("🎓 Portal Evidence Ujian")

# --- 1. INPUT DATA SOURCE ---
# GANTI LINK INI DENGAN LINK 'PUBLISH TO WEB' MILIK ANDA (CSV FORMAT)
default_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQinSdwQBQZj649QKRimqqmTFQ0WaSlEHucehHOEg7jvTaioDXe0snCcpo3kTJJsnFrIcqEasjif9E8/pub?output=csv" 

# Jika belum di hardcode, munculkan input box
if "http" not in default_url:
    url = st.text_input("Masukkan Link CSV Google Sheet (Publish to Web):")
else:
    url = default_url

if url:
    df = load_data(url)
    
    if df is not None:
        # --- 2. SIDEBAR FILTER ---
        st.sidebar.header("🔍 Filter Dosen")
        
        # Ambil daftar nama dosen (hapus yang kosong)
        daftar_dosen = sorted([x for x in df['Nama Dosen'].unique() if pd.notna(x)])
        selected_dosen = st.sidebar.selectbox("Pilih Nama Dosen:", daftar_dosen)
        
        # Filter dataframe
        df_dosen = df[df['Nama Dosen'] == selected_dosen].copy()
        
        # --- 3. TAMPILAN UTAMA ---
        st.subheader(f"Rekap Kegiatan: {selected_dosen}")
        
        # Metric ringkas
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Kegiatan", len(df_dosen))
        col_m2.metric("Ujian Skripsi/Tesis", len(df_dosen[df_dosen['Pilih Jenis Ujian'].str.contains('Skripsi', na=False)]))
        col_m3.metric("UAS", len(df_dosen[df_dosen['Pilih Jenis Ujian'].str.contains('UAS', na=False)]))
        
        st.divider()

        # Loop setiap baris data dosen tersebut
        for idx, row in df_dosen.iterrows():
            evidence = parse_evidence(row)
            
            with st.expander(f"{row['Timestamp'].strftime('%d %b %Y')} - {row['Pilih Jenis Ujian']} ({row.get('Nama Matkul', '-')})", expanded=True):
                
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.markdown("#### Detail Kegiatan")
                    st.write(f"**Prodi:** {row.get('Program Studi', '-')}")
                    st.write(f"**Semester:** {row.get('Semester', '-')}")
                    if pd.notna(row.get('Nama Kelas')):
                        st.write(f"**Kelas:** {row['Nama Kelas']}")
                    
                    st.info("Klik kanan pada gambar -> 'Save Image' untuk mengunduh bukti.")

                with c2:
                    st.markdown("#### 📸 Bukti Dokumentasi")
                    
                    # Tampilkan Tab jika ada banyak jenis bukti
                    tab1, tab2, tab3 = st.tabs(["Foto Pelaksanaan", "Berita Acara", "Naskah Soal"])
                    
                    with tab1:
                        if evidence['foto_files']:
                            # Tampilkan gallery
                            cols = st.columns(len(evidence['foto_files']))
                            for i, img_url in enumerate(evidence['foto_files']):
                                cols[i].image(img_url, width=200, caption=f"Foto {i+1}")
                        else:
                            st.warning("Tidak ada foto pelaksanaan.")
                            
                    with tab2:
                        if evidence['ba_files']:
                            for img_url in evidence['ba_files']:
                                st.image(img_url, width=200, caption="Berita Acara")
                        else:
                            st.warning("Tidak ada Berita Acara.")

                    with tab3:
                        if evidence['naskah_files']:
                            for img_url in evidence['naskah_files']:
                                st.image(img_url, width=200, caption="Naskah Soal")
                        else:
                            st.write("-")

        # --- 4. DOWNLOAD REKAP ---
        st.sidebar.markdown("---")
        
        # Buat dataframe bersih untuk didownload (Hanya kolom penting)
        download_df = df_dosen[['Timestamp', 'Nama Dosen', 'Pilih Jenis Ujian', 'Program Studi', 'Nama Matkul', 'Nama Kelas']]
        csv = download_df.to_csv(index=False).encode('utf-8')
        
        st.sidebar.download_button(
            "📥 Download Rekap (Excel/CSV)",
            csv,
            f"Laporan_{selected_dosen}.csv",
            "text/csv"
        )

