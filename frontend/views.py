import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os
import zipfile

# Import Django components
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from .models import HomePage, YearlyMap  # Sesuaikan jika nama app Anda berbeda


# --- Fungsi Bantuan: Menjalankan Analisis Korelasi Multi-Year ---
def run_correlation_analysis_multi_year(csv_files_dict):
    """
    Analisis korelasi untuk multiple tahun.
    csv_files_dict: {2022: 'path/to/2022.csv', 2023: 'path/to/2023.csv', ...}
    """
    analysis_dir_name = "analysis"
    output_dir = os.path.join(settings.MEDIA_ROOT, analysis_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    # Load dan gabungkan data dari semua tahun
    all_data = {}
    for year, csv_path in csv_files_dict.items():
        df = pd.read_csv(csv_path)
        # Ambil kolom numerik (makanan dan non-makanan)
        numeric_cols = [col for col in df.columns if col != 'kabupaten']
        
        for col in numeric_cols:
            if 'makanan' in col.lower() or 'bukan' in col.lower():
                # Bersihkan dan convert ke numeric
                if df[col].dtype == "object":
                    df[col] = df[col].str.replace('"', "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
                # Simpan dengan nama yang include tahun
                if 'bukan' in col.lower():
                    all_data[f"{year}_Non"] = df[col]
                else:
                    all_data[f"{year}_Mkn"] = df[col]
    
    # Buat DataFrame gabungan
    df_combined = pd.DataFrame(all_data).dropna()
    
    # Pisahkan kolom makanan dan non-makanan
    food_cols = [col for col in df_combined.columns if '_Mkn' in col]
    non_food_cols = [col for col in df_combined.columns if '_Non' in col]
    
    # Korelasi makanan
    if len(food_cols) > 1:
        corr_makanan = df_combined[food_cols].corr()
        mkn_heatmap_path = os.path.join(output_dir, "correlation_heatmap_MAKANAN.png")
        corr_makanan.to_csv(
            os.path.join(output_dir, "correlation_matrix_MAKANAN.csv"), index=True
        )
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            corr_makanan,
            annot=True,
            fmt=".2f",
            cmap="Blues",
            linewidths=0.5,
            cbar_kws={"label": "Korelasi"},
        )
        plt.title("Korelasi Pengeluaran Makanan Antar Tahun", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(mkn_heatmap_path)
        plt.close()
    else:
        corr_makanan = pd.DataFrame()
    
    # Korelasi non-makanan
    if len(non_food_cols) > 1:
        corr_non_makanan = df_combined[non_food_cols].corr()
        non_mkn_heatmap_path = os.path.join(
            output_dir, "correlation_heatmap_NON_MAKANAN.png"
        )
        corr_non_makanan.to_csv(
            os.path.join(output_dir, "correlation_matrix_NON_MAKANAN.csv"), index=True
        )
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            corr_non_makanan,
            annot=True,
            fmt=".2f",
            cmap="Greens",
            linewidths=0.5,
            cbar_kws={"label": "Korelasi"},
        )
        plt.title("Korelasi Pengeluaran Non-Makanan Antar Tahun", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(non_mkn_heatmap_path)
        plt.close()
    else:
        corr_non_makanan = pd.DataFrame()
    
    return {
        "mkn_heatmap_url": os.path.join(
            settings.MEDIA_URL, analysis_dir_name, "correlation_heatmap_MAKANAN.png"
        ),
        "non_mkn_heatmap_url": os.path.join(
            settings.MEDIA_URL, analysis_dir_name, "correlation_heatmap_NON_MAKANAN.png"
        ),
        "mkn_matrix": corr_makanan.to_html(
            classes=["table", "table-bordered", "table-striped"]
        ) if not corr_makanan.empty else "<p>Tidak ada data korelasi makanan</p>",
        "non_mkn_matrix": corr_non_makanan.to_html(
            classes=["table", "table-bordered", "table-striped"]
        ) if not corr_non_makanan.empty else "<p>Tidak ada data korelasi non-makanan</p>",
    }


# Backward compatibility - keep old function name
def run_correlation_analysis(csv_file_path):
    """Wrapper untuk compatibility dengan code lama"""
    # Ambil tahun dari nama file jika bisa
    import re
    year_match = re.search(r'(\d{4})', os.path.basename(csv_file_path))
    year = int(year_match.group(1)) if year_match else 2024
    
    return run_correlation_analysis_multi_year({year: csv_file_path})


def home(request):
    # Ambil konfigurasi halaman utama
    try:
        config = HomePage.objects.first()
        if not config:
            context = {
                "title": "Konfigurasi Belum Tersedia",
                "error": "Silakan lengkapi konfigurasi di Admin Dashboard.",
            }
            return render(request, "frontend/index.html", context)
    except Exception:
        context = {
            "title": "Kesalahan Database",
            "error": "Gagal memuat model HomePage.",
        }
        return render(request, "frontend/index.html", context)

    # Ambil semua peta per tahun yang aktif
    yearly_maps = YearlyMap.objects.filter(is_active=True).order_by('tahun')
    
    # Ambil semua CSV untuk analisis multi-year
    maps_with_csv = YearlyMap.objects.filter(is_active=True, data_csv__isnull=False)
    
    # Jalankan analisis korelasi jika ada CSV
    analysis_results = None
    if maps_with_csv.exists():
        try:
            # Buat dictionary {tahun: path_csv}
            csv_files_dict = {}
            for yearly_map in maps_with_csv:
                csv_files_dict[yearly_map.tahun] = yearly_map.data_csv.path
            
            # Run analisis multi-year
            analysis_results = run_correlation_analysis_multi_year(csv_files_dict)
        except Exception as e:
            # Jika analisis gagal, lanjutkan tanpa analisis
            print(f"Error running correlation analysis: {e}")
            analysis_results = None

    # Siapkan context untuk template
    context = {
        "title": config.name,
        "config": config,
        "yearly_maps": yearly_maps,
    }
    
    # Tambahkan hasil analisis jika ada
    if analysis_results:
        context.update({
            "mkn_heatmap_url": analysis_results["mkn_heatmap_url"],
            "non_mkn_heatmap_url": analysis_results["non_mkn_heatmap_url"],
            "mkn_matrix_html": analysis_results["mkn_matrix"],
            "non_mkn_matrix_html": analysis_results["non_mkn_matrix"],
            "download_zip_url": "/download/analysis/",
        })
    
    return render(request, "frontend/index.html", context)


def fullscreen_map(request):
    """View untuk halaman peta fullscreen - redirect ke tahun terbaru"""
    try:
        # Ambil peta tahun terbaru
        latest_map = YearlyMap.objects.filter(is_active=True).order_by('-tahun').first()
        
        if not latest_map:
            context = {
                'title': 'Peta Fullscreen',
                'error': 'Belum ada peta yang tersedia. Silakan tambahkan data melalui admin.'
            }
            return render(request, 'frontend/fullscreen_map.html', context)
        
        # Redirect ke fullscreen tahun terbaru
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('frontend:yearly_fullscreen', args=[latest_map.tahun]))
        
    except Exception as e:
        context = {
            'title': 'Peta Fullscreen',
            'error': f'Terjadi kesalahan: {str(e)}'
        }
        return render(request, 'frontend/fullscreen_map.html', context)


def download_analysis_zip(request):
    # Ambil konfigurasi
    config = get_object_or_404(HomePage, pk=HomePage.objects.first().pk)
    
    # Ambil CSV dari peta pertama yang ada
    first_map_with_csv = YearlyMap.objects.filter(is_active=True, data_csv__isnull=False).first()
    
    if not first_map_with_csv or not first_map_with_csv.data_csv:
        return HttpResponse("Tidak ada data CSV yang tersedia untuk didownload.", status=404)

    original_csv_path = first_map_with_csv.data_csv.path

    # Jalankan analisis lagi (sebagai fallback) jika file belum ada
    analysis_dir = os.path.join(settings.MEDIA_ROOT, "analysis")

    # Cek apakah file hasil analisis sudah ada
    if not os.path.exists(os.path.join(analysis_dir, "correlation_matrix_MAKANAN.csv")):
        # Jika tidak ada, jalankan analisis
        run_correlation_analysis(original_csv_path)

    # Daftar file yang akan di-zip
    files_to_zip = [
        original_csv_path,
        os.path.join(analysis_dir, "correlation_matrix_MAKANAN.csv"),
        os.path.join(analysis_dir, "correlation_matrix_NON_MAKANAN.csv"),
        os.path.join(analysis_dir, "correlation_heatmap_MAKANAN.png"),
        os.path.join(analysis_dir, "correlation_heatmap_NON_MAKANAN.png"),
    ]

    # Buat buffer ZIP in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_zip:
            if os.path.exists(file_path):
                # Memberi nama file yang bersih di dalam ZIP
                arcname = os.path.basename(file_path)
                zf.write(file_path, arcname)

    zip_buffer.seek(0)

    # Buat respons download
    filename = f"QGIS_Analysis_Papua_{config.tahun_mulai}-{config.tahun_akhir}.zip"
    response = HttpResponse(zip_buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def yearly_map_fullscreen(request, tahun):
    """View untuk halaman peta fullscreen per tahun"""
    try:
        yearly_map = get_object_or_404(YearlyMap, tahun=tahun, is_active=True)
        
        # Ambil config HomePage untuk metadata
        homepage_config = HomePage.objects.first()
        
        context = {
            'title': f'Peta Fullscreen - {yearly_map.judul}',
            'yearly_map': yearly_map,
            'config': homepage_config,  # Config HomePage untuk metadata
        }
        
        return render(request, 'frontend/fullscreen_map.html', context)
        
    except Exception as e:
        context = {
            'title': f'Peta Fullscreen {tahun}',
            'error': f'Terjadi kesalahan: {str(e)}'
        }
        return render(request, 'frontend/fullscreen_map.html', context)


def data_tahunan(request):
    """View untuk halaman data tahunan lengkap"""
    import json
    
    try:
        # Ambil config HomePage untuk metadata
        homepage_config = HomePage.objects.first()
        
        # Ambil semua peta per tahun yang aktif dan ada CSV-nya
        yearly_maps = YearlyMap.objects.filter(is_active=True, data_csv__isnull=False).order_by('tahun')
        
        # Siapkan data untuk setiap tahun
        yearly_data = []
        all_kabupaten = set()
        
        for yearly_map in yearly_maps:
            try:
                # Baca CSV
                df = pd.read_csv(yearly_map.data_csv.path)
                
                # Normalisasi nama kolom
                df.columns = df.columns.str.strip().str.lower()
                
                # Ambil kabupaten
                kabupaten_col = 'kabupaten' if 'kabupaten' in df.columns else df.columns[0]
                
                # Identifikasi kolom makanan dan non-makanan
                makanan_col = None
                non_makanan_col = None
                
                for col in df.columns:
                    if 'makanan' in col and 'bukan' not in col and 'non' not in col:
                        makanan_col = col
                    elif 'bukan' in col or 'non' in col or 'non_makanan' in col:
                        non_makanan_col = col
                
                if not makanan_col or not non_makanan_col:
                    continue
                
                # Konversi ke numeric
                df[makanan_col] = pd.to_numeric(df[makanan_col], errors='coerce')
                df[non_makanan_col] = pd.to_numeric(df[non_makanan_col], errors='coerce')
                
                # Hapus baris dengan NaN
                df = df.dropna(subset=[kabupaten_col, makanan_col, non_makanan_col])
                
                # Simpan data per kabupaten
                data_per_kabupaten = []
                for _, row in df.iterrows():
                    kabupaten_name = str(row[kabupaten_col]).strip()
                    all_kabupaten.add(kabupaten_name)
                    
                    data_per_kabupaten.append({
                        'kabupaten': kabupaten_name,
                        'makanan': float(row[makanan_col]),
                        'non_makanan': float(row[non_makanan_col])
                    })
                
                # Hitung statistik
                stats = {
                    'makanan': {
                        'min': float(df[makanan_col].min()),
                        'max': float(df[makanan_col].max()),
                        'mean': float(df[makanan_col].mean()),
                        'std': float(df[makanan_col].std())
                    },
                    'non_makanan': {
                        'min': float(df[non_makanan_col].min()),
                        'max': float(df[non_makanan_col].max()),
                        'mean': float(df[non_makanan_col].mean()),
                        'std': float(df[non_makanan_col].std())
                    }
                }
                
                yearly_data.append({
                    'tahun': yearly_map.tahun,
                    'judul': yearly_map.judul,
                    'data': data_per_kabupaten,
                    'stats': stats,
                    'csv_url': yearly_map.data_csv.url
                })
                
            except Exception as e:
                print(f"Error processing CSV for year {yearly_map.tahun}: {e}")
                continue
        
        # Sort kabupaten
        all_kabupaten = sorted(list(all_kabupaten))
        
        # Convert yearly_data to JSON string for JavaScript
        yearly_data_json = json.dumps(yearly_data)
        
        context = {
            'title': 'Data Tahunan - Makanan & Non-Makanan',
            'config': homepage_config,
            'yearly_data': yearly_data,
            'yearly_data_json': yearly_data_json,  # JSON string untuk JavaScript
            'all_kabupaten': all_kabupaten,
            'years': [data['tahun'] for data in yearly_data]
        }
        
        return render(request, 'frontend/data_tahunan.html', context)
        
    except Exception as e:
        context = {
            'title': 'Data Tahunan',
            'error': f'Terjadi kesalahan: {str(e)}'
        }
        return render(request, 'frontend/data_tahunan.html', context)
