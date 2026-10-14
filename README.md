# 📦 Envanter ve Stok Yönetim Paneli

FastAPI, PostgreSQL ve modern Vanilla JavaScript kullanılarak geliştirilmiş, gerçek zamanlı veri analitiği, asenkron e-posta otomasyonu ve Excel raporlama özelliklerine sahip kurumsal stok yönetim sistemi.

## 🚀 Özellikler
- **Full CRUD Operasyonları:** Ürün ekleme, listeleme, güncelleme ve silme.
- **Asenkron Stok Bildirimi:** Stok 0 veya kritik seviyeye indiğinde `BackgroundTasks` ile tetiklenen otomatik yönetici e-posta uyarısı.
- **Canlı Metrikler & Dashboard:** Toplam çeşit, depo adedi, anlık sermaye/envanter değeri ve kritik stok sayacı.
- **Dinamik Veri Görselleştirme:** Chart.js ile kategori bazlı dağılım (Doughnut) ve en yüksek envanter değerine sahip ilk 5 ürün (Bar Chart).
- **Hızlı Operasyon:** Tablo üzerinden tek tıkla satış yapma (`-1`) veya stok artırma (`+5`) ve Bootstrap Toast bildirimleri.
- **Excel (.xlsx) Dışa Aktarım:** `openpyxl` kütüphanesi ile in-memory akış (StreamingResponse) kullanılarak üretilen başlık stilli kurumsal rapor.

## 🛠️ Kullanılan Teknolojiler
- **Backend:** Python, FastAPI, Pydantic, Psycopg2, Uvicorn, smtplib
- **Veritabanı:** PostgreSQL
- **Frontend:** HTML5, Bootstrap 5, Bootstrap Icons, JavaScript (Fetch API), Chart.js
- **Raporlama:** OpenPyXL

## 💻 Kurulum ve Çalıştırma

1. Projeyi klonlayın:
   ```bash
   git clone [https://github.com/KULLANICI_ADINIZ/stok-yonetim-paneli.git](https://github.com/KULLANICI_ADINIZ/stok-yonetim-paneli.git)
   cd stok-yonetim-paneli