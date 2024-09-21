import os
import argparse
from moviepy.editor import VideoFileClip

def crop_and_split_video(input_file, output_dir):
    # Load the video file
    video = VideoFileClip(input_file)
    
    # Get video properties
    width, height = video.size
    duration = video.duration
    
    # Calculate the crop dimensions for 9:16 aspect ratio
    target_aspect_ratio = 9 / 16
    target_height = height
    target_width = int(target_height * target_aspect_ratio)
    
    if target_width > width:
        target_width = width
        target_height = int(target_width / target_aspect_ratio)
    
    crop_x_center = width // 2
    crop_y_center = height // 2
    
    x1 = crop_x_center - (target_width // 2)
    y1 = crop_y_center - (target_height // 2)
    x2 = x1 + target_width
    y2 = y1 + target_height
    
    # Crop the video to the desired aspect ratio
    cropped_video = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    
    # Split the video into 60-second segments
    segment_duration = 60
    num_segments = int(duration // segment_duration)
    
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = start_time + segment_duration
        
        segment = cropped_video.subclip(start_time, end_time)
        segment_filename = os.path.join(output_dir, f'segment_{i+1}.mp4')
        segment.write_videofile(segment_filename, codec='libx264')
    
    # Close the video file
    video.close()
    cropped_video.close()

def main():
    parser = argparse.ArgumentParser(description="Video kesme ve kırpma aracı")
    parser.add_argument("--video", type=str, required=True, help="Giriş video dosyasının yolu")
    parser.add_argument("--output_dir", type=str, default="output_segments", help="Çıktı klasörünün yolu (varsayılan: 'output_segments')")

    args = parser.parse_args()

    input_file = args.video
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    crop_and_split_video(input_file, output_dir)

if __name__ == "__main__":
    main()
