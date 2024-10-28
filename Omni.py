import os
import subprocess
import time
import threading
import keyboard
import win32gui
import logging
import json
import telebot
import openai
import pyperclip
import re
import sys
import psutil
from dataclasses import dataclass
from typing import Dict, Optional, Callable, List
from datetime import datetime

@dataclass
class PixelState:
    is_active: bool = False
    last_color: Optional[int] = None
    last_execution: float = 0

@dataclass
class ScriptChainState:
    is_running: bool = False
    process: Optional[subprocess.Popen] = None

@dataclass
class MessageContext:
    original_message: str
    command_response: str
    timestamp: datetime

class ClipboardMonitor:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.running = True
        self.last_content = pyperclip.paste()

    def monitor(self):
        while self.running:
            current_content = pyperclip.paste()
            if current_content != self.last_content:
                self.last_content = current_content
                self.callback(current_content)
            time.sleep(0.5)

    def stop(self):
        self.running = False

class PixelMonitor:
    def __init__(self, config: dict, execute_script: Callable, send_clipboard: Callable):
        self.config = config['PIXELES_MONITOREAR']
        self.execute_script = execute_script
        self.send_clipboard = send_clipboard
        self.running = True
        self.states = {name: PixelState() for name in self.config}

    def get_pixel_color(self, x: int, y: int) -> Optional[int]:
        try:
            hdc = win32gui.GetWindowDC(win32gui.GetDesktopWindow())
            color = win32gui.GetPixel(hdc, x, y)
            win32gui.ReleaseDC(win32gui.GetDesktopWindow(), hdc)
            return color
        except Exception as e:
            logging.error(f"Error getting pixel color: {e}")
            return None

    def monitor(self):
        while self.running:
            for name, config in self.config.items():
                current_color = self.get_pixel_color(*config['coordenadas'])
                if current_color is None:
                    continue

                state = self.states[name]
                if current_color == state.last_color:
                    continue

                state.last_color = current_color
                current_time = time.time()
                
                if current_time - state.last_execution < 0.5:
                    continue

                if 'color_inicial' in config:
                    if not state.is_active and current_color == config['color_inicial']:
                        state.is_active = True
                    elif state.is_active and current_color == config['color_final']:
                        keyboard.press_and_release(config['accion'])
                        state.last_execution = current_time
                        state.is_active = False
                        
                        if config.get('copiar_al_telegram', False):
                            time.sleep(0.5)
                            self.send_clipboard()
                
                elif 'color_esperado' in config and current_color == config['color_esperado']:
                    if not state.is_active:
                        self.execute_script(config['ruta_script'], name)
                        state.last_execution = current_time
                        state.is_active = True
                else:
                    state.is_active = False

            time.sleep(0.05)

    def stop(self):
        self.running = False

