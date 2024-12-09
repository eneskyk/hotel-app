from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pyodbc
import bcrypt
from datetime import timedelta
import logging
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Oturum Süresi
app.permanent_session_lifetime = timedelta(minutes=30)

# Veritabanı Bağlantı Ayarları
server = 'localhost\\SQLEXPRESS'
database = 'OtelRezervasyonu'
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"

# Veritabanı Bağlantısı
def db_connect():
    try:
        conn = pyodbc.connect(connection_string)
        print("Veritabanı bağlantısı başarılı!")
        logging.info("Veritabanı bağlantısı başarılı!")  # Başarı mesajı kaydedildi
        return conn
    except pyodbc.Error as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        logging.error(f"Veritabanı bağlantı hatası: {e}")  # Hata mesajı kaydedildi
        return None

# Ana Sayfa
@app.route("/home")
def home():
    if 'username' in session:
        return render_template("ana_sayfa.html")
    else:
        return redirect(url_for('giris_sayfasi'))

# Giriş Sayfası
@app.route("/giris_sayfasi")
def giris_sayfasi():
    return render_template("giris_kayit.html")

# Kayıt İşlemi
@app.route("/register", methods=["POST"])
def kayit():
    if not request.is_json:
        return jsonify({"message": "Desteklenmeyen içerik türü, 'application/json' bekleniyor."}), 415

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    password2 = data.get("password2")
    email = data.get("email")
    tel = data.get("tel")

    if not username or not password or not password2 or not email or not tel:
        return jsonify({"message": "Tüm alanları doldurmanız gerekiyor!"}), 400

    if password != password2:
        return jsonify({"message": "Şifreler uyuşmuyor!"}), 400

    if len(password) < 8:
        return jsonify({"message": "Şifre en az 8 karakter olmalıdır!"}), 400

    try:
        conn = db_connect()
        if not conn:
            return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Kullanici WHERE KullaniciAdi = ? OR Email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            return jsonify({"message": "Bu kullanıcı adı veya e-posta adresi zaten kayıtlı!"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Kullanıcıyı 'üye' rolü ile kaydediyoruz
        cursor.execute("INSERT INTO Kullanici (KullaniciAdi, Sifre, Tel, Email, Rol) VALUES (?, ?, ?, ?, ?)", 
                       (username, hashed_password.decode('utf-8'), tel, email, 'üye'))
        conn.commit()
        return jsonify({"message": "Kayıt başarılı!"})
    except Exception as e:
        return jsonify({"message": f"Hata: {e}"}), 500


# Giriş İşlemi
@app.route("/login", methods=["POST"])
def giris():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Kullanıcı adı ve şifre gereklidir!"}), 400

    try:
        conn = db_connect()
        if not conn:
            return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT Sifre, Rol FROM Kullanici WHERE KullaniciAdi = ?", (username,))
        result = cursor.fetchone()

        if result:
            hashed_password, rol = result
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                session['username'] = username
                session['rol'] = rol  # Rol bilgisini oturumda tutuyoruz

                # Eğer admin kullanıcı girişi yaparsa, admin ana sayfasına yönlendireceğiz
                if rol == 'admin':
                    return jsonify({"message": "Giriş başarılı!", "redirect": "/admin_home"})
                else:
                    return jsonify({"message": "Giriş başarılı!", "redirect": "/home"})
            else:
                return jsonify({"message": "Hatalı kullanıcı adı veya şifre!"}), 401
        else:
            return jsonify({"message": "Kullanıcı bulunamadı!"}), 404
    except Exception as e:
        return jsonify({"message": f"Bir hata oluştu: {e}"}), 500


# Admin Ana Sayfası
@app.route("/admin_home")
def admin_home():
    # Eğer kullanıcı admin değilse, tekrar giriş sayfasına yönlendir
    if 'username' in session and session.get('rol') == 'admin':
        return render_template("admin_home.html")
    else:
        return redirect(url_for('giris_sayfasi'))
     
@app.route('/get_users', methods=['GET'])
def get_users():
    conn = db_connect()
    if not conn:
        return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

    cursor = conn.cursor()
    cursor.execute("SELECT KullaniciID, KullaniciAdi, Email, Tel, Rol FROM Kullanici")  # Rol sütunu da eklendi
    users = cursor.fetchall()
    user_list = [
        {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'tel': row[3],
            'role': row[4]  # Rol bilgisi burada yer alıyor
        } 
        for row in users
    ]
    conn.close()  # Veritabanı bağlantısını kapatıyoruz
    return jsonify(user_list)

@app.route('/admin_user_list')
def admin_user_list():
    if 'username' in session and session.get('rol') == 'admin':
        conn = db_connect()
        if not conn:
            return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT KullaniciID, KullaniciAdi, Email, Tel, Rol FROM Kullanici")
        users = cursor.fetchall()
        user_list = [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'tel': row[3],
                'role': row[4]
            } 
            for row in users
        ]
        conn.close()  # Veritabanı bağlantısını kapatıyoruz
        return render_template("admin_user_list.html", users=user_list)  # Kullanıcıları HTML sayfasında gösteriyoruz
    else:
        return redirect(url_for('giris_sayfasi'))
        
@app.route('/update_role', methods=['POST'])
def update_role():
    data = request.get_json()
    user_id = data['id']
    new_role = data['role']

    conn = db_connect()
    if not conn:
        return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

    cursor = conn.cursor()
    cursor.execute("UPDATE Kullanici SET Rol = ? WHERE KullaniciID = ?", (new_role, user_id))  # Rol alanı güncelleniyor
    conn.commit()
    conn.close()  # Veritabanı bağlantısını kapatıyoruz
    return jsonify({'status': 'success'})


# Kullanıcı tanımlama sayfası
@app.route('/kullanici_tanimla')
def kullanici_tanimla():
    return render_template('kullanici_tanimla.html')


# Anasayfa Yönlendirme
@app.route("/")
def anasayfa():
    if 'username' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('giris_sayfasi'))

