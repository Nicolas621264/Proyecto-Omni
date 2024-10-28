import os
import asyncio
import feedparser
import yt_dlp
import whisper
import re
import openai
import requests
from openai.error import APIError, RateLimitError, AuthenticationError

# Función para hacer seguro el nombre del archivo
def make_safe_filename(title):
    safe_title = re.sub(r'[^\w\s-]', '', title)
    safe_title = safe_title.replace(' ', '_')
    return safe_title

# Función para verificar si el video es en vivo, un short o mayor a 1 hora
def is_ignored_video(video_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        if info_dict.get('is_live', False):
            return True
        duration = info_dict.get('duration', 0)
        if duration < 60 or 'shorts' in video_url or duration > 3600:
            return True
        return False

# Función para obtener la URL del video desde el feed
def get_video_url(entry):
    return entry.link

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

# Función para transcribir audio usando Whisper con marcas de tiempo
def transcribe_audio(file_path):
    print(f"Verificando existencia del archivo para transcripción: {file_path}")
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return ""

    try:
        print("Cargando el modelo Whisper...")
        model = whisper.load_model("base")
        print("Modelo cargado. Iniciando transcripción con marcas de tiempo...")
        result = model.transcribe(file_path, word_timestamps=True)

        transcription_with_timestamps = []
        for segment in result['segments']:
            start_time = segment['start']
            minutes, seconds = divmod(int(start_time), 60)
            timestamp = f"{minutes:02}:{seconds:02}"
            transcription_with_timestamps.append(f"[{timestamp}] {segment['text']}")

        return "\n".join(transcription_with_timestamps)
    except Exception as e:
        print(f"Error al transcribir el archivo {file_path}: {e}")
        return ""

# Configuración de OpenAI
openai.api_key = "OPENAI_API_KEY"  # Reemplaza con tu clave API de OpenAI
model_engine = "gpt-4o-mini"

# Prompt mejorado para resumen estructurado
prompt_resumen = """
Quiero que respondas solo en español. Su objetivo es dividir la parte de la transcripción en secciones de información con un tema común y anotar la marca de tiempo inicial de cada sección. Cada bloque de información no debe durar menos de 2 minutos, contener la marca de tiempo del inicio de la sección, una descripción textual del contenido principal de toda la sección y de 1 a 3 viñetas que detallan las ideas principales de toda la sección. Su respuesta debe ser concisa, informativa y fácil de leer y comprender. Utilice el formato especificado:[URL de marca de tiempo de inicio de sección] [Emoji de sección] [Conclusión clave de sección en español]Conclusión clave de sección,[Utilice tantas viñetas para las conclusiones clave de sección como necesite].Siga el formato requerido, no escriba cualquier cosa adicional, evite frases genéricas y no repita mi tarea. La marca de tiempo debe presentarse en formato URL de rebajas. El texto de la URL indica y la dirección enlaza a un momento específico en el video, por ejemplo:
00:05 [URL de marca de tiempo de inicio de sección] 🤖
 ...02:18[URL de marca de tiempo de inicio de sección)] 🛡
 ...05:37[URL de marca de tiempo de inicio de sección] 💼
 ...
Mantenga los emoji relevantes y únicos para cada sección. No uses el mismo emoji para cada sección. No renderice corchetes. No anteponga la comillas para llevar con "Conclusión clave".
"""

# Configuración de Telegram
bot_token = 'TELEGRAM_TOKEN'  # Reemplaza con tu token de la API de Telegram
chat_id_group3 = '@canalnoticiasia'

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.json()

async def send_telegram_message(token, chat_id, title, resumen_estructurado):
    message = f"<b>Resumen estructurado para {title}:</b>\n{resumen_estructurado}"

    MAX_MESSAGE_LENGTH = 4096
    if len(message) <= MAX_MESSAGE_LENGTH:
        response = send_message(token, chat_id, message)
        if not response['ok']:
            print(f"Error al enviar mensaje a Telegram: {response}")
    else:
        for x in range(0, len(message), MAX_MESSAGE_LENGTH):
            response = send_message(token, chat_id, message[x:x + MAX_MESSAGE_LENGTH])
            if not response['ok']:
                print(f"Error al enviar mensaje a Telegram: {response}")
                break

async def process_channel(channel_id, output_path, bot_token, chat_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    existing_files = os.listdir(output_path)
    existing_titles = [os.path.splitext(file)[0] for file in existing_files]

    transcriptions_done_path = os.path.join(output_path, "transcriptions_done.txt")
    if os.path.exists(transcriptions_done_path):
        with open(transcriptions_done_path, 'r') as file:
            transcriptions_done = file.read().splitlines()
    else:
        transcriptions_done = []

    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:2]:
        video_url = get_video_url(entry)
        title = entry.title
        safe_title = make_safe_filename(title)

        if safe_title in existing_titles or video_url in transcriptions_done:
            print(f"Omitiendo {title}: ya está descargado o transcrito.")
            continue

        if is_ignored_video(video_url):
            print(f"Omitiendo {title}: es un video en vivo, un short o mayor a 1 hora.")
            continue

        # Guardar la URL en el archivo de transcripciones hechas
        with open(transcriptions_done_path, 'a') as file:
            file.write(f"{video_url}\n")

        mp3_path = download_audio(video_url, output_path, title)

        if not os.path.exists(mp3_path):
            print(f"No se pudo encontrar el archivo .mp3 para {title}")
            continue

        print(f"Archivo descargado: {mp3_path}")

        transcription = transcribe_audio(mp3_path)
        if transcription:
            print(f"Transcripción completada para {title}:\n{transcription}\n")

            try:
                # Enviar la transcripción con la URL del video a GPT-4 para el resumen
                response = await openai.ChatCompletion.acreate(
                    model=model_engine,
                    messages=[
                        {"role": "system", "content": prompt_resumen},
                        {"role": "user", "content": f"Transcripción:\n{transcription}\n\nURL del video: {video_url}"}
                    ],
                    max_tokens=1000,
                )

                resumen_estructurado = response.choices[0].message['content']
                print(f"Resumen estructurado para {title}:\n{resumen_estructurado}\n")

                # Enviar solo el resumen estructurado a Telegram
                await send_telegram_message(bot_token, chat_id, safe_title, resumen_estructurado)

                # Eliminar archivo de audio después de enviar el resumen
                os.remove(mp3_path)
                print(f"Archivo de audio eliminado: {mp3_path}")

            except (APIError, RateLimitError, AuthenticationError) as e:
                print(f"Error al obtener el resumen para {title}: {e}")
                await send_telegram_message(bot_token, chat_id, safe_title, f"Error al procesar {title}: {e}")

async def main():
    # Tercer grupo de canales
    channel_ids_group3 = ["UCl5-lvQyfILb-l2abPk4Ntg", "UC5rJaxmE3UyVz59OGxbPdAg","UC3nwmvE2aDzUSJ4evQ1NhoA","UCy5znSnfMsDwaLlROnZ7Qbg","UCP15FVAA2UL-QOcGhy7-ezA"]
    output_path_group3 = "C:/ruta/a/tu/directorio/group3"  # Reemplaza con la ruta a tu directorio
    chat_id_group3 = '@canalnoticiasia'

    tasks = []
    for channel_id in channel_ids_group3:
        tasks.append(process_channel(channel_id, output_path_group3, bot_token, chat_id_group3))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
