import os
import sys
import time
import glob
import re
import subprocess
from app.src.errors import AudioException



def parse_timestamp(
        ts: float
    ) -> str:
    """
    Parse a timestamp into hours, minutes, and seconds.
    """
    h, m, s = int(ts // 3600), int((ts % 3600) // 60), int(ts % 60)
    return f"{h:02}:{m:02}:{s:02}"



def get_audio_duration(
        path: str
    ) -> float:
    """
    Get the duration of an audio file in seconds.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", 
                "-v", 
                "error", 
                "-show_entries", 
                "format=duration", 
                "-of",
                "default=noprint_wrappers=1:nokey=1", 
                path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        return float(result.stdout.strip())
    except Exception as e:
        raise AudioException(f"Error getting duration of {path}: {e}")



def split_mp3(
        input_file: str,
        temp_id: str,
        chunk_duration: float =600
    ) -> list[str]:
    """
    Split an MP3 file into smaller chunks of specified duration.
    """
    subprocess.run([
        'ffmpeg', 
        '-i', 
        input_file,
        '-f', 
        'segment',
        '-segment_time', 
        str(chunk_duration),
        '-c', 
        'copy',
        f'/tmp/chunk_{temp_id}%03d.mp3'
    ], check=True)

    # Collect all matching chunk files
    return sorted(glob.glob(f'/tmp/chunk_{temp_id}*.mp3'))



def progress_bar_callback(
        message: str
    ) -> None:
    """
    Callback function to display progress in the console.
    """
    bar_length = 30   # Length of progress bar
    match = re.search(r'(\d+)%', message)
    if match:
        percent = int(match.group(1))
        filled_length = int(bar_length * percent // 100)

        if filled_length == 0:
            bar = '>' + '_' * (bar_length - 1)
        elif filled_length >= bar_length:
            bar = '=' * bar_length
        else:
            bar = '=' * (filled_length - 1) + '>' + '_' * (bar_length - filled_length)

        sys.stdout.write(
            f'\rProgress: [{bar}] {percent}%'
        )
        sys.stdout.flush()

    elif "complete" in message.lower():
        sys.stdout.write(
            '\rProgress: [' + (bar_length * '=') + '] 100%\n'
        )
        sys.stdout.flush()

    else:
        print(message)



def cleanup_old_chunks(
        expiry_seconds: float
    ) -> None:
    """
    Delete /tmp/chunk_*.mp3 or *.wav files older than expiry_seconds.
    """
    patterns = ["/tmp/chunk_*.mp3", "/tmp/chunk_*.wav"]
    now = time.time()

    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > expiry_seconds:
                        os.remove(filepath)
                        print(f"Deleted: {filepath}")
            except Exception as e:
                print(f"Error deleting {filepath}: {e}")