USE OtelRezervasyonu;
GO

-- Kullanıcılar Tablosu
CREATE TABLE Kullanici (
    KullaniciID INT PRIMARY KEY IDENTITY,  -- Benzersiz kullanıcı kimliği
    KullaniciAdi NVARCHAR(100) NOT NULL UNIQUE,  -- Kullanıcı adı
    Sifre NVARCHAR(256) NOT NULL,  -- Şifre (hashlenmiş)
    Tel NVARCHAR(15) NOT NULL,  -- Telefon numarası
    Email NVARCHAR(100) NOT NULL UNIQUE,  -- E-posta adresi
	Rol NVARCHAR(50) NULL,
    SonGirisTarihi DATETIME NULL,  -- Son giriş tarihi
    CONSTRAINT CHK_Sifre CHECK (LEN(Sifre) >= 8),  -- Şifre uzunluğu kontrolü (örneğin 8 karakter)
    CONSTRAINT CHK_Tel CHECK (Tel LIKE '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
);

CREATE TABLE Oda (
    OdaID INT IDENTITY(1,1) PRIMARY KEY,
    OdaTuru NVARCHAR(50),  -- Oda türü: Standart, Exclusive, Deluxe
    OdaKapasite INT,       -- Oda kapasitesi: 1, 2, 4, vb.
    Durum NVARCHAR(20) DEFAULT 'Boş',  -- Oda durumu: 'Boş' veya 'Dolu'
    MisafirID INT NULL     -- Rezervasyon yapıldığında, bu oda kimde olduğunu belirten MisafirID
);

CREATE TABLE Rezervasyon (
    RezervasyonID INT IDENTITY(1,1) PRIMARY KEY, 
    MisafirID INT,
    OdaID INT,
    BaslangicTarihi DATE,
    BitisTarihi DATE,
    FOREIGN KEY (MisafirID) REFERENCES GeçiciMisafir(MisafirID),
    FOREIGN KEY (OdaID) REFERENCES Oda(OdaID)
);


-- Ödemeler Tablosu
CREATE TABLE Odeme (
    OdemeID INT PRIMARY KEY IDENTITY,  -- Benzersiz ödeme kimliği
    RezervasyonID INT NOT NULL,  -- İlgili rezervasyon
    OdemeTutar DECIMAL(10, 2) NOT NULL,  -- Ödeme tutarı
    OdemeDurumu NVARCHAR(10) NOT NULL CHECK (OdemeDurumu IN ('Yapıldı', 'Yapılmadı')),  -- Ödeme durumu
    OdemeTarihi DATE NOT NULL,  -- Ödeme tarihi
    FOREIGN KEY (RezervasyonID) REFERENCES Rezervasyon(RezervasyonID),  -- Rezervasyon ilişkisi
    CONSTRAINT CHK_OdemeTutar CHECK (OdemeTutar > 0)  -- Ödeme tutarı sıfırdan büyük olmalı
);

CREATE TABLE Misafir (
    MisafirID INT IDENTITY(1,1) PRIMARY KEY,
    Isim NVARCHAR(100) NOT NULL,
    Soyisim NVARCHAR(100) NOT NULL,
    Yas INT NOT NULL,
    Kimlik VARCHAR(50) NOT NULL UNIQUE -- Kimlik numarasının benzersiz olması gerektiğini varsayıyorum
	GirisTarihi DATE NULL,
    CikisTarihi DATE NULL
);



CREATE TABLE GeçiciRezervasyon (
    RezervasyonID INT IDENTITY(1,1) PRIMARY KEY,
    MisafirID INT,
    RezervasyonTarihi DATETIME DEFAULT GETDATE(),
    MisafirSayisi INT,
    FOREIGN KEY (MisafirID) REFERENCES GeçiciMisafir(MisafirID)
);


CREATE TABLE GeçiciMisafir (
    MisafirID INT IDENTITY(1,1) PRIMARY KEY,
    Isim NVARCHAR(100),
    Soyisim NVARCHAR(100),
    Yas INT,
    Kimlik NVARCHAR(11),
    OdaTuru NVARCHAR(50),   
    BaslangicTarihi DATETIME NULL,
    BitisTarihi DATETIME NULL
);
