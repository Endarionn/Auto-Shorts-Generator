import cv2
from moviepy.editor import VideoFileClip, CompositeVideoClip
import numpy as np

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
    
    # Resize the background to match the duration of the foreground
    background_clip = background_clip.set_duration(foreground_clip.duration)
    
    # Scale down the foreground video and set its position
    new_width = background_clip.w - 2 * margin
    new_height = (foreground_clip.h / foreground_clip.w) * new_width
    foreground_clip = foreground_clip.resize((new_width, new_height)).set_position(("center", "center"))

    # Composite the clips together
    final_clip = CompositeVideoClip([background_clip, foreground_clip])
    final_clip.write_videofile(output_video_path, codec='libx264')

# Paths to your videos
background_video_path = "C:\\Users\\ygzat\\Desktop\\Auto Shorts AI\\auto-subtitle-main\\auto-subtitle-main\\output_segments\\segment_1.mp4"
foreground_video_path = "C:\\Users\\ygzat\\Desktop\\Auto Shorts AI\\auto-subtitle-main\\auto-subtitle-main\output\\randıman.mp4"
blurred_background_video_path = 'blurred_background.mp4'
output_video_path = 'output_video2.mp4'

# Blur the background video
blur_background_video(background_video_path, blurred_background_video_path)

# Overlay the foreground video on the blurred background video
overlay_videos(blurred_background_video_path, foreground_video_path, output_video_path)
