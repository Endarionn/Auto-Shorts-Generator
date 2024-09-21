import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import re

# Create the main window
window = tk.Tk()
window.title("Video Transcription Tool")

# Function to handle the file selection
def select_files():
    files = filedialog.askopenfilenames(title="Select Video File(s)", filetypes=(("Video Files", "*.mp4"), ("All Files", "*.*")))
    file_list.delete(1.0, tk.END)  # Clear the existing file list
    file_list.insert(tk.END, "\n".join(files))

def convert_path_to_wsl(paths):
    wsl_paths = []
    for path in paths:
        # Convert path to string if it is not already
        path = str(path)
        # Convert drive letter and colon to /mnt/ and lowercase
        wsl_path = re.sub(r"^([A-Z]):", lambda m: f"/mnt/{m.group(1).lower()}", path)
        # Replace backslashes with forward slashes
        wsl_path = wsl_path.replace("\\", "/")
        wsl_paths.append(wsl_path)
    return wsl_paths

def is_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False
# Function to execute the transcription process
def execute_transcription():
    if is_ffmpeg_installed():
        line = "ffmpeg is installed."
        log_text.insert(tk.END, line)
        log_text.see(tk.END)
        window.update()
    else:
        line = "ffmpeg is not installed."
        log_text.insert(tk.END, line)
        log_text.see(tk.END)
        window.update()
        exit(1)
    
    files = file_list.get(1.0, tk.END).strip().split("\n")
    if not files:
        messagebox.showerror("Error", "Please select video file(s).")
        return
    
    # Get the values of the arguments
    model = model_combobox.get()
    if (model == ""):
        model = 'base'
    output_dir = output_dir_entry.get()
    if (output_dir == ""):
        output_dir = 'subtitle'
    output_srt = output_srt_var.get()
    srt_only = srt_only_var.get()
    language = language_combobox.get()
    if (language == ""):
        language = 'en'

    # Construct the command
    try:
        command = ["python3", "auto_subtitle.py"]  # Replace with the name of your script
    except:
        command = ["wsl", "python3", "auto_subtitle.py"]
    wsl_path = convert_path_to_wsl(files)
    command.extend(wsl_path)
    command.extend(["--model", model, "--output_dir", output_dir, "--output_srt", str(output_srt), "--srt_only", str(srt_only), "--language", language])
    
    # Execute the command and capture the output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print("start")
    try:
        for line in iter(process.stdout.readline, ""):
            line = "IN PROGRESS .."
            log_text.insert(tk.END, line)
            log_text.see(tk.END)
            window.update()
    except Exception:
        line = "IN PROGRESS .."
        log_text.insert(tk.END, line)
        log_text.see(tk.END)
        window.update()
    finally:
        print("close")


    
    process.stdout.close()
    return_code = process.wait()
    
    messagebox.showinfo("Process Completed", "Transcription process has finished.")


# Create and position GUI elements
file_label = tk.Label(window, text="Selected Files:")
file_label.pack()

file_list = tk.Text(window, height=5, width=50)
file_list.pack()

file_button = tk.Button(window, text="Select Files", command=select_files)
file_button.pack()

def handle_model_selection(event):
    selected_model = model_combobox.get()
    print(f"Selected model: {selected_model}")

model_options = [
    "tiny.en",
    "tiny",
    "base.en",
    "base",
    "small.en",
    "small",
    "medium.en",
    "medium",
    "large"
]


model_label = tk.Label(window, text="Select model: DEFULT = base")
model_label.pack()

# Create the model combobox
model_combobox = ttk.Combobox(window, values=model_options)
model_combobox.pack()

# Bind the selection event
model_combobox.bind("<<ComboboxSelected>>", handle_model_selection)

output_dir_label = tk.Label(window, text="Output Directory:")
output_dir_label.pack()

output_dir_entry = tk.Entry(window)
output_dir_entry.pack()

output_srt_var = tk.BooleanVar()
output_srt_check = tk.Checkbutton(window, text="Output .srt File", variable=output_srt_var)
output_srt_check.pack()

srt_only_var = tk.BooleanVar()
srt_only_check = tk.Checkbutton(window, text="Only Generate .srt File", variable=srt_only_var)
srt_only_check.pack()

def handle_language_selection(event):
    selected_language = language_combobox.get()
    print(f"Selected language: {selected_language}")

# Create the language label
language_label = tk.Label(window, text="Select Language: DEFULT = English")
language_label.pack()

# Define the language options
language_options = [
    'auto', 'af', 'am', 'ar', 'as', 'az', 'ba', 'be', 'bg', 'bn', 'bo', 'br', 'bs', 'ca', 'cs', 'cy', 'da', 'de', 'el', 'en', 'es', 'et', 'eu', 'fa', 'fi', 'fo', 'fr', 'gl', 'gu', 'ha', 'haw', 'he', 'hi', 'hr', 'ht', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jw', 'ka', 'kk', 'km', 'kn', 'ko', 'la', 'lb', 'ln', 'lo', 'lt', 'lv', 'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my', 'ne', 'nl', 'nn', 'no', 'oc', 'pa', 'pl', 'ps', 'pt', 'ro', 'ru', 'sa', 'sd', 'si', 'sk', 'sl', 'sn', 'so', 'sq', 'sr', 'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tr', 'tt', 'uk', 'ur', 'uz', 'vi', 'yi', 'yo', 'zh'
]

# Create the language combobox
language_combobox = ttk.Combobox(window, values=language_options)
language_combobox.pack()

# Bind the selection event
language_combobox.bind("<<ComboboxSelected>>", handle_language_selection)

execute_button = tk.Button(window, text="Execute", command=execute_transcription)
execute_button.pack()

log_label = tk.Label(window, text="Logs:")
log_label.pack()

log_text = scrolledtext.ScrolledText(window, height=10, width=100)
log_text.pack()

# Run the GUI main loop
window.mainloop()
