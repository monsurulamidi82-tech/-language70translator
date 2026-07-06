"""
Language70 Translator Bot
A Telegram bot that translates text and voice messages into 70+ languages
Deployed on Railway with GitHub integration
"""

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
import subprocess

# ============================================
# CONFIGURATION
# ============================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN environment variable is not set!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()
user_languages: Dict[int, str] = {}

# 70+ Language Mapping
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
    "gujarati": "gu", "kannada": "kn", "malayalam": "ml", "punjabi": "pa",
    "sanskrit": "sa", "somali": "so", "kurdish": "ku", "pashto": "ps",
    "dari": "prs", "tajik": "tg", "kyrgyz": "ky", "turkmen": "tk",
    "maltese": "mt", "irish": "ga", "scottish": "gd", "welsh": "cy",
    "basque": "eu", "catalan": "ca", "galician": "gl", "latin": "la",
    "esperanto": "eo"
}

POPULAR_LANGUAGES = [
    "english", "spanish", "french", "german", 
    "chinese", "japanese", "arabic", "russian", 
    "hindi", "portuguese", "italian", "korean"
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_user_language(user_id: int) -> str:
    return user_languages.get(user_id, "english")

def set_user_language(user_id: int, language: str) -> None:
    if language in LANGUAGE_MAP:
        user_languages[user_id] = language
        logger.info(f"User {user_id} set language to {language}")

def get_language_code(language_name: str) -> str:
    return LANGUAGE_MAP.get(language_name.lower(), "en")

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = f"""
👋 *Welcome to Language70 Translator, {user.first_name}!*

I can translate text and voice messages into *70+ languages*.

📝 *Commands:*
/start - Welcome message
/help - Help menu
/setlang - Choose target language
/langlist - See all 70+ languages
/about - About this bot
/tl - Translate replied message

💡 *Default language is English.*
Send any text or voice message to translate!
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📖 *Help Guide*

• Send any *text message* → Auto-translate
• Send a *voice message* → Transcribe & translate
• Reply with `/tl` → Translate replied message

⚙️ *Commands:*
/setlang - Change target language
/langlist - List all languages
/about - Bot info
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    about_text = """
🤖 *Language70 Translator Bot*

🌍 *Version:* 2.0.0
🎯 *Languages:* 70+

✨ *Features:*
• Real-time text translation
• Voice message transcription
• User language preferences
• Reply translation support

🛠️ *Built with:*
• Python 3.11
• Google Translate API
• Speech Recognition
• Railway

📌 *Bot:* @language70translator
"""
    await update.message.reply_text(about_text, parse_mode="Markdown")

async def langlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    languages = sorted(LANGUAGE_MAP.keys())
    chunks = [languages[i:i+25] for i in range(0, len(languages), 25)]
    
    message = "🌍 *All Supported Languages (70+)*\n\n"
    for lang in chunks[0]:
        message += f"• {lang.capitalize()}\n"
    
    if len(chunks) > 1:
        message += f"\n_+{sum(len(chunk) for chunk in chunks[1:])} more languages_"
    
    await update.message.reply_text(message, parse_mode="Markdown")

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
    
    keyboard.append([InlineKeyboardButton("📋 View All Languages", callback_data="view_all")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current = get_user_language(update.effective_user.id)
    await update.message.reply_text(
        f"🌍 Current language: *{current.capitalize()}*\n\nSelect your target language:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action = query.data
    
    if action == "view_all":
        languages = sorted(LANGUAGE_MAP.keys())
        keyboard = []
        for lang in languages[:50]:
            keyboard.append([InlineKeyboardButton(lang.capitalize(), callback_data=f"lang_{lang}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        await query.edit_message_text(
            "🌍 *Select Your Target Language:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    if action == "back":
        await setlang_command(update, context)
        return
    
    if action.startswith("lang_"):
        language = action.replace("lang_", "")
        if language in LANGUAGE_MAP:
            set_user_language(user_id, language)
            await query.edit_message_text(
                f"✅ *Language set to:* {language.capitalize()}\n\nSend me any text or voice message to translate!",
                parse_mode="Markdown"
            )

async def inline_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("ℹ️ Reply to a message with /tl")
        return
    
    text = update.message.reply_to_message.text
    if not text:
        await update.message.reply_text("❌ No text to translate")
        return
    
    user_id = update.effective_user.id
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        translated = translator.translate(text, dest=target_code)
        await update.message.reply_text(
            f"🔄 *Translated to {target_lang.capitalize()}:*\n{translated.text}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Inline translation error: {e}")
        await update.message.reply_text("❌ Translation failed")

# ============================================
# TRANSLATION HANDLERS
# ============================================

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        return
    
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        detection = translator.detect(text)
        source_lang = detection.lang
        
        translated = translator.translate(text, dest=target_code)
        
        response = f"""
🔄 *Translation*

📤 *Original:*
{text}

📥 *Translated to {target_lang.capitalize()}:*
{translated.text}
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")

async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    voice = update.message.voice
    
    if not voice:
        return
    
    processing_msg = await update.message.reply_text("🎵 Processing voice message...")
    
    try:
        file = await context.bot.get_file(voice.file_id)
        
        # Download as OGG
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
            await file.download_to_drive(ogg_file.name)
            ogg_path = ogg_file.name
        
        # Convert OGG to WAV using pydub
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            try:
                audio = AudioSegment.from_ogg(ogg_path)
                audio.export(wav_file.name, format="wav")
                wav_path = wav_file.name
            except Exception as e:
                logger.error(f"Audio conversion error: {e}")
                await processing_msg.edit_text("❌ Could not process voice file. Please try again.")
                os.unlink(ogg_path)
                return
        
        # Transcribe using SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            await processing_msg.edit_text("❌ Could not understand the voice message. Please speak clearly and try again.")
            os.unlink(ogg_path)
            os.unlink(wav_path)
            return
        except sr.RequestError:
            await processing_msg.edit_text("❌ Speech recognition service unavailable. Please try again later.")
            os.unlink(ogg_path)
            os.unlink(wav_path)
            return
        
        # Clean up temp files
        os.unlink(ogg_path)
        os.unlink(wav_path)
        
        # Translate the transcribed text
        target_lang = get_user_language(user_id)
        target_code = get_language_code(target_lang)
        
        translated = translator.translate(text, dest=target_code)
        
        response = f"""
🎙️ *Voice Translation*

🔊 *Transcribed:*
{text}

🌍 *Translated to {target_lang.capitalize()}:*
{translated.text}
"""
        await processing_msg.edit_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Voice translation error: {e}")
        await processing_msg.edit_text("❌ Voice processing failed. Please try again or send text instead.")

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ An error occurred. Please try again.")
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# ============================================
# MAIN APPLICATION
# ============================================

def main() -> None:
    logger.info("🚀 Starting Language70 Translator Bot...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("langlist", langlist_command))
    application.add_handler(CommandHandler("setlang", setlang_command))
    application.add_handler(CommandHandler("tl", inline_translate))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^(lang_|view_all|back)"))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    application.add_handler(MessageHandler(filters.VOICE, translate_voice))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ Bot is running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
