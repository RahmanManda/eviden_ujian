import streamlit as st
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Eviden Ujian", layout="wide")

# --- FUNGSI LOAD DATA ---
# Menggunakan cache agar data tidak didownload berulang kali setiap klik
@st.cache_data
def load_data(url):
    try:
        # Membaca CSV langsung dari Link Publish Google Sheet
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal membaca data: {e}")
        return None

# --- FUNGSI FORMAT GAMBAR ---
def format_drive_link(url):
    """
    Mengubah link 'open?id=' atau 'file/d/' menjadi link thumbnail
    yang bisa dirender oleh browser.
    """
    if not isinstance(url, str):
        return None
    
    # Logika sederhana untuk mengambil ID file Google Drive
    file_id = ""
    if "id=" in url:
        file_id = url.split("id=")[1].split("&")[0]
    elif "/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
    
    if file_id:
        # Mengembalikan URL format thumbnail
        return f"https://drive.google.com/uc?id={file_id}"
    return None

# --- HEADER APLIKASI ---
st.title("📂 Portal E-Eviden & Honor Ujian")
st.markdown("""
Aplikasi ini untuk memudahkan Dosen/Penguji mengunduh bukti pelaksanaan ujian 
(Skripsi, Proposal, Komprehensif) sebagai lampiran keuangan.
""")
st.markdown("---")

# --- INPUT LINK CSV ---
# Nanti link ini bisa kita hardcode jika aplikasi sudah fix
sheet_url = st.text_input("https://docs.google.com/spreadsheets/d/e/2PACX-1vQinSdwQBQZj649QKRimqqmTFQ0WaSlEHucehHOEg7jvTaioDXe0snCcpo3kTJJsnFrIcqEasjif9E8/pub?output=csv", placeholder="https://docs.google.com/spreadsheets/d/e/.../pub?output=csv")

if sheet_url:
    df = load_data(sheet_url)

    if df is not None:
        # --- SIDEBAR FILTER ---
        st.sidebar.header("🔍 Filter Pencarian")
        
        # 1. Deteksi Kolom Nama Dosen (Sesuaikan dengan nama kolom di Sheet Anda)
        # Asumsi nama kolom di Sheet ada kata "Penguji" atau "Dosen"
        possible_name_cols = [c for c in df.columns if "nama" in c.lower() or "dosen" in c.lower() or "penguji" in c.lower()]
        selected_col_name = st.sidebar.selectbox("Pilih Kolom Nama Dosen:", possible_name_cols)
        
        # 2. Input Nama Dosen
        # Mengambil daftar unik nama dosen dari data
        unique_names = sorted(df[selected_col_name].dropna().unique())
        selected_dosen = st.sidebar.selectbox("Pilih Nama Dosen:", unique_names)
        
        # 3. Filter Data
        filtered_df = df[df[selected_col_name] == selected_dosen]
        
        # --- TAMPILAN UTAMA ---
        st.subheader(f"Hasil Pencarian: {selected_dosen}")
        st.info(f"Ditemukan {len(filtered_df)} kegiatan ujian.")

        # Tampilkan Tabel Data Sederhana
        st.dataframe(filtered_df)

        st.markdown("### 📸 Galeri Bukti & Download")
        
        # Loop untuk menampilkan kartu per kegiatan
        for index, row in filtered_df.iterrows():
            with st.container():
                # Membuat tampilan seperti kartu
                c1, c2, c3 = st.columns([1, 1, 2])
                
                # Asumsi kolom foto ada kata "foto" atau "bukti" atau "dokumentasi"
                foto_cols = [c for c in df.columns if "foto" in c.lower() or "upload" in c.lower()]
                
                with c1:
                    st.write(f"**Kegiatan #{index+1}**")
                    # Tampilkan data penting (Timestamp, Jenis Ujian, dll)
                    # Sesuaikan 'Timestamp' dengan nama kolom tanggal di sheet Anda
                    if 'Timestamp' in row:
                        st.write(f"📅 {row['Timestamp']}")
                    
                    # Mencari kolom jenis ujian
                    jenis_ujian = [c for c in df.columns if "jenis" in c.lower() or "ujian" in c.lower()]
                    if jenis_ujian:
                         st.write(f"📝 {row[jenis_ujian[0]]}")

                # Menampilkan Foto (Jika ada link)
                if foto_cols:
                    img_url_raw = row[foto_cols[0]] # Ambil kolom foto pertama
                    img_url_clean = format_drive_link(img_url_raw)
                    
                    with c2:
                        if img_url_clean:
                            st.image(img_url_clean, caption="Bukti Pelaksanaan", width=200)
                        else:
                            st.warning("Tidak ada foto / Link rusak")
                
                with c3:
                    st.success("✅ Data Valid")
                    # Tombol copy link (Simulasi)
                    st.code(row[foto_cols[0]] if foto_cols else "No Link", language="text")
                    st.caption("Salin link di atas jika gambar tidak muncul.")
                
                st.divider()

        # --- TOMBOL DOWNLOAD REKAP ---
        st.sidebar.markdown("---")
        st.sidebar.write("📥 **Unduh Laporan**")
        
        # Konversi data filter ke CSV untuk didownload dosen
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        
        st.sidebar.download_button(
            label="Download Rekap (Excel/CSV)",
            data=csv,
            file_name=f"Rekap_Honor_{selected_dosen}.csv",
            mime="text/csv",
        )

    else:
        st.warning("Menunggu input Link CSV yang valid...")