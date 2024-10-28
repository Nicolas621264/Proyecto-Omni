import sounddevice as sd
import numpy as np
import wave
import time
import os
import whisper
from datetime import datetime
import threading
import queue

class AudioRecorderTranscriber:
    def __init__(self, save_path, sample_rate=44100):
        # Configuración básica
        self.save_path = save_path
        self.sample_rate = sample_rate
        self.channels = 2
        self.segment_duration = 10  # duración en segundos
        self.is_recording = False
        
        # Cola para procesar las transcripciones de manera asíncrona
        self.transcription_queue = queue.Queue()
        
        # Crear carpetas si no existen
        self.audio_temp_path = os.path.join(save_path, "temp_audio")
        os.makedirs(self.audio_temp_path, exist_ok=True)
        os.makedirs(save_path, exist_ok=True)
        
        # Cargar modelo Whisper
        print("Cargando modelo Whisper...")
        self.model = whisper.load_model("base")
        print("Modelo Whisper cargado")

    def record_segment(self):
        """Graba un segmento de audio"""
        print(f"Grabando segmento de {self.segment_duration} segundos...")
        
        # Calcular el número total de frames para el segmento
        frames = int(self.sample_rate * self.segment_duration)
        
        # Grabar audio
        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16
        )
        sd.wait()
        
        return recording

    def save_audio_segment(self, recording, timestamp):
        """Guarda el segmento de audio en un archivo temporal"""
        audio_filename = os.path.join(self.audio_temp_path, f"segment_{timestamp}.wav")
        
        with wave.open(audio_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 2 bytes para int16
            wf.setframerate(self.sample_rate)
            wf.writeframes(recording.tobytes())
        
        return audio_filename

    def transcribe_segment(self, audio_file, timestamp):
        """Transcribe un segmento de audio y guarda la transcripción"""
        try:
            # Realizar la transcripción
            result = self.model.transcribe(audio_file)
            
            # Crear el archivo de transcripción
            transcription_file = os.path.join(
                self.save_path, 
                f"transcripcion_{timestamp}.txt"
            )
            
            # Guardar la transcripción
            with open(transcription_file, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Transcripción:\n{result['text']}\n")
            
            print(f"Transcripción guardada: {transcription_file}")
            
            # Eliminar el archivo de audio temporal
            os.remove(audio_file)
            
        except Exception as e:
            print(f"Error en la transcripción: {e}")

    def transcription_worker(self):
        """Worker para procesar las transcripciones en segundo plano"""
        while self.is_recording or not self.transcription_queue.empty():
            try:
                audio_file, timestamp = self.transcription_queue.get(timeout=1)
                self.transcribe_segment(audio_file, timestamp)
                self.transcription_queue.task_done()
            except queue.Empty:
                continue

    def start_recording(self):
        """Inicia el proceso de grabación continua"""
        self.is_recording = True
        
        # Iniciar el worker de transcripción en un hilo separado
        transcription_thread = threading.Thread(target=self.transcription_worker)
        transcription_thread.start()
        
        print("Iniciando grabación continua... Presiona Ctrl+C para detener.")
        
        try:
            while self.is_recording:
                # Obtener timestamp actual
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Grabar segmento
                recording = self.record_segment()
                
                # Guardar audio
                audio_file = self.save_audio_segment(recording, timestamp)
                
                # Agregar a la cola de transcripción
                self.transcription_queue.put((audio_file, timestamp))
                
        except KeyboardInterrupt:
            print("\nDetención solicitada por el usuario.")
        finally:
            self.is_recording = False
            transcription_thread.join()
            print("Grabación detenida y transcripciones completadas.")

def main():
    # Ruta donde se guardarán las transcripciones
    save_path = r"C:\Users\54115\Desktop\Omni\BaseDeDatos📁\Personal\GrabacionAudio"
    
    # Crear y ejecutar el grabador/transcriptor
    recorder = AudioRecorderTranscriber(save_path)
    recorder.start_recording()

if __name__ == "__main__":
    main()