import os
import numpy as np
import librosa
from moviepy.editor import VideoFileClip
import argparse

def extract_important_parts(input_video, output_directory, loudness_factor=1.5, min_duration=1.0, pre_duration=15.0, post_duration=30.0, skip_duration=0):
    # Video dosyasını yükle
    video = VideoFileClip(input_video).subclip(skip_duration, None)
    
    # Ses dosyasını çıkar ve yükle
    audio = video.audio
    audio_file = "temp_audio.wav"
    audio.write_audiofile(audio_file, codec='pcm_s16le')
    
    # Ses verisini yükle
    y, sr = librosa.load(audio_file, sr=None)
    
    # RMS enerji hesapla
    rms = librosa.feature.rms(y=y).flatten()
    rms_times = librosa.frames_to_time(range(len(rms)), sr=sr) + skip_duration  # Skip duration ekle
    
    # RMS değerinin ortalamasını hesapla
    average_rms = np.mean(rms)
    
    # Ortalamanın belirli bir katından daha büyük olan bölümleri tespit et
    is_loud = rms > (average_rms * loudness_factor)
    change_points = np.diff(is_loud.astype(int))
    
    start_times = rms_times[np.where(change_points == 1)[0]]
    end_times = rms_times[np.where(change_points == -1)[0]]
    
    if len(start_times) > len(end_times):
        end_times = np.append(end_times, rms_times[-1])
    
    # Önceki klibin bittiği zamanı takip etmek için bir değişken oluştur
    last_clip_end = skip_duration
    
    # Tespit edilen bölümleri videodan çıkar
    part_number = 1
    for start, end in zip(start_times, end_times):
        if end - start >= min_duration:
            # Eğer bu kısım, önceki klibin kapsadığı sürenin içindeyse atla
            if start < last_clip_end:
                continue
            
            # Her bir komik kısmı 15 saniye öncesi ve 30 saniye sonrası olacak şekilde alın
            clip_start = max(skip_duration, start - pre_duration)
            clip_end = min(video.duration + skip_duration, start + post_duration)
            
            # Yeni bir klibin başlangıcını ve bitişini belirle
            clip = video.subclip(clip_start - skip_duration, clip_end - skip_duration)
            
            # 9:16 formatında kesme işlemi için, ekranın ortasından kes
            clip_width = 1080
            clip_height = 1920
            
            # Video boyutlarını al
            video_width, video_height = clip.size
            
            # Merkezi alanı hesapla
            center_x, center_y = video_width / 2, video_height / 2
            x1 = max(center_x - clip_width / 2, 0)
            y1 = max(center_y - clip_height / 2, 0)
            x2 = min(center_x + clip_width / 2, video_width)
            y2 = min(center_y + clip_height / 2, video_height)
            
            # Eğer 9:16 formatında uyumsuzluk varsa, kesim yaparak uyumlu hale getir
            aspect_ratio = clip_width / clip_height
            if (x2 - x1) / (y2 - y1) != aspect_ratio:
                new_height = int((x2 - x1) / aspect_ratio)
                y1 = max((video_height - new_height) // 2, 0)
                y2 = min(y1 + new_height, video_height)
            
            if x2 - x1 > 0 and y2 - y1 > 0:
                cropped_clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize(width=clip_width, height=clip_height)
                output_file = os.path.join(output_directory, f"importantPart_{part_number}.mp4")
                cropped_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
                
                # Son klibin bitiş zamanını güncelle
                last_clip_end = clip_end
                
                part_number += 1

    # Geçici dosyayı sil
    if os.path.exists(audio_file):
        os.remove(audio_file)
    
    # Kaynakları serbest bırak
    video.close()

def main():
    parser = argparse.ArgumentParser(description="Video içerisindeki önemli kısımları ve yüz odaklı 9:16 formatında kesme scripti.")
    parser.add_argument("--input", type=str, required=True, help="Giriş video dosyasının yolu.")
    parser.add_argument("--skip", type=float, default=0, help="Başlangıçta kesilecek saniye sayısı (varsayılan: 0).")
    args = parser.parse_args()

    # Giriş ve çıkış dosya adlarını belirle
    input_video = args.input
    skip_duration = args.skip
    output_directory = os.path.join(os.getcwd(), "output", "cropped")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Fonksiyonu çalıştır
    extract_important_parts(input_video, output_directory, skip_duration=skip_duration)

    print(f"Önemli kısımlar başarıyla kesildi ve {output_directory} konumuna kaydedildi.")

if __name__ == "__main__":
    main()
