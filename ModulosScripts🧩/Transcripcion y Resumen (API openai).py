import os
import asyncio
import yt_dlp
import whisper
import re
import openai
import pyperclip

# Rutas de carpetas
resumenes_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Youtube", "Resumenes")
temp_audio_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Youtube", "Temp_Audios")

# Asegurar que las carpetas existen
os.makedirs(resumenes_folder, exist_ok=True)
os.makedirs(temp_audio_folder, exist_ok=True)

# Configuración de OpenAI
openai.api_key = "OPENAI_API_KEY"
model_engine = "gpt-4o-mini"

def make_safe_filename_from_url(url):
    """Función para hacer seguro el nombre del archivo desde la URL"""
    safe_title = re.sub(r'[^\w\s-]', '', url)
    safe_title = safe_title.replace(' ', '_')
    return safe_title

def download_audio(video_url, temp_audio_path, url_as_filename):
    """Función para descargar audio de YouTube"""
    safe_title = make_safe_filename_from_url(url_as_filename)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_audio_path, f'{safe_title}.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return os.path.join(temp_audio_path, f'{safe_title}.mp3')
    except Exception as e:
        print(f"Error al descargar el video: {e}")
        return None

def transcribe_audio(file_path):
    """Función para transcribir audio usando Whisper con marcas de tiempo"""
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

# Prompt para resumen estructurado
prompt_resumen = """
Quiero que respondas solo en español. Su objetivo es dividir la parte de la transcripción en secciones de información con un tema común y anotar la marca de tiempo inicial de cada sección. Cada bloque de información no debe durar menos de 2 minutos, contener la marca de tiempo del inicio de la sección, una descripción textual del contenido principal de toda la sección y de 1 a 3 viñetas que detallan las ideas principales de toda la sección. Su respuesta debe ser concisa, informativa y fácil de leer y comprender. Utilice el formato especificado:
[URL de marca de tiempo de inicio de sección] [Emoji de sección] [Conclusión clave de sección en español]
• Punto clave 1
• Punto clave 2
• Punto clave 3 (opcional)
"""

async def process_video(video_url):
    """Función principal para procesar un video de YouTube"""
    print(f"Iniciando procesamiento del video: {video_url}")
    
    # Descargar el audio del video
    mp3_path = download_audio(video_url, temp_audio_folder, video_url)
    if not mp3_path or not os.path.exists(mp3_path):
        print(f"No se pudo descargar el audio para {video_url}")
        return

    print(f"Archivo descargado: {mp3_path}")

    # Transcribir el audio
    transcription = transcribe_audio(mp3_path)
    if transcription:
        print(f"Transcripción completada para {video_url}")

        try:
            # Enviar la transcripción a GPT-4 para el resumen
            print("Generando resumen con GPT-4...")
            response = await openai.ChatCompletion.acreate(
                model=model_engine,
                messages=[
                    {"role": "system", "content": prompt_resumen},
                    {"role": "user", "content": f"Transcripción:\n{transcription}\n\nURL del video: {video_url}"}
                ],
                max_tokens=4096,
            )

            resumen_estructurado = response.choices[0].message['content']
            print("Resumen estructurado generado.")

            # Copiar el resumen al portapapeles
            pyperclip.copy(resumen_estructurado)
            print("El resumen ha sido copiado al portapapeles.")

            # Guardar el resumen en un archivo
            safe_title = make_safe_filename_from_url(video_url)
            resumen_path = os.path.join(resumenes_folder, f"resumen_{safe_title}.txt")
            with open(resumen_path, "w", encoding="utf-8") as f:
                f.write(resumen_estructurado)
            print(f"Resumen guardado en: {resumen_path}")

        except Exception as e:
            print(f"Error al obtener el resumen para {video_url}: {e}")
        
        finally:
            # Eliminar el archivo de audio temporal
            try:
                os.remove(mp3_path)
                print(f"Archivo de audio temporal eliminado: {mp3_path}")
            except Exception as e:
                print(f"Error al eliminar el archivo temporal: {e}")

    else:
        print(f"Transcripción fallida para {video_url}. No se continuará con el resumen.")

async def main():
    """Función principal para ejecutar el proceso"""
    try:
        youtube_url = pyperclip.paste()
        if not youtube_url:
            print("No se encontró ninguna URL en el portapapeles.")
            return
        if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            print("La URL en el portapapeles no parece ser de YouTube.")
            return
            
        print(f"URL de YouTube encontrada en el portapapeles: {youtube_url}")
        await process_video(youtube_url)
        print("Proceso de resumen completado")
    except Exception as e:
        print(f"Error al procesar la URL del portapapeles: {e}")

if __name__ == "__main__":
    asyncio.run(main())