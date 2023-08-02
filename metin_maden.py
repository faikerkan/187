## Bu kod ile, mp3 formatındaki ses kayıtlarının bir DB üzerine transkript edilmesi sağlanmıştır.
## Müşteri ve temsilcinin, farklı kanallarda ses kayıtlarının olduğu varsayımı üzerine oluşturulmuştur.


import os
import glob
from pydub import AudioSegment
import speech_recognition as sr
import psycopg2
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# PostgreSQL veritabanı bağlantısı için gerekli bilgileri ayarlayın

db_connection_params = {
    'host': 'host-adını-yazın',
    'database': 'database-adını-yazın',
    'user': 'user',
    'password': 'passwprk'
}

# Ses dosyalarının bulunduğu klasör
input_folder = "C:/Users/..."
output_folder = "C:/Users/....../output"

# Yeni klasörü oluşturun, eğer zaten varsa atlayın
os.makedirs(output_folder, exist_ok=True)

# PostgreSQL veritabanına bağlanın
conn = psycopg2.connect(**db_connection_params)
cur = conn.cursor()

# Yeni "metin" tablosunu oluşturun (eğer zaten varsa hata almayın)
cur.execute("""
    CREATE TABLE IF NOT EXISTS metin (
        ID SERIAL PRIMARY KEY,
        file_name TEXT,
        temsilci TEXT,
        musteri TEXT
    )
""")
conn.commit()

def transcribe_and_save(mp3_file):
    # Dosya adını alın (dosya adı + .mp3)

    file_name = os.path.basename(mp3_file)

    # "file_name" sütununda aynı dosya adı zaten varsa, bu kaydı pas geçin
    cur.execute("SELECT COUNT(*) FROM metin WHERE file_name = %s", (file_name,))
    result = cur.fetchone()
    if result[0] > 0:
        print(f"{mp3_file} zaten veritabanında mevcut. Transkript edilmedi.")
        return

    # Ses dosyasını yükleyin
    audio = AudioSegment.from_mp3(mp3_file)


## Burada, yukarıda belirtilen prensiple ilerlenmektedir. Test çağrılarında müşteri ve temsilcinin sesi sağ ve sol olarak kayıt altındadır.
## Kendi ses kayıtlarınız için bu kısmı düzeltebilirsiniz.


    # Sağ kanalı "müşteri" ve sol kanalı "temsilci" olarak ayırın
    left_channel = audio.split_to_mono()[0]  # Sol kanal (temsilci)
    right_channel = audio.split_to_mono()[1]  # Sağ kanal (müşteri)

    # .mp3 uzantısını kaldırın ve .wav uzantısını ekleyin
    file_name_without_extension = os.path.splitext(file_name)[0]

    # "temsilci" sesini geçici bir .wav dosyasına kaydedin
    temsilci_wav_file_path = os.path.join(output_folder, file_name_without_extension + "_temsilci.wav")
    left_channel.export(temsilci_wav_file_path, format="wav")

    # "müşteri" sesini geçici bir .wav dosyasına kaydedin
    musteri_wav_file_path = os.path.join(output_folder, file_name_without_extension + "_musteri.wav")
    right_channel.export(musteri_wav_file_path, format="wav")

    # "müşteri" sesini transkript etmek ve PostgreSQL veritabanına kaydetmek
    recognizer = sr.Recognizer()
    with sr.AudioFile(musteri_wav_file_path) as source:
        try:
            audio_data = recognizer.record(source)
            transcript_musteri = recognizer.recognize_google(audio_data, language="tr-TR")
            transcript_musteri = transcript_musteri.strip()  # Boşlukları temizleyin
        except sr.UnknownValueError:
            # Algılanamayan sesleri pas geçin ve bir sonraki ses kaydına devam edin
            transcript_musteri = ""

    # "temsilci" sesini transkript etmek
    with sr.AudioFile(temsilci_wav_file_path) as source:
        try:
            audio_data = recognizer.record(source)
            transcript_temsilci = recognizer.recognize_google(audio_data, language="tr-TR")
            transcript_temsilci = transcript_temsilci.strip()  # Boşlukları temizleyin
        except sr.UnknownValueError:
            # Algılanamayan sesleri pas geçin ve bir sonraki ses kaydına devam edin
            transcript_temsilci = ""

    # PostgreSQL veritabanına sonuçları kaydedin
    cur.execute("INSERT INTO metin (file_name, temsilci, musteri) VALUES (%s, %s, %s)", (file_name, transcript_temsilci, transcript_musteri))
    conn.commit()

    # Kullanılmayan geçici wav dosyalarını silin
    os.remove(temsilci_wav_file_path)
    os.remove(musteri_wav_file_path)

    print(f"{mp3_file} için çağrı bilgileri veritabanına kaydedildi.")

num_threads = multiprocessing.cpu_count()

def process_audio_files(mp3_files):
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Her bir ses dosyası için transcribe_and_save fonksiyonunu çağırın
        futures = [executor.submit(transcribe_and_save, mp3_file) for mp3_file in mp3_files]

        # Tüm işlemlerin tamamlanmasını bekleyin
        for future in futures:
            future.result()

while True:
    mp3_files = glob.glob(os.path.join(input_folder, "*.mp3"))

    # Ses dosyalarını işleme görevini yeni bir iş parçacığıyla başlatın
    process_audio_files(mp3_files)
