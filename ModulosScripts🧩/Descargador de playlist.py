import os
import json
import re
import yt_dlp
import librosa
import numpy as np
from mutagen.id3 import ID3, TIT2, TPE1
from mutagen.mp3 import MP3
import warnings
import uuid
import time
from collections import defaultdict, Counter
import pyperclip

warnings.filterwarnings("ignore", category=FutureWarning)

def make_safe_filename(title):
    """Crea un nombre de archivo seguro para la mayoría de los sistemas de archivos."""
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def download_audio(video_url, output_path):
    """Descarga audio de YouTube en formato MP3 de alta calidad y extrae la información adicional."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        file_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        title = info_dict.get('title', None)
        uploader = info_dict.get('uploader', None)
        description = info_dict.get('description', None)
        return file_path, title, uploader, description

def analyze_audio(file_path):
    """Analiza las características del audio utilizando Librosa."""
    y, sr = librosa.load(file_path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    energy = np.sum(librosa.feature.rms(y=y)**2) / len(y)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    danceability = np.mean(librosa.util.normalize(onset_env))
    valence = np.mean(librosa.feature.tonnetz(y=y, sr=sr))

    return {
        'tempo': tempo,
        'energy': energy,
        'danceability': danceability,
        'valence': valence,
    }

def get_youtube_playlist_videos(playlist_url):
    """Obtiene las URL de los videos y el título de una lista de reproducción de YouTube."""
    ydl_opts = {
        'extract_flat': True,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)

    playlist_title = result.get('title', 'Unknown Playlist')
    video_entries = [
        {'url': f"https://www.youtube.com/watch?v={entry['id']}", 'title': entry.get('title', '')}
        for entry in result.get('entries', [])
    ]
    
    return playlist_title, video_entries

def process_single_video(entry, temp_path, playlist_path, processed_urls_file):
    try:
        audio_file, title, channel, description = download_audio(entry['url'], temp_path)
        print(f"Downloaded {title} from channel {channel}: {audio_file}")

        features = analyze_audio(audio_file)

        new_file_name = f"{make_safe_filename(title)}_"
        new_file_name += "_".join(f"{feature}[{value}]" for feature, value in features.items())
        new_file_name += f"_{make_safe_filename(channel)}.mp3"

        new_file_path = os.path.join(playlist_path, new_file_name)

        if os.path.exists(new_file_path):
            new_file_path = os.path.join(playlist_path, f"{uuid.uuid4()}_{new_file_name}")

        os.rename(audio_file, new_file_path)

        audio = MP3(new_file_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=channel))

        audio.save()

        with open(processed_urls_file, 'a') as f:
            f.write(f"{entry['url']}\n")

        print(f"Processed and moved: {new_file_path}")

    except Exception as e:
        print(f"Could not process video with URL {entry['url']}. Error: {e}")

def download_and_organize_youtube_videos(playlist_url, output_path):
    """Descarga y organiza videos de YouTube en función de sus características de audio y la lista de reproducción."""
    temp_path = os.path.join(output_path, 'temp')
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    try:
        playlist_title, video_entries = get_youtube_playlist_videos(playlist_url)
        playlist_folder = make_safe_filename(playlist_title)
        playlist_path = os.path.join(output_path, playlist_folder)
        if not os.path.exists(playlist_path):
            os.makedirs(playlist_path)
    except Exception as e:
        print(f"Failed to fetch playlist videos. Error: {e}")
        return

    print(f"\nIniciando descarga de la playlist: {playlist_title}")
    print(f"Total de videos en la playlist: {len(video_entries)}")

    processed_urls_file = os.path.join(playlist_path, 'processed_urls.txt')
    processed_urls = set()

    if os.path.exists(processed_urls_file):
        with open(processed_urls_file, 'r') as f:
            processed_urls = set(f.read().strip().split('\n'))

    new_video_entries = [entry for entry in video_entries if entry['url'] not in processed_urls]

    print(f"Videos nuevos por procesar: {len(new_video_entries)}")
    print(f"Videos ya procesados anteriormente: {len(processed_urls)}\n")

    for entry in new_video_entries:
        process_single_video(entry, temp_path, playlist_path, processed_urls_file)
        
        for file in os.listdir(temp_path):
            file_path = os.path.join(temp_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

if __name__ == "__main__":
    output_path = r'C:\\Users\\54115\\Desktop\\Playlist'
    
    # Obtener la URL del portapapeles
    playlist_url = pyperclip.paste().strip()
    
    if playlist_url:
        print("URL de playlist detectada en el portapapeles.")
        download_and_organize_youtube_videos(playlist_url, output_path)
    else:
        print("No se encontró ninguna URL en el portapapeles.")