from django.urls import path
from .views import home, download_analysis_zip, fullscreen_map, yearly_map_fullscreen, data_tahunan


app_name = "frontend"
urlpatterns = [
    path("", home, name="home"),
    path("peta-fullscreen/", fullscreen_map, name="fullscreen_map"),
    path("download/analysis/", download_analysis_zip, name="download_analysis"),
    path("peta/<int:tahun>/fullscreen/", yearly_map_fullscreen, name="yearly_fullscreen"),
    path("data-tahunan/", data_tahunan, name="data_tahunan"),
]
