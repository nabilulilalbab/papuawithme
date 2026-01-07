from django.contrib import admin
from .models import HomePage, YearlyMap  # Import model yang baru dibuat


class YearlyMapInline(admin.TabularInline):
    model = YearlyMap
    extra = 1
    fields = ("tahun", "judul", "url_peta", "data_csv", "is_active")
    verbose_name = "Peta Per Tahun"
    verbose_name_plural = "Peta Per Tahun"


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    # --- FIELD LISTING ---
    list_display = ("name", "tahun_mulai", "tahun_akhir", "updated_at")

    # PERBAIKAN: Menambahkan search_fields dan list_filter untuk memastikan
    # template admin memiliki konteks yang lengkap, yang seringkali memperbaiki 'super' error.
    search_fields = ("name", "lingkup_geografi", "sumber_data")
    list_filter = ("tahun_mulai", "sumber_data")

    # Optional: Tambahkan ini untuk kerapian tampilan
    list_per_page = 10
    
    # Tambahkan ini untuk mengatasi masalah context
    change_list_template = 'admin/change_list.html'
    
    # Tambahkan inline untuk YearlyMap
    inlines = [YearlyMapInline]

    # --- FIELDSETS (Grup Input) ---
    fieldsets = (
        (
            "KONFIGURASI JUDUL",
            {
                "fields": ("name",),
            },
        ),
        (
            "METADATA DATA",
            {
                "fields": (
                    "tahun_mulai",
                    "tahun_akhir",
                    "lingkup_geografi",
                    "sumber_data",
                    "platform_gis",
                ),
            },
        ),
    )


@admin.register(YearlyMap)
class YearlyMapAdmin(admin.ModelAdmin):
    list_display = ("tahun", "judul", "is_active", "updated_at")
    list_filter = ("is_active", "tahun", "homepage")
    search_fields = ("judul", "tahun")
    list_editable = ("is_active",)
    list_per_page = 20
    
    fieldsets = (
        (
            "INFORMASI DASAR",
            {
                "fields": ("homepage", "tahun", "judul", "is_active"),
            },
        ),
        (
            "KONTEN PETA",
            {
                "fields": ("url_peta", "data_csv"),
            },
        ),
    )
