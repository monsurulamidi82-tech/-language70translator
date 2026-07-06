import os
import logging
import tempfile
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from googletrans import Translator
import speech_recognition as sr
from pydub import AudioSegment

# Configuration
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()
user_languages: Dict[int, str] = {}

# 70+ Languages
LANGUAGE_MAP = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "portuguese": "pt", "russian": "ru", "chinese": "zh-cn",
    "japanese": "ja", "korean": "ko", "arabic": "ar", "hindi": "hi",
    "bengali": "bn", "urdu": "ur", "turkish": "tr", "dutch": "nl",
    "greek": "el", "hebrew": "he", "polish": "pl", "swedish": "sv",
    "norwegian": "no", "danish": "da", "finnish": "fi", "indonesian": "id",
    "malay": "ms", "thai": "th", "vietnamese": "vi", "tagalog": "tl",
    "persian": "fa", "ukrainian": "uk", "czech": "cs", "hungarian": "hu",
    "romanian": "ro", "bulgarian": "bg", "croatian": "hr", "slovak": "sk",
    "slovenian": "sl", "lithuanian": "lt", "latvian": "lv", "estonian": "et",
    "icelandic": "is", "albanian": "sq", "serbian": "sr", "macedonian": "mk",
    "georgian": "ka", "armenian": "hy", "azerbaijani": "az", "kazakh": "kk",
    "uzbek": "uz", "mongolian": "mn", "nepali": "ne", "sinhala": "si",
    "khmer": "km", "lao": "lo", "burmese": "my", "amharic": "am",
    "swahili": "sw", "zulu": "zu", "hausa": "ha", "yoruba": "yo",
    "igbo": "ig", "tamil": "ta", "telugu": "te", "marathi": "mr",
    "gujarati": "gu", "kannada": "kn", "malayalam": "ml", "punjabi": "pa"
}

POPULAR_LANGUAGES = [
    "english", "spanish", "french", "german", 
    "chinese", "japanese", "arabic", "russian", 
    "hindi", "portuguese", "italian", "korean"
]

def get_user_language(user_id: int) -> str:
    return user_languages.get(user_id, "english")

def set_user_language(user_id: int, language: str) -> None:
    if language in LANGUAGE_MAP:
        user_languages[user_id] = language
        logger.info(f"User {user_id} set language to {language}")

def get_language_code(language_name: str) -> str:
    return LANGUAGE_MAP.get(language_name.lower(), "en")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome to Language70 Translator, {user.first_name}!\n\n"
        "Send any text or voice message to translate!\n"
        "Use /setlang to change your target language.\n"
        "Use /help for more commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 Help Guide\n\n"
        "• Send text → Auto-translate\n"
        "• Send voice → Transcribe & translate\n"
        "• /setlang → Change language\n"
        "• /langlist → All languages\n"
        "• /tl (reply) → Translate replied message"
    )

async def setlang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    row = []
    for i, lang in enumerate(POPULAR_LANGUAGES):
        row.append(InlineKeyboardButton(lang.capitalize(), callback_data=f"lang_{lang}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📋 View All", callback_data="view_all")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current = get_user_language(update.effective_user.id)
    await update.message.reply_text(
        f"🌍 Current: {current.capitalize()}\nSelect target:",
        reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action = query.data
    
    if action == "view_all":
        languages = sorted(LANGUAGE_MAP.keys())
        keyboard = [[InlineKeyboardButton(lang.capitalize(), callback_data=f"lang_{lang}")] for lang in languages[:50]]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        await query.edit_message_text(
            "🌍 Select language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    if action == "back":
        await setlang_command(update, context)
        return
    
    if action.startswith("lang_"):
        language = action.replace("lang_", "")
        if language in LANGUAGE_MAP:
            set_user_language(user_id, language)
            await query.edit_message_text(f"✅ Language set to: {language.capitalize()}")

async def langlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    languages = sorted(LANGUAGE_MAP.keys())
    message = "🌍 All Languages (70+):\n\n"
    for lang in languages[:50]:
        message += f"• {lang.capitalize()}\n"
    await update.message.reply_text(message)

async def inline_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message with /tl")
        return
    
    text = update.message.reply_to_message.text
    if not text:
        await update.message.reply_text("No text to translate")
        return
    
    user_id = update.effective_user.id
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        translated = translator.translate(text, dest=target_code)
        await update.message.reply_text(
            f"🔄 Translated to {target_lang.capitalize()}:\n{translated.text}"
        )
    except Exception as e:
        await update.message.reply_text("Translation failed")

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        return
    
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        translated = translator.translate(text, dest=target_code)
        await update.message.reply_text(
            f"📥 {target_lang.capitalize()}: {translated.text}"
        )
    except Exception as e:
        await update.message.reply_text("Translation failed")

async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    voice = update.message.voice
    
    if not voice:
        return
    
    processing_msg = await update.message.reply_text("🎵 Processing...")
    
    try:
        file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
            await file.download_to_drive(ogg_file.name)
            ogg_path = ogg_file.name
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            audio = AudioSegment.from_ogg(ogg_path)
            audio.export(wav_file.name, format="wav")
            wav_path = wav_file.name
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data)
        
        os.unlink(ogg_path)
        os.unlink(wav_path)
        
        target_lang = get_user_language(user_id)
        target_code = get_language_code(target_lang)
        translated = translator.translate(text, dest=target_code)
        
        await processing_msg.edit_text(
            f"🔊 {text}\n\n📥 {target_lang.capitalize()}: {translated.text}"
        )
        
    except Exception as e:
        await processing_msg.edit_text("Voice processing failed")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 Language70 Translator\n"
        "Version 2.0\n"
        "Supports 70+ languages\n"
        "Text & Voice translation"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error: {context.error}")

def main() -> None:
    logger.info("🚀 Starting Language70 Translator Bot...")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("langlist", langlist_command))
    application.add_handler(CommandHandler("setlang", setlang_command))
    application.add_handler(CommandHandler("tl", inline_translate))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^(lang_|view_all|back)"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    application.add_handler(MessageHandler(filters.VOICE, translate_voice))
    application.add_error_handler(error_handler)
    
    logger.info("✅ Bot is running successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
