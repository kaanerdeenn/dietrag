import sqlite3
from typing import Dict, Any, List

DATABASE_NAME = "user_diet.db"

def init_db():
    """Veritabanını ve tabloları oluşturur."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Kullanıcıların temel bilgilerini tutan tablo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        boy_cm REAL NOT NULL,
        kilo_kg REAL NOT NULL,
        yas INTEGER NOT NULL,
        cinsiyet TEXT NOT NULL
    )
    """)

    # Kullanıcıların yediği öğünleri tutan tablo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ogun_adi TEXT NOT NULL,
        kalori INTEGER NOT NULL,
        tarih DATE DEFAULT (date('now')),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)
    conn.commit()
    conn.close()
    print("Veritabanı ve tablolar başarıyla oluşturuldu/kontrol edildi.")

def add_sample_data():
    """Örnek veriler ekler."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Örnek kullanıcılar (eğer yoksa ekle)
    users_data = [
        (1, 175.0, 78.5, 30, 'Erkek'),
        (2, 162.0, 55.0, 25, 'Kadın')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (user_id, boy_cm, kilo_kg, yas, cinsiyet) VALUES (?, ?, ?, ?, ?)", users_data)

    # Örnek öğünler (eğer yoksa ekle)
    meals_data = [
        (1, 'Kahvaltı', 450),
        (1, 'Öğle Yemeği', 700),
        (2, 'Kahvaltı', 300)
    ]
    # Sadece bugün için veri ekleyelim
    for user_id, ogun_adi, kalori in meals_data:
        cursor.execute("INSERT INTO meals (user_id, ogun_adi, kalori) VALUES (?, ?, ?)", (user_id, ogun_adi, kalori))

    conn.commit()
    conn.close()
    print("Örnek veriler eklendi.")


def get_user_data(user_id: int) -> Dict[str, Any]:
    """Verilen user_id için tüm kullanıcı verilerini çeker."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Kullanıcı temel bilgilerini al
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_info = cursor.fetchone()

    if not user_info:
        return None # Kullanıcı bulunamadı

    user_profile = dict(user_info)

    # Kullanıcının bugünkü öğünlerini al
    cursor.execute("SELECT ogun_adi, kalori FROM meals WHERE user_id = ? AND tarih = date('now')", (user_id,))
    meals_today = cursor.fetchall()
    user_profile['gunluk_ogunler'] = [dict(row) for row in meals_today]
    user_profile['gunluk_toplam_kalori'] = sum(meal['kalori'] for meal in user_profile['gunluk_ogunler'])


    conn.close()
    return user_profile

# Veritabanını ve örnek verileri oluşturmak için bu betiği bir kez çalıştırın
if __name__ == '__main__':
    init_db()
    add_sample_data()
    # Test edelim
    print("\n--- KULLANICI 1 VERİLERİ ---")
    print(get_user_data(1))