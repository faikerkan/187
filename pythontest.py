import os
import glob
from pydub import AudioSegment
import speech_recognition as sr
import psycopg2

# PostgreSQL veritabanı bağlantısı için gerekli bilgileri ayarlayın
db_connection_params = {
    'host': 'hostname ya da ip',
    'database': 'bağlanılan database',
    'user': 'DB kullanıcı',
    'password': DB '
}

# Ses dosyalarının bulunduğu klasör
input_folder = "Ses dosyalarının bulunduğu klasör yolu"
output_folder = "wav çıktısının kayıt edileceği klasör yolu"

# Yeni klasörü oluşturun, eğer zaten varsa atlayın
os.makedirs(output_folder, exist_ok=True)

# Klasördeki tüm mp3 dosyalarını seçin
mp3_files = glob.glob(os.path.join(input_folder, "*.mp3"))

# Müşteri tarafında yakalanması gereken sözcükler
customer_keywords = ["kaçak", "koku", "arkasından", "alarm", "çürük", "sarımsak", "sarmısak", "mutfak", "dolap", "tavan", "sensör", "ağır", "gaz", "yangın", "patlama"]

# PostgreSQL veritabanına bağlanın
conn = psycopg2.connect(**db_connection_params)
cur = conn.cursor()

for mp3_file in mp3_files:
    # Ses dosyasını yükle
    audio = AudioSegment.from_mp3(mp3_file)

    # Sağ kanalı "müşteri" ve sol kanalı "temsilci" olarak ayır. 
    left_channel = audio.split_to_mono()[0]  # Sol kanal (temsilci)
    right_channel = audio.split_to_mono()[1]  # Sağ kanal (müşteri)

    # Dosya adını alın (dosya adı + .mp3)
    file_name = os.path.basename(mp3_file)

    # .mp3 uzantısını kaldırın ve .wav uzantısını ekleyin
    file_name_without_extension = os.path.splitext(file_name)[0]

    # "temsilci" sesini .wav formatında kaydedin
    temsilci_wav_file_path = os.path.join(output_folder, file_name_without_extension + "_temsilci.wav")
    left_channel.export(temsilci_wav_file_path, format="wav")

    # "müşteri" sesini .wav formatında kaydedin
    musteri_wav_file_path = os.path.join(output_folder, file_name_without_extension + "_musteri.wav")
    right_channel.export(musteri_wav_file_path, format="wav")

    #Sonuç ver
    print(f"{mp3_file} dönüştürüldü ve {temsilci_wav_file_path} ve {musteri_wav_file_path} olarak kaydedildi.")

    # "müşteri" sesini transkript etmek ve "ihbar çağrısı" olup olmadığını kontrol etmek
    recognizer = sr.Recognizer()
    with sr.AudioFile(musteri_wav_file_path) as source:
        try:
            audio_data = recognizer.record(source)
            transcript_musteri = recognizer.recognize_google(audio_data, language="tr-TR")
        except sr.UnknownValueError:
            # Algılanamayan sesleri pas geçin ve bir sonraki ses kaydına devam edin
            continue

    # Müşteri anahtar sözcüklerini kontrol et
    has_customer_keywords = any(word in transcript_musteri for word in customer_keywords)

    # "temsilci" sesini transkript etmek ve "ihbar çağrısı" olup olmadığını kontrol etmek
    recognizer = sr.Recognizer()
    with sr.AudioFile(temsilci_wav_file_path) as source:
        try:
            audio_data = recognizer.record(source)
            transcript_temsilci = recognizer.recognize_google(audio_data, language="tr-TR")
        except sr.UnknownValueError:
            # Algılanamayan sesleri pas geçin ve bir sonraki ses kaydına devam edin
            continue

    # Temsilci anahtar sözcükler
    temsilci_keywords = ["vana", "kapatın", "havalandırın", "yanıcı", "parlayıcı"]
    has_temsilci_keywords = any(word in transcript_temsilci for word in temsilci_keywords)

    # Çağrı kategori etiketleri
    if not has_customer_keywords:
        call_label = "diğer çağrı"
    else:
        if has_temsilci_keywords:
            call_label = "uygun"
        elif has_customer_keywords and not has_temsilci_keywords:
            call_label = "eksik"
        else:
            call_label = "hatalı"

    print(f"Çağrı etiketi: {call_label}")

    # PostgreSQL veritabanına sonuçları kaydedin
    cur.execute("INSERT INTO calls (file_name, call_label) VALUES (%s, %s)", (file_name, call_label))
    conn.commit()

# PostgreSQL veritabanı bağlantısını kapatın
cur.close()
conn.close()

print("Tamamlandı")
