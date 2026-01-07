from django.db import models


# Model ini akan menyimpan semua konfigurasi dan metadata untuk Halaman Utama QGIS Anda
class HomePage(models.Model):
    # 1. Judul
    name = models.CharField(max_length=200, verbose_name="Nama Proyek (Judul Besar)")

    # 2. Metadata
    tahun_mulai = models.IntegerField(verbose_name="Tahun Mulai Data", default=2022)
    tahun_akhir = models.IntegerField(verbose_name="Tahun Akhir Data", default=2024)

    lingkup_geografi = models.CharField(
        max_length=255,
        verbose_name="Lingkup Geografi",
        default="Kabupaten/Kota di Provinsi Papua",
    )
    sumber_data = models.CharField(
        max_length=255,
        verbose_name="Sumber Data Utama",
        default="Survei Sosial Ekonomi Nasional (Susenas)",
    )
    platform_gis = models.CharField(
        max_length=100, verbose_name="Platform GIS", default="QGIS & Leaflet"
    )

    # 4. Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konfigurasi Halaman Utama"
        verbose_name_plural = "Konfigurasi Halaman Utama"

    def __str__(self):
        return self.name


# Model untuk Peta Per Tahun
class YearlyMap(models.Model):
    homepage = models.ForeignKey(
        HomePage, 
        on_delete=models.CASCADE, 
        related_name='yearly_maps',
        verbose_name="Halaman Utama"
    )
    
    tahun = models.IntegerField(
        verbose_name="Tahun",
        unique=True,
        help_text="Tahun data peta (contoh: 2022, 2023, 2024)"
    )
    
    judul = models.CharField(
        max_length=200,
        verbose_name="Judul Peta Tahun Ini",
        help_text="Contoh: Peta Inflasi Papua 2024"
    )
    
    url_peta = models.URLField(
        max_length=500,
        verbose_name="URL Peta QGIS2Web untuk Tahun Ini",
        help_text="URL peta spesifik untuk tahun ini"
    )
    
    data_csv = models.FileField(
        upload_to="qgis_data/yearly/",
        verbose_name="Upload File Data CSV Tahun Ini",
        help_text="Data statistik untuk tahun ini",
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
        help_text="Centang untuk menampilkan peta ini"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Peta Per Tahun"
        verbose_name_plural = "Peta Per Tahun"
        ordering = ['tahun']  # Urutkan dari tahun terlama
    
    def __str__(self):
        return f"{self.judul} ({self.tahun})"
