import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Reemplaza 'TU_TOKEN' con el token de tu bot
TOKEN = 'TELEGRAM_TOKEN'
# Diccionario para almacenar información de los grupos
group_info = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bot iniciado. La información del grupo se mostrará en la consola del servidor.')

async def log_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message

    if chat.type in ['group', 'supergroup']:
        group_info[chat.id] = {
            'id': chat.id,
            'name': chat.title,
            'type': chat.type
        }
        
        print(f"\n--- Información del Grupo ---")
        print(f"ID del grupo: {chat.id}")
        print(f"Nombre del grupo: {chat.title}")
        print(f"Tipo de chat: {chat.type}")
        print(f"Mensaje enviado por: {message.from_user.first_name} (ID: {message.from_user.id})")
        print("-----------------------------\n")
    else:
        print("Mensaje recibido fuera de un grupo")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_group_info))
    
    print("Bot iniciado. Esperando mensajes...")
    application.run_polling()

if __name__ == '__main__':
    main()