# Rezervasyon Sayfası
@app.route("/rezervasyon", methods=["GET", "POST"])
def rezervasyon():
    if request.method == "POST":
        data = request.get_json()
        isim = data.get("isim")
        soyisim = data.get("soyisim")
        yas = data.get("yas")
        kimlik = data.get("kimlik")
        oda_turu = data.get("odaTuru")
        misafir_sayisi = data.get("misafirSayisi")
        baslangic_tarihi = data.get("baslangicTarihi")
        bitis_tarihi = data.get("bitisTarihi")
        misafirler = data.get("misafirler")  # Misafirler bilgisi alındı

        try:
            conn = db_connect()
            if not conn:
                return jsonify({"message": "Veritabanı bağlantısı kurulamadı!"}), 500

            cursor = conn.cursor()

            # 1. Geçici Misafirler Tablosunda Kimlik Kontrolü
            for misafir in misafirler:
                kimlik = misafir.get("kimlik")
                cursor.execute("SELECT COUNT(*) FROM GeciciMisafir WHERE Kimlik = ?", (kimlik,))
                if cursor.fetchone()[0] > 0:
                    return jsonify({"message": f"{misafir.get('isim')} {misafir.get('soyisim')} kimlik numarası zaten geçici misafirler tablosunda mevcut!"}), 400

            # 2. Gerçek Misafirler Tablosunda Kimlik Kontrolü
            for misafir in misafirler:
                kimlik = misafir.get("kimlik")
                cursor.execute("SELECT COUNT(*) FROM Misafir WHERE Kimlik = ?", (kimlik,))
                if cursor.fetchone()[0] > 0:
                    return jsonify({"message": f"{misafir.get('isim')} {misafir.get('soyisim')} kimlik numarası zaten gerçek misafirler tablosunda mevcut!"}), 400

            # 3. Rezervasyon ve Misafir Kaydını Yapma
            cursor.execute("EXEC KaydetMisafirVeRezervasyon ?, ?, ?, ?, ?, ?, ?, ?",
                           (isim, soyisim, yas, kimlik, oda_turu, misafir_sayisi, baslangic_tarihi, bitis_tarihi))

            conn.commit()
            return jsonify({"message": "Rezervasyon başarıyla kaydedildi!"}), 200
        except Exception as e:
            return jsonify({"message": f"Hata: {e}"}), 500
    return render_template("rezervasyon.html")

# Çıkış İşlemi
@app.route("/cikis")
def cikis():
    session.clear()  # Oturumu temizle
    return redirect(url_for('giris_sayfasi'))  # Giriş sayfasına yönlendir

if __name__ == "__main__":
    app.run(debug=True)