class MonitoringSystem:
    def __init__(self):
        self.config = self.load_config()
        self.setup_logging()
        self.bot = self.setup_telegram()
        self.pixel_monitor = None
        self.clipboard_monitor = None
        self.running = True
        self.message_context = {}  # Dictionary to store context per chat_id
        openai.api_key = self.config["OPENAI_API_KEY"]
        
        # Create necessary directories
        for path in self.config['DIRECTORIOS'].values():
            os.makedirs(path, exist_ok=True)

        self.script_chains = {
            script_path: {
                'script': chain_config['script_encadenado'],
                'state': ScriptChainState()
            }
            for script_path, chain_config in self.config.get('SCRIPTS_ENCADENADOS', {}).items()
        }

    def load_config(self) -> dict:
        with open('config⚙️.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def setup_logging(self):
        log_dir = self.config['DIRECTORIO_LOGS']
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'sistema_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
        )

    def setup_telegram(self) -> telebot.TeleBot:
        bot = telebot.TeleBot(self.config["TELEGRAM_TOKEN"])
        
        @bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
        def handle_files(message):
            self.handle_file_message(message)
            
        for group_id in self.config["GRUPOS_MONITOREADOS"]:
            bot.message_handler(func=lambda m, gid=group_id: str(m.chat.id) == gid)(
                self.handle_telegram_message
            )
        
        return bot

    def get_context_messages(self, chat_id: int) -> List[dict]:
        if chat_id not in self.message_context:
            return []
        
        context = self.message_context[chat_id]
        return [
            {"role": "user", "content": context.original_message},
            {"role": "assistant", "content": context.command_response}
        ]

    def print_api_request(self, messages: List[dict], source: str):
        print("\n" + "="*50)
        print(f"API Request from: {source}")
        print("="*50)
        print("\nMessages sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content: {msg['content']}")
        print("\n" + "="*50 + "\n")

    def handle_clipboard_update(self, content: str):
        try:
            # Read the prompt
            with open(self.config["RUTA_PROMPT"], 'r', encoding='utf-8') as f:
                prompt = f.read().strip()

            # Get context from the last interaction
            chat_id = next(iter(self.config["GRUPOS_MONITOREADOS"]))
            context_messages = self.get_context_messages(int(chat_id))

            # Prepare messages with context
            messages = [{"role": "system", "content": prompt}]
            messages.extend(context_messages)
            messages.append({"role": "user", "content": content})

            # Print API request
            self.print_api_request(messages, "Clipboard Update")

            # Make API call
            response = openai.ChatCompletion.create(
                model=self.config.get("OPENAI_MODEL"),
                messages=messages
            )
            
            instruction = response.choices[0].message['content'].strip()
            
            # Handle the response
            if instruction == "RespuestaFinal":
                # Send to first monitored group
                self.bot.send_message(
                    chat_id,
                    f"📋 Clipboard content:\n\n{content}"
                )
                logging.info("Clipboard content sent to Telegram after OpenAI RespuestaFinal")
                return
            
            # Check for script execution
            script_path = (
                self.config["AHK_SCRIPTS"].get(instruction) or 
                self.config.get("PYTHON_SCRIPTS", {}).get(instruction)
            )
            
            if script_path:
                self.execute_script(script_path)
                logging.info(f"Executed script based on clipboard content: {instruction}")
            else:
                logging.warning(f"Unrecognized instruction from clipboard content: {instruction}")

        except Exception as e:
            logging.error(f"Error processing clipboard content: {e}")

    def handle_general_message(self, message):
        pyperclip.copy(message.text)
        
        try:
            with open(self.config["RUTA_PROMPT"], 'r', encoding='utf-8') as f:
                prompt = f.read().strip()

            # Get context from previous interactions
            context_messages = self.get_context_messages(message.chat.id)

            # Prepare messages with context
            messages = [{"role": "system", "content": prompt}]
            messages.extend(context_messages)
            messages.append({"role": "user", "content": message.text})

            # Print API request
            self.print_api_request(messages, "Telegram Message")

            response = openai.ChatCompletion.create(
                model=self.config.get("OPENAI_MODEL", "OPENAI_MODEL"),
                messages=messages
            )
            instruction = response.choices[0].message['content'].strip()
            
            # Store the context for future use
            self.message_context[message.chat.id] = MessageContext(
                original_message=message.text,
                command_response=instruction,
                timestamp=datetime.now()
            )
            
            # Check if the response is "RespuestaFinal"
            if instruction == "RespuestaFinal":
                clipboard_content = pyperclip.paste()
                if clipboard_content:
                    self.bot.reply_to(message, f"📋 Contenido del portapapeles:\n\n{clipboard_content}")
                    logging.info("Clipboard content sent to Telegram after OpenAI RespuestaFinal")
                else:
                    self.bot.reply_to(message, "❌ El portapapeles está vacío")
                return
            
            # Check both AHK and Python scripts
            script_path = (
                self.config["AHK_SCRIPTS"].get(instruction) or 
                self.config.get("PYTHON_SCRIPTS", {}).get(instruction)
            )
            
            if script_path:
                self.execute_script(script_path)
                self.bot.reply_to(message, f"Executed: {instruction}")
            else:
                self.bot.reply_to(message, "Instruction not recognized")
        except Exception as e:
            logging.error(f"API error: {e}")
            self.bot.reply_to(message, "Processing error occurred")

    def terminate_process(self, process):
        if process is None:
            return
        
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            gone, alive = psutil.wait_procs([parent] + parent.children(recursive=True), timeout=3)
            for p in alive:
                p.kill()
        except Exception as e:
            logging.error(f"Error terminating process: {e}")

    def execute_script(self, script_path: str, context: str = ""):
        try:
            # Determine script type and execute accordingly
            if script_path.endswith('.py'):
                process = subprocess.run(
                    [sys.executable, os.path.abspath(script_path)],
                    check=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # .ahk scripts
                process = subprocess.run(
                    [self.config['RUTA_AHK'], os.path.abspath(script_path)],
                    check=True
                )
            
            logging.info(f"Script executed: {script_path} {context}")

            if script_path in self.script_chains:
                chain_config = self.script_chains[script_path]
                chain_state = chain_config['state']
                chained_script = chain_config['script']

                if chain_state.is_running:
                    self.terminate_process(chain_state.process)
                    chain_state.process = None
                    chain_state.is_running = False
                    logging.info(f"Chained script stopped: {chained_script}")
                else:
                    is_python = chained_script.endswith('.py')
                    chain_state.process = subprocess.Popen(
                        [sys.executable if is_python else self.config['RUTA_AHK'],
                         os.path.abspath(chained_script)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    chain_state.is_running = True
                    logging.info(f"Chained script started: {chained_script}")

        except Exception as e:
            logging.error(f"Script execution error: {e}")

    def handle_file_message(self, message):
        try:
            file_obj = next((
                obj for obj in [
                    message.document,
                    message.photo[-1] if message.photo else None,
                    message.video,
                    message.audio
                ] if obj is not None
            ), None)
            
            if not file_obj:
                self.bot.reply_to(message, "❌ Unsupported file type")
                return
            
            file_info = self.bot.get_file(file_obj.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            file_name = getattr(file_obj, 'file_name', None) or (
                f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_info.file_path.split('.')[-1]}"
            )
            
            file_path = os.path.join(self.config['DIRECTORIOS']['descargas'], file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded_file)
            
            subprocess.Popen(
                [sys.executable, self.config['SCRIPTS']['database_loader']],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.bot.reply_to(message, f"✅ File saved and processing started:\n{file_name}")
            logging.info(f"File downloaded and processing: {file_path}")
            
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error processing file: {str(e)}")
            logging.error(f"File processing error: {e}")

    def handle_telegram_message(self, message):
        text = message.text.strip()
        
        handlers = {
            lambda t: t.split('\n')[0].strip() == "X": self.handle_twitter_message,
            lambda t: any(re.match(p, t) for p in self.config['PATRONES_URL']['youtube_video']): 
                self.handle_youtube_video,
            lambda t: any(re.match(p, t) for p in self.config['PATRONES_URL']['playlist']): 
                self.handle_playlist
        }

        for checker, handler in handlers.items():
            if checker(text):
                success = handler(text)
                response = "✅ Processed successfully!" if success else "❌ Processing failed"
                self.bot.reply_to(message, response)
                return

        self.handle_general_message(message)

    def handle_twitter_message(self, text: str) -> bool:
        try:
            lines = text.strip().split('\n')
            channel_name = lines[1].strip()
            tweet_content = '\n'.join(lines[2:]).strip()
            
            channel_dir = os.path.join(self.config['DIRECTORIOS']['twitter'], channel_name)
            os.makedirs(channel_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(channel_dir, f"tweet_{timestamp}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Canal: {channel_name}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Contenido: {tweet_content}\n")
            return True
        except Exception as e:
            logging.error(f"Error saving tweet: {e}")
            return False

    def handle_youtube_video(self, url: str) -> bool:
        try:
            pyperclip.copy(url)
            subprocess.Popen(
                [sys.executable, self.config['SCRIPTS']['transcription']], 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
        except Exception as e:
            logging.error(f"Error processing YouTube video: {e}")
            return False

    def handle_playlist(self, url: str) -> bool:
        try:
            pyperclip.copy(url)
            subprocess.Popen(
                [sys.executable, self.config['SCRIPTS']['playlist']], 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
        except Exception as e:
            logging.error(f"Error downloading playlist: {e}")
            return False

    def setup_hotkeys(self):
        for hotkey, script in self.config['TECLAS_RAPIDAS'].items():
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass
            keyboard.add_hotkey(hotkey, lambda p=script: self.execute_script(p))

    def run(self):
        self.setup_hotkeys()
        for script in self.config['SCRIPTS_AL_INICIO']:
            if script:  # Only execute non-empty script paths
                self.execute_script(script)

        self.pixel_monitor = PixelMonitor(
            self.config,
            self.execute_script,
            lambda: self.bot.send_message(
                next(iter(self.config["GRUPOS_MONITOREADOS"])),
                f"Clipboard content:\n\n{pyperclip.paste()}"
            )
        )

        # Initialize and start clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(self.handle_clipboard_update)
        
        # Start monitoring threads
        monitor_thread = threading.Thread(target=self.pixel_monitor.monitor, daemon=True)
        clipboard_thread = threading.Thread(target=self.clipboard_monitor.monitor, daemon=True)
        
        monitor_thread.start()
        clipboard_thread.start()

        try:
            logging.info("System started with clipboard monitoring")
            self.bot.polling(none_stop=True)
        except KeyboardInterrupt:
            self.running = False
            self.pixel_monitor.stop()
            self.clipboard_monitor.stop()
            for chain_config in self.script_chains.values():
                if chain_config['state'].is_running:
                    self.terminate_process(chain_config['state'].process)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if self.bot:
                self.bot.stop_polling()

if __name__ == '__main__':
    try:
        MonitoringSystem().run()
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        raise