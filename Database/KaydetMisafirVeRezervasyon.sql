USE OtelRezervasyonu; -- doðru veritabanýný kullandýðýnýzdan emin olun
GO

CREATE PROCEDURE KaydetMisafirVeRezervasyon
    @Isim NVARCHAR(100),
    @Soyisim NVARCHAR(100),
    @Yas INT,
    @Kimlik NVARCHAR(50),
    @OdaTuru NVARCHAR(50),
    @MisafirSayisi INT,
    @BaslangicTarihi DATE,
    @BitisTarihi DATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Kimlik numarasý mevcut mu kontrol et
    IF EXISTS (SELECT 1 FROM Misafir WHERE Kimlik = @Kimlik)
    BEGIN
        -- Eðer kimlik numarasý zaten varsa, hata mesajý döndür
        RAISERROR('Bu kimlik numarasýna sahip bir misafir zaten kayýtlý.', 16, 1);
        RETURN;
    END

    -- Misafir yoksa geçici misafire ekle
    INSERT INTO GeçiciMisafir (Isim, Soyisim, Yas, Kimlik, OdaTuru)
    VALUES (@Isim, @Soyisim, @Yas, @Kimlik, @OdaTuru);

    -- MisafirID'yi al
    DECLARE @MisafirID INT;
    SELECT @MisafirID = MisafirID FROM Misafir WHERE Kimlik = @Kimlik;

    -- Rezervasyonu ekleyelim
    INSERT INTO Rezervasyon (MisafirID, OdaID, BaslangicTarihi, BitisTarihi)
    VALUES (@MisafirID, 
            (SELECT TOP 1 OdaID FROM Oda WHERE OdaTuru = @OdaTuru AND Durum = 'Boþ'), 
            @BaslangicTarihi, 
            @BitisTarihi);

    -- Oda durumunu 'Dolu' olarak güncelle
    UPDATE Oda
    SET Durum = 'Dolu'
    WHERE OdaID = (SELECT TOP 1 OdaID FROM Oda WHERE OdaTuru = @OdaTuru AND Durum = 'Boþ');
    
    -- Misafir Sayýsý güncellemesi (GeçiciRezervasyon tablosu)
    INSERT INTO GeçiciRezervasyon (MisafirID, MisafirSayisi)
    VALUES (@MisafirID, @MisafirSayisi);

END
GO
