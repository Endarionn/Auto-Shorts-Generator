import os
import ffmpeg
import whisper
import argparse
import warnings
import subprocess
import tempfile
from utils import filename, str2bool, write_srt
import platform

# Uyarıları devre dışı bırak
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def clear_console():
    """Temizleme konsolu için bir yardımcı fonksiyon."""
    command = 'cls' if platform.system() == 'Windows' else 'clear'
    os.system(command)

def get_audio(paths):
    temp_dir = tempfile.gettempdir()

    audio_paths = {}

    for path in paths:
        clear_console()
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
        
        print(
            f"Generating subtitles for {filename(path)}... This might take a while."
        )

        result = transcribe(audio_path)

        with open(srt_path, "w", encoding="utf-8") as srt:
            write_srt(result["segments"], file=srt)

        subtitles_path[path] = srt_path

    return subtitles_path

def main_function():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", type=str, required=True,
                        help="path to video file to transcribe")
    parser.add_argument("--model", default="small",
                        choices=whisper.available_models(), help="name of the Whisper model to use")
    parser.add_argument("--output_dir", "-o", type=str,
                        default="./output/subtitled", help="directory to save the outputs")
    parser.add_argument("--output_srt", type=str2bool, default=True,
                        help="whether to output the .srt file along with the video files")
    parser.add_argument("--srt_only", type=str2bool, default=False,
                        help="only generate the .srt file and not create overlayed video")
    parser.add_argument("--verbose", type=str2bool, default=False,
                        help="whether to print out the progress and debug messages")

    parser.add_argument("--task", type=str, default="transcribe", choices=[
                        "transcribe", "translate"], help="whether to perform X->X speech recognition ('transcribe') or X->English translation ('translate')")
    parser.add_argument("--language", type=str, default="auto", choices=["auto","af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca","cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha","haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn","ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my","ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl","sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk","ur","uz","vi","yi","yo","zh"], 
    help="What is the origin language of the video? If unset, it is detected automatically.")

    args = parser.parse_args().__dict__
    model_name: str = args.pop("model")
    output_dir: str = args.pop("output_dir")
    output_srt: bool = args.pop("output_srt")
    srt_only: bool = args.pop("srt_only")
    language: str = args.pop("language")
    
    os.makedirs(output_dir, exist_ok=True)

    if model_name.endswith(".en"):
        warnings.warn(
            f"{model_name} is an English-only model, forcing English detection.")
        args["language"] = "en"
    # if translate task used and language argument is set, then use it
    elif language != "auto":
        args["language"] = language
        
    model = whisper.load_model(model_name)
    audios = get_audio([args.pop("input")])
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

        # Text watermark için `drawtext` filtresi ekleniyor
        text_watermark = (
            ffmpeg
            .drawtext(
                video, text='Khaenn',
                fontsize=56,  # Yazı boyutu 48
                fontcolor='white@0.5',  # Yarı saydam beyaz
                x='(w-text_w)/2',  # Ortala
                y='h*0.05',  # Üstten %5 aşağıda
                shadowcolor='black@0.1',  # Gölge rengi
                shadowx=2,  # Gölge x ofset
                shadowy=2,   # Gölge y ofset
                borderw=2,  # Kenar genişliği
                bordercolor='black'  # Kenar rengi
            )
        )

        ffmpeg.concat(
            text_watermark.filter(
                'subtitles', srt_path, force_style="OutlineColour=&H40000000,BorderStyle=1,Bold=1,MarginV=50"), audio, v=1, a=1
        ).output(out_path).run(quiet=True, overwrite_output=True)

        print(f"Saved subtitled video to {os.path.abspath(out_path)}.")

        # SRT dosyasını sil
        try:
            os.remove(srt_path)
            print(f"Deleted SRT file {srt_path}.")
        except OSError as e:
            print(f"Error: {e.strerror} - {e.filename}")

if __name__ == '__main__':
    main_function()
