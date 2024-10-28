import os
import asyncio
import yt_dlp
import whisper
import re
import pyautogui
import pyperclip  # Importa pyperclip para manejar el portapapeles
import feedparser
import time

# Función para hacer seguro el nombre del archivo
def make_safe_filename(title):
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = safe_title.replace(' ', '_')
    return safe_title

# Función para descargar audio de YouTube
def download_audio(video_url, output_path, title):
    safe_title = make_safe_filename(title)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, f'{safe_title}.%(ext)s'),
        'ffmpeg_location': 'C:/ffmpeg/bin',  # Reemplaza con la ruta a tu instalación de FFmpeg
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': 'C:/Users/54115/Documents/cookies.txt'  # Reemplaza con la ruta a tu archivo de cookies
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return os.path.join(output_path, f'{safe_title}.mp3')

# Función para transcribir audio usando Whisper y agregar marcas de tiempo
def transcribe_audio(file_path):
    print(f"Verificando existencia del archivo para transcripción: {file_path}")
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return ""

    try:
        print("Cargando el modelo Whisper...")
        model = whisper.load_model("base")
        print("Modelo cargado. Iniciando transcripción...")
        result = model.transcribe(file_path, word_timestamps=True)
        
        # Construir la transcripción con marcas de tiempo
        transcription_with_timestamps = ""
        for segment in result['segments']:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            transcription_with_timestamps += f"{format_timestamp(start_time)} - {format_timestamp(end_time)}: {text}\n"

        return transcription_with_timestamps
    except Exception as e:
        print(f"Error al transcribir el archivo {file_path}: {e}")
        return ""

# Función para formatear los timestamps en formato de minutos:segundos (MM:SS)
def format_timestamp(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Función para copiar texto al portapapeles junto con el prompt
def copy_to_clipboard(transcription, video_url):
    prompt = (
        "Quiero que respondas solo en español. Su objetivo es dividir la parte de la transcripción en secciones de "
        "información con un tema común y anotar la marca de tiempo inicial de cada sección. Cada bloque de información "
        "no debe durar menos de 2 minutos, contener la marca de tiempo del inicio de la sección, una descripción textual "
        "del contenido principal de toda la sección y de 1 a 3 viñetas que detallan las ideas principales de toda la sección. "
        "Su respuesta debe ser concisa, informativa y fácil de leer y comprender. Utilice el formato especificado: "
        "[URL de marca de tiempo de inicio de sección] [Emoji de sección] [Conclusión clave de sección en español] "
        "Conclusión clave de sección,[Utilice tantas viñetas para las conclusiones clave de sección como necesite]. "
        "Siga el formato requerido, no escriba cualquier cosa adicional, evite frases genéricas y no repita mi tarea. "
        "La marca de tiempo debe presentarse en formato URL de rebajas. El texto de la URL indica y la dirección enlaza a un "
        "momento específico en el video, por ejemplo:\n"
        "00:05 [URL de marca de tiempo de inicio de sección] 🤖\n"
        "02:18 [URL de marca de tiempo de inicio de sección] 🛡\n"
        "05:37 [URL de marca de tiempo de inicio de sección] 💼\n"
        "...\n"
        "Mantenga los emoji relevantes y únicos para cada sección. No uses el mismo emoji para cada sección. No renderice corchetes. "
        "No anteponga la comillas para llevar con 'Conclusión clave'."
    )
    
    full_text = f"{prompt}\n\nURL del video: {video_url}\n\nTranscripción:\n{transcription}"
    pyperclip.copy(full_text)
    print("Texto y prompt copiados al portapapeles.")

# Función para ejecutar la combinación de teclas
def execute_shortcut_sequence():
    print("Ejecutando combinación de teclas Windows + 5")
    pyautogui.hotkey('win', '1')
    time.sleep(3)  # Espera 3 segundos
    print("Pegando el texto copiado")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(3)  # Espera 3 segundos
    print("Presionando Enter")
    pyautogui.press('enter')
    time.sleep(20)
    pyautogui.hotkey('ctrl', 'shift', 'c')
    time.sleep(3)
    pyautogui.hotkey('win', '6')
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    pyautogui.press('enter')

async def process_video(video_url, output_path, title):
    mp3_path = download_audio(video_url, output_path, title)

    if not os.path.exists(mp3_path):
        print(f"No se pudo encontrar el archivo .mp3 para {title}")
        return

    print(f"Archivo descargado: {mp3_path}")

    transcription = transcribe_audio(mp3_path)
    if transcription:
        print(f"Transcripción completada para {title}:\n{transcription}\n")
        copy_to_clipboard(transcription, video_url)  # Copiar la transcripción junto con el prompt y la URL al portapapeles
        execute_shortcut_sequence()  # Ejecutar la secuencia de teclas

async def main():
    channel_id = "UC3nwmvE2aDzUSJ4evQ1NhoA"  # Reemplaza con el ID de tu canal
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    output_path = "C:/ruta/a/tu/directorio"  # Reemplaza con la ruta a tu directorio

    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:2]:
        video_url = entry.link
        title = entry.title
        await process_video(video_url, output_path, title)

if __name__ == "__main__":
    asyncio.run(main())
