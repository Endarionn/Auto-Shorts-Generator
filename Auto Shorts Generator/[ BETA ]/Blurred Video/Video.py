    import os
    import ffmpeg
    import whisper
    import argparse
    import warnings
    import subprocess
    import tempfile
    from utils import filename, str2bool, write_srt
    import random
    import cv2
    from moviepy.editor import VideoFileClip, CompositeVideoClip
    from moviepy.editor import TextClip

    def get_audio(paths):
        temp_dir = tempfile.gettempdir()
        audio_paths = {}
        for path in paths:
            print(f"Extracting audio from {filename(path)}...")
            output_path = os.path.join(temp_dir, f"{filename(path)}.wav")
            command = [
                "ffmpeg", "-i", f"file:{path}",
                "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16k",
                "-y", output_path
            ]
            try:
                subprocess.run(command, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while extracting audio from {filename(path)}:")
                print(e.stderr.decode())
                continue
            audio_paths[path] = output_path
        return audio_paths

    def get_subtitles(audio_paths: list, output_srt: bool, output_dir: str, transcribe: callable):
        subtitles_path = {}
        for path, audio_path in audio_paths.items():
            srt_path = output_dir if output_srt else tempfile.gettempdir()
            srt_path = os.path.join(srt_path, f"{filename(path)}.srt")
            print(f"Generating subtitles for {filename(path)}... This might take a while.")
            warnings.filterwarnings("ignore")
            result = transcribe(audio_path)
            warnings.filterwarnings("default")
            with open(srt_path, "w", encoding="utf-8") as srt:
                write_srt(result["segments"], file=srt)
            subtitles_path[path] = srt_path
        return subtitles_path

    def blur_background_video(input_video_path, output_blurred_video_path, blur_strength=21):
        cap = cv2.VideoCapture(input_video_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_blurred_video_path, fourcc, fps, (width, height))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            blurred_frame = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
            out.write(blurred_frame)
        cap.release()
        out.release()

    def overlay_videos(background_video_path, foreground_video_path, output_video_path, margin=50):
        background_clip = VideoFileClip(background_video_path)
        foreground_clip = VideoFileClip(foreground_video_path)
        
        # Arka plan videosunun süresini ön plan videosunun süresine ayarlama
        background_clip = background_clip.set_duration(foreground_clip.duration)
        
        # Ön plan videosunun boyutlarını ayarlama
        new_width = background_clip.w - 2 * margin
        new_height = (foreground_clip.h / foreground_clip.w) * new_width
        foreground_clip = foreground_clip.resize((new_width, new_height)).set_position(("center", "center"))
        
        # Video süresinden son bir saniye çıkarma
        final_clip_duration = background_clip.duration - 1
        background_clip = background_clip.subclip(0, final_clip_duration)
        foreground_clip = foreground_clip.subclip(0, final_clip_duration)
        
        # Watermark için yazı ekleme
        watermark = TextClip("Code by: Khaenn", fontsize=20, color='white')
        watermark = watermark.set_position(('center', 50)).set_duration(final_clip_duration)
        
        final_clip = CompositeVideoClip([background_clip, foreground_clip, watermark])
        final_clip.write_videofile(output_video_path, codec='libx264')


    def main_function():
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("video", nargs="+", type=str, help="paths to video files to transcribe")
        parser.add_argument("--model", default="small", choices=whisper.available_models(), help="name of the Whisper model to use")
        parser.add_argument("--output_dir", "-o", type=str, default=".", help="directory to save the outputs")
        parser.add_argument("--output_srt", type=str2bool, default=False, help="whether to output the .srt file along with the video files")
        parser.add_argument("--srt_only", type=str2bool, default=False, help="only generate the .srt file and not create overlayed video")
        parser.add_argument("--verbose", type=str2bool, default=False, help="whether to print out the progress and debug messages")
        parser.add_argument("--task", type=str, default="transcribe", choices=["transcribe", "translate"], help="whether to perform X->X speech recognition ('transcribe') or X->English translation ('translate')")
        parser.add_argument("--language", type=str, default="auto", choices=["auto", "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh"], help="What is the origin language of the video? If unset, it is detected automatically.")
        args = parser.parse_args().__dict__
        model_name: str = args.pop("model")
        output_dir: str = args.pop("output_dir")
        output_srt: bool = args.pop("output_srt")
        srt_only: bool = args.pop("srt_only")
        language: str = args.pop("language")
        os.makedirs(output_dir, exist_ok=True)
        if model_name.endswith(".en"):
            warnings.warn(f"{model_name} is an English-only model, forcing English detection.")
            args["language"] = "en"
        elif language != "auto":
            args["language"] = language
        model = whisper.load_model(model_name)
        audios = get_audio(args.pop("video"))
        subtitles = get_subtitles(
            audios, output_srt or srt_only, output_dir, lambda audio_path: model.transcribe(audio_path, **args)
        )
        if srt_only:
            return
        for path, srt_path in subtitles.items():
            out_path = os.path.join(output_dir, f"{filename(path)}.mp4")
            print(f"Adding subtitles to {filename(path)}...")
            video = ffmpeg.input(path)
            audio = video.audio
            try:
                ffmpeg.concat(
                    video.filter('subtitles', srt_path.replace('\\', '\\\\'), 
                                force_style="OutlineColour=&H40000000,BorderStyle=3,BackColour=&H00000000"),
                    audio, v=1, a=1
                ).output(out_path).run(overwrite_output=True)
            except ffmpeg.Error as e:
                if e.stderr:
                    print(e.stderr.decode())
                else:
                    print("FFmpeg error occurred but no stderr output is available.")
        
        # Burada rastgele bir arka plan videosu seçiyoruz.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        background_videos_dir = os.path.join(base_dir, 'Background Videos')
        background_video_files = os.listdir(background_videos_dir)
        background_video_path = os.path.join(background_videos_dir, random.choice(background_video_files))
        blurred_background_video_path = os.path.join(output_dir, 'blurred_background.mp4')
        blur_background_video(background_video_path, blurred_background_video_path)
        
        # Çıktı dosyasını güncelle
        final_output_path = os.path.join(output_dir, 'final_output.mp4')
        
        # En son video ile overlay işlemi
        for path in subtitles.keys():
            out_path = os.path.join(output_dir, f"{filename(path)}.mp4")
            overlay_videos(blurred_background_video_path, out_path, final_output_path)
            break  # sadece ilk video ile overlay yapılır

        
        # Burada rastgele bir arka plan videosu seçiyoruz.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        background_videos_dir = os.path.join(base_dir, 'Background Videos')
        background_video_files = os.listdir(background_videos_dir)
        background_video_path = os.path.join(background_videos_dir, random.choice(background_video_files))
        blurred_background_video_path = os.path.join(output_dir, 'blurred_background.mp4')
        blur_background_video(background_video_path, blurred_background_video_path)
        
        # Çıktı dosyasını güncelle
        final_output_path = os.path.join(output_dir, 'final_output.mp4')
        
        # En son video ile overlay işlemi
        for path in subtitles.keys():
            out_path = os.path.join(output_dir, f"{filename(path)}.mp4")
            overlay_videos(blurred_background_video_path, out_path, final_output_path)
            break  # sadece ilk video ile overlay yapılır

    if __name__ == '__main__':
        main_function()
