from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(title="Stok Yönetim Paneli API")

# --- CORS İzni ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# İstek gövdesi (Body) için veri modeli
class UrunSema(BaseModel):
    urun_adi: str
    kategori: str
    fiyat: float
    stok_adedi: int

# PostgreSQL Veritabanı Bağlantısı
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        port=5432,
        cursor_factory=RealDictCursor
    )
    return conn

# --- E-POSTA GÖNDERME FONKSİYONU (Arka Plan Görevi) ---
SMTP_KULLANICI = ""       # Gerçek gönderim için: "ornek@gmail.com"
SMTP_SIFRE = ""           # Google Hesap > Güvenlik > Uygulama Şifresi (16 haneli)
BILDIRIM_ALICI = ""       # Bildirimin gideceği e-posta: "yonetici@ornek.com"

def stok_tukenme_bildirimi_gonder(urun_adi: str, kategori: str):
    konu = f"🚨 KRİTİK STOK ALARMI: {urun_adi} Tükendi!"
    icerik = f"""
    Sayın Yönetici,

    Aşağıdaki ürünün stoğu tükenmiştir (0 adet):

    - Ürün Adı: {urun_adi}
    - Kategori: {kategori}
    - Durum: Stok tükendi / Acil tedarik gerekiyor.

    Lütfen envanter yönetim panelini kontrol ediniz.
    """

    # Eğer gerçek SMTP bilgileri girilmemişse konsola profesyonel log basar (Simülasyon Modu)
    if not SMTP_KULLANICI or not SMTP_SIFRE or not BILDIRIM_ALICI:
        print("\n" + "="*55)
        print("📨 [E-POSTA SİMÜLASYONU TETİKLENDİ]")
        print(f"Kime: {BILDIRIM_ALICI or 'yonetici@ornek.com'}")
        print(f"Konu: {konu}")
        print(icerik.strip())
        print("="*55 + "\n")
        return

    try:
        mesaj = MIMEMultipart()
        mesaj["From"] = SMTP_KULLANICI
        mesaj["To"] = BILDIRIM_ALICI
        mesaj["Subject"] = konu
        mesaj.attach(MIMEText(icerik, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as sunucu:
            sunucu.login(SMTP_KULLANICI, SMTP_SIFRE)
            sunucu.sendmail(SMTP_KULLANICI, BILDIRIM_ALICI, mesaj.as_string())
        print(f"✅ Bildirim e-postası başarıyla gönderildi: {urun_adi}")
    except Exception as e:
        print(f"❌ E-posta gönderilirken hata oluştu: {e}")

# 1. READ: Tüm ürünleri listele
@app.get("/urunler")
def urunleri_listele():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urunler ORDER BY id ASC;")
    urunler = cursor.fetchall()
    cursor.close()
    conn.close()
    return urunler

# 2. CREATE: Yeni ürün ekle
@app.post("/urunler")
def urun_ekle(urun: UrunSema, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    sorgu = """
        INSERT INTO urunler (urun_adi, kategori, fiyat, stok_adedi)
        VALUES (%s, %s, %s, %s) RETURNING *;
    """
    cursor.execute(sorgu, (urun.urun_adi, urun.kategori, urun.fiyat, urun.stok_adedi))
    yeni_urun = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    # Stok 0 girildiyse arka planda e-posta bildirimi tetikle
    if urun.stok_adedi <= 0:
        background_tasks.add_task(stok_tukenme_bildirimi_gonder, urun.urun_adi, urun.kategori)

    return {"mesaj": "Ürün başarıyla eklendi", "urun": yeni_urun}

# 3. UPDATE: Ürünü güncelle
@app.put("/urunler/{urun_id}")
def urun_guncelle(urun_id: int, urun: UrunSema, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    sorgu = """
        UPDATE urunler 
        SET urun_adi = %s, kategori = %s, fiyat = %s, stok_adedi = %s
        WHERE id = %s RETURNING *;
    """
    cursor.execute(sorgu, (urun.urun_adi, urun.kategori, urun.fiyat, urun.stok_adedi, urun_id))
    guncellenen = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not guncellenen:
        raise HTTPException(status_code=404, detail="Güncellenecek ürün bulunamadı")

    # Stok 0 veya altına düştüyse arka planda e-posta bildirimi tetikle
    if urun.stok_adedi <= 0:
        background_tasks.add_task(stok_tukenme_bildirimi_gonder, urun.urun_adi, urun.kategori)

    return {"mesaj": "Ürün güncellendi", "urun": guncellenen}

# 4. DELETE: Ürün sil
@app.delete("/urunler/{urun_id}")
def urun_sil(urun_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM urunler WHERE id = %s RETURNING id;", (urun_id,))
    silinen = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if not silinen:
        raise HTTPException(status_code=404, detail="Silinecek ürün bulunamadı")
    return {"mesaj": f"{urun_id} numaralı ürün silindi"}

# 5. EXPORT: Excel (.xlsx) İndir
@app.get("/urunler/excel-indir")
def urunler_excel_indir():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urunler ORDER BY id ASC;")
    urunler = cursor.fetchall()
    cursor.close()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stok Listesi"

    basliklar = ["Sıra No", "Ürün Adı", "Kategori", "Birim Fiyat (TL)", "Stok Adedi"]
    ws.append(basliklar)

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    for col_idx in range(1, len(basliklar) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for i, u in enumerate(urunler, start=1):
        ws.append([i, u["urun_adi"], u["kategori"], float(u["fiyat"]), int(u["stok_adedi"])])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    headers = {"Content-Disposition": "attachment; filename=stok_raporu.xlsx"}
    return StreamingResponse(
        buffer, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers=headers
    )