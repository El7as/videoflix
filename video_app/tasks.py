import json
import logging
import os
import shutil
import subprocess
import tempfile

from django.conf import settings

logger = logging.getLogger(__name__)

RESOLUTION_LADDER = [
    ('480p', 480, '1400k', '128k', '1498k', '2100k'),
    ('720p', 720, '2800k', '128k', '2996k', '4200k'),
    ('1080p', 1080, '5000k', '192k', '5350k', '7500k'),
]

FFMPEG_TIMEOUT_SECONDS = 60 * 30  


class HLSConversionError(Exception):
    """Raised when the HLS conversion fails."""


def _probe_source_height(input_path: str) -> int:
    """Reads the source video's height via ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=height',
        '-of', 'json',
        input_path,
    ]
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        streams = data.get('streams') or []
        if not streams or 'height' not in streams[0]:
            raise HLSConversionError(f'Could not read video stream info from {input_path}')
        return int(streams[0]['height'])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
        raise HLSConversionError(f'ffprobe failed for {input_path}: {e}') from e


def _encode_variant(input_path: str, output_dir: str, height: int,
                     video_bitrate: str, audio_bitrate: str,
                     maxrate: str, bufsize: str) -> None:
    output_path = os.path.join(output_dir, 'index.m3u8')
    segment_path = os.path.join(output_dir, '%03d.ts')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', f'scale=-2:{height}',
        '-c:v', 'libx264',
        '-profile:v', 'main',
        '-level', '3.1',
        '-b:v', video_bitrate,
        '-maxrate', maxrate,
        '-bufsize', bufsize,
        '-preset', 'veryfast',
        '-force_key_frames', 'expr:gte(t,n_forced*10)',
        '-sc_threshold', '0',
        '-c:a', 'aac',
        '-b:a', audio_bitrate,
        '-ac', '2',
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-hls_flags', 'independent_segments',
        '-hls_segment_filename', segment_path,
        '-f', 'hls',
        output_path,
    ]

    try:
        subprocess.run(
            cmd, check=True, capture_output=True, text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as e:
        raise HLSConversionError(
            f'FFmpeg timeout after {FFMPEG_TIMEOUT_SECONDS}s at {height}p'
        ) from e
    except subprocess.CalledProcessError as e:
        raise HLSConversionError(
            f'FFmpeg failed at {height}p: {e.stderr}'
        ) from e


def convert_to_hls_job(input_path: str, video_id: int) -> str:
    """
    Converts a video file into HLS (HTTP Live Streaming) with multiple
    resolutions (up to the source resolution).

    This function:
    - Checks that the input file exists and reads its resolution
    - Generates one HLS variant per resolution <= source resolution
      (H.264/AAC, bitrate ladder, keyframes tied to segment length)
    - Renders into a temporary directory first and only moves the result
      to the final location on full success (a half-finished output is
      never served)

    Note: there is deliberately NO cross-resolution master playlist - the
    API serves each resolution individually under
    /api/video/<movie_id>/<resolution>/index.m3u8, so resolution selection
    happens on the client side.

    Args:
        input_path: Path to the originally uploaded file.
        video_id: ID of the video, used for the target directory.

    Returns:
        Path to the video's base directory (<base_dir>).

    Raises:
        HLSConversionError: on validation or FFmpeg errors.

    Output structure:
        /<video_id>/
            /480p/index.m3u8
                  000.ts, 001.ts, ...
            /720p/index.m3u8
                  000.ts, 001.ts, ...
            /1080p/index.m3u8
                  000.ts, 001.ts, ...
    """
    
    if not os.path.isfile(input_path):
        raise HLSConversionError(f'Input file not found: {input_path}')

    source_height = _probe_source_height(input_path)

    variants_to_encode = [
        v for v in RESOLUTION_LADDER if v[1] <= source_height
    ] or [RESOLUTION_LADDER[0]]

    final_base_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(video_id))

    with tempfile.TemporaryDirectory(prefix=f'hls_{video_id}_') as tmp_base_dir:
        for res_name, height, video_bitrate, audio_bitrate, maxrate, bufsize in variants_to_encode:
            output_dir = os.path.join(tmp_base_dir, res_name)
            os.makedirs(output_dir, exist_ok=True)

            logger.info('Starting FFmpeg %s for video %s', res_name, video_id)
            try:
                _encode_variant(
                    input_path, output_dir, height,
                    video_bitrate, audio_bitrate, maxrate, bufsize,
                )
            except HLSConversionError:
                logger.exception(
                    'FFmpeg failed for video %s (%s)', video_id, res_name
                )
                raise

            logger.info('FFmpeg finished %s for video %s', res_name, video_id)

        if os.path.exists(final_base_dir):
            shutil.rmtree(final_base_dir)
        os.makedirs(os.path.dirname(final_base_dir), exist_ok=True)
        shutil.move(tmp_base_dir, final_base_dir)
        os.makedirs(tmp_base_dir, exist_ok=True)

    return final_base_dir

