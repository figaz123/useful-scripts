import os
from PIL import Image
import argparse
import ffmpeg # Make sure you have 'ffmpeg-python' installed: pip install ffmpeg-python

def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def compress_img(image_name, dest_folder, new_size_ratio=0.9, quality=90, width=None, height=None, to_jpg=True):
    # This function remains exactly the same
    img = Image.open(image_name)
    print("[*] Image shape:", img.size)
    image_size = os.path.getsize(image_name)
    print("[*] Size before compression:", get_size_format(image_size))
    
    if new_size_ratio < 1.0:
        img = img.resize((int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)), Image.LANCZOS)
        print("[+] New Image shape:", img.size)
    elif width and height:
        img = img.resize((width, height), Image.LANCZOS)
        print("[+] New Image shape:", img.size)
    
    base_filename, ext = os.path.splitext(os.path.basename(image_name))
    
    if to_jpg:
        new_filename = f"{base_filename}_compressed.jpg"
    else:
        new_filename = f"{base_filename}_compressed{ext}"

    new_filepath = os.path.join(dest_folder, new_filename)

    try:
        img.save(new_filepath, quality=quality, optimize=True)
    except OSError:
        img = img.convert("RGB")
        img.save(new_filepath, quality=quality, optimize=True)

    print(f"[+] New file saved: {new_filepath}")
    new_image_size = os.path.getsize(new_filepath)
    print("[+] Size after compression:", get_size_format(new_image_size))
    saving_diff = new_image_size - image_size
    print(f"[+] Image size change: {saving_diff/image_size*100:.2f}% of the original image size.")

def compress_video(video_full_path, output_file_name, target_size):
    # This function also remains exactly the same.
    # It already accepts the target_size in KB, which we will now calculate
    # based on the user's percentage input.
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000

    probe = ffmpeg.probe(video_full_path)
    duration = float(probe['format']['duration'])
    audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate
    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, os.devnull,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                  ).overwrite_output().run()
    ffmpeg.output(i, output_file_name,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                  ).overwrite_output().run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Python script for compressing and resizing images/videos in a folder")
    
    # Image arguments
    parser.add_argument("-j", "--to-jpg", action="store_true", help="Whether to convert the image to the JPEG format")
    parser.add_argument("-q", "--quality", type=int, help="Quality ranging from a minimum of 0 (worst) to a maximum of 95 (best). Default is 90", default=90)
    parser.add_argument("-r", "--resize-ratio", type=float, help="Resizing ratio (for images) from 0 to 1, setting to 0.5 will multiply width & height of the image by 0.5. Default is 1.0", default=1.0)
    parser.add_argument("-w", "--width", type=int, help="The new width image, make sure to set it with the `height` parameter")
    parser.add_argument("-hh", "--height", type=int, help="The new height for the image, make sure to set it with the `width` parameter")
    
    # --- MODIFIED: Video argument ---
    # Changed from "--size" (int) to "--size-ratio" (float)
    # Added 'dest="size_ratio"' so the variable is args.size_ratio
    # Used '%%' to display a literal '%' in the help text
    parser.add_argument("-s", "--size-ratio", dest="size_ratio", type=float, 
                        help="Target size RATIO for VIDEOS from 0.1 to 1.0 (e.g., 0.5 for 50%% of original size). Video compression is skipped if not provided.")
    
    args = parser.parse_args()
    
    # print the passed arguments
    print("="*50)
    print("Compression Settings:")
    print(f"[*] To JPEG: {args.to_jpg}")
    print(f"[*] Quality: {args.quality}")
    print(f"[*] Resizing ratio: {args.resize_ratio}")
    if args.width and args.height:
        print(f"[*] Width: {args.width}")
        print(f"[*] Height: {args.height}")
        
    # --- MODIFIED: Print video ratio ---
    if args.size_ratio and 0 < args.size_ratio < 1.0:
        print(f"[*] Video Target Ratio: {args.size_ratio * 100:.0f}% of original size")
    else:
        print("[*] Video Target Ratio: Not set or invalid (videos will be skipped)")
    print("="*50)

    # --- Get folder path from user ---
    folder_path = input("[?] Please enter the path to the SOURCE folder: ")
    dest_folder_path = input("[?] Please enter the path for the DESTINATION folder: ")
    os.makedirs(dest_folder_path, exist_ok=True)
    print(f"[*] Compressed files will be saved to: {dest_folder_path}")

    # --- Validate folder and loop through files ---
    if not os.path.isdir(folder_path):
        print(f"[!] Error: The path '{folder_path}' is not a valid directory.")
    else:
        print(f"[*] Processing folder: {folder_path}")
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv'}
        
        for filename in os.listdir(folder_path):
            base_filename, ext = os.path.splitext(filename)
            file_ext_lower = ext.lower()
            
            source_file_path = os.path.join(folder_path, filename)
            
            if not os.path.isfile(source_file_path):
                continue 
            
            # --- Image Processing (no change) ---
            if file_ext_lower in image_extensions:
                print("-" * 50)
                print(f"[*] Compressing Image: {filename}")
                try:
                    compress_img(source_file_path, dest_folder_path, args.resize_ratio, 
                                 args.quality, args.width, args.height, args.to_jpg)
                except Exception as e:
                    print(f"[!] Failed to compress image {filename}: {e}")
            
            # --- MODIFIED: Video processing logic ---
            elif file_ext_lower in video_extensions:
                # Check for a valid ratio (between 0 and 1, but not 1)
                if args.size_ratio and 0 < args.size_ratio < 1.0: 
                    print("-" * 50)
                    print(f"[*] Compressing Video: {filename}")
                    try:
                        new_video_filename = f"{base_filename}_compressed{ext}"
                        output_video_path = os.path.join(dest_folder_path, new_video_filename)
                        
                        # --- NEW: Calculate target size from ratio ---
                        original_size_bytes = os.path.getsize(source_file_path)
                        # Calculate the target size in Kilobytes
                        target_size_kb = (original_size_bytes * args.size_ratio) / 1024 
                        
                        print(f"[*] Original size: {get_size_format(original_size_bytes)}")
                        print(f"[*] Target size:   ~{get_size_format(target_size_kb * 1024)}")
                        
                        # Pass the calculated KB size to the function
                        compress_video(source_file_path, output_video_path, target_size_kb)
                        
                    except Exception as e:
                        print(f"[!] Failed to compress video {filename}: {e}")
                else:
                    pass 
            else:
                pass
                
        print("="*50)
        print("[+] Folder processing complete.")