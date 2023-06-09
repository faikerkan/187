from pydub import AudioSegment

audio_file_mp3 = "/Users/faikerkangursen/Documents/Yazılım Dosyaları/Python/187Ses/187.mp3"
audio_file_wav = "/Users/faikerkangursen/Documents/Yazılım Dosyaları/Python/187Ses/187.wav"

# MP3 dosyasını yükle
audio = AudioSegment.from_mp3(audio_file_mp3)

# WAV dosyasına dönüştür ve kaydet
audio.export(audio_file_wav, format="wav")

import speech_recognition as sr

audio_file = "/Users/faikerkangursen/Documents/Yazılım Dosyaları/Python/187Ses/187.wav"

# Tanıma motorunu oluştur
recognizer = sr.Recognizer()

# Ses dosyasını yükle
with sr.AudioFile(audio_file) as source:
    audio = recognizer.record(source)

# Metni tanı
try:
    text = recognizer.recognize_google(audio, language="tr-TR")
    print("Ses kaydı metni:")
    print(text)
except sr.UnknownValueError:
    print("Ses kaydı anlaşılamadı.")
except sr.RequestError as e:
    print("Ses tanıma hizmeti çalışmıyor; {0}".format(e))


