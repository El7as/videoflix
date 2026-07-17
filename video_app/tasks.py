import os
import subprocess

def convert_to_hls_job(input_path, video_id):
    base_dir = os.path.join(os.path.dirname(input_path), str(video_id))
    os.makedirs(base_dir, exist_ok=True)

    resolutions = {
        "480p": "scale=-2:480",
        "720p": "scale=-2:720",
        "1080p": "scale=-2:1080",
    }

    for res, scale in resolutions.items():
        output_dir = os.path.join(base_dir, res)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "index.m3u8")

        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-vf", scale,
            "-profile:v", "baseline", "-level", "3.0",
            "-start_number", "0", "-hls_time", "10", "-hls_list_size", "0",
            "-f", "hls", output_path
        ])
