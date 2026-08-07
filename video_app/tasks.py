import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def convert_to_hls_job(input_path, video_id):
    """
    Convert a video file into HLS format (HTTP Live Streaming)
    with multiple resolutions: 480p, 720p, and 1080p.

    This function:
    - Creates a directory structure for the video
    - Generates HLS playlists and segments for each resolution
    - Uses FFmpeg to perform scaling and HLS packaging

    Args:
        input_path (str): Path to the original uploaded video file.
        video_id (int): ID of the video, used to create a unique output folder.

    Output structure:
        /<video_id>/
            /480p/index.m3u8
            /720p/index.m3u8
            /1080p/index.m3u8
    """
        
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

        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", scale,
            "-profile:v", "baseline", "-level", "3.0",
            "-start_number", "0", "-hls_time", "10", "-hls_list_size", "0",
            "-f", "hls", output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("FFmpeg finished %s successfully for %s", res, video_id)
        except subprocess.CalledProcessError as e:
            logger.error(
                "FFmpeg failed for video %s (%s): %s",
                video_id, res, e.stderr
            )
            raise