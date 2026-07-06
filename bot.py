"""
Language70 Translator Bot
A Telegram bot that translates text and voice messages into 70+ languages
Deployed on Railway with GitHub integration
"""

import os
import logging
import tempfile
import asyncio
from typing import Dict, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from googletrans import Translator, LANGUAGES
import speech_recognition as sr
from pydub import AudioSegment

# ============================================
# CONFIGURATION
# ============================================

# Environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN environment variable is not set!")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize translator
translator = Translator()

# User language preferences (in-memory cache)
# For production, replace with Redis or database
user_languages: Dict[int, str] = {}

# Language mapping (70+ languages)
LANGUAGE_MAP = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "chinese": "zh-cn",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "bengali": "bn",
    "urdu": "ur",
    "turkish": "tr",
    "dutch": "nl",
    "greek": "el",
    "hebrew": "he",
    "polish": "pl",
    "swedish": "sv",
    "norwegian": "no",
    "danish": "da",
    "finnish": "fi",
    "indonesian": "id",
    "malay": "ms",
    "thai": "th",
    "vietnamese": "vi",
    "tagalog": "tl",
    "persian": "fa",
    "ukrainian": "uk",
    "czech": "cs",
    "hungarian": "hu",
    "romanian": "ro",
    "bulgarian": "bg",
    "croatian": "hr",
    "slovak": "sk",
    "slovenian": "sl",
    "lithuanian": "lt",
    "latvian": "lv",
    "estonian": "et",
    "icelandic": "is",
    "albanian": "sq",
    "serbian": "sr",
    "macedonian": "mk",
    "georgian": "ka",
    "armenian": "hy",
    "azerbaijani": "az",
    "kazakh": "kk",
    "uzbek": "uz",
    "mongolian": "mn",
    "nepali": "ne",
    "sinhala": "si",
    "khmer": "km",
    "lao": "lo",
    "burmese": "my",
    "amharic": "am",
    "swahili": "sw",
    "zulu": "zu",
    "hausa": "ha",
    "yoruba": "yo",
    "igbo": "ig",
    "tamil": "ta",
    "telugu": "te",
    "marathi": "mr",
    "gujarati": "gu",
    "kannada": "kn",
    "malayalam": "ml",
    "punjabi": "pa",
    "sanskrit": "sa",
    "somali": "so",
    "kurdish": "ku",
    "pashto": "ps",
    "dari": "prs",
    "tajik": "tg",
    "kyrgyz": "ky",
    "turkmen": "tk",
    "maltese": "mt",
    "irish": "ga",
    "scottish": "gd",
    "welsh": "cy",
    "basque": "eu",
    "catalan": "ca",
    "galician": "gl",
    "latin": "la",
    "esperanto": "eo",
}

# Reverse mapping
LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_MAP.items()}

# Popular languages for quick selection
POPULAR_LANGUAGES = [
    "english", "spanish", "french", "german", 
    "chinese", "japanese", "arabic", "russian", 
    "hindi", "portuguese", "italian", "korean"
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_user_language(user_id: int) -> str:
    """Get user's preferred language, default to English."""
    return user_languages.get(user_id, "english")

def set_user_language(user_id: int, language: str) -> None:
    """Set user's preferred language."""
    if language in LANGUAGE_MAP:
        user_languages[user_id] = language
        logger.info(f"User {user_id} set language to {language}")

def get_language_code(language_name: str) -> str:
    """Get language code from language name."""
    return LANGUAGE_MAP.get(language_name.lower(), "en")

def get_language_name(code: str) -> str:
    """Get language name from language code."""
    return LANGUAGE_NAMES.get(code, code)

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    welcome_message = f"""
👋 *Welcome to Language70 Translator, {user.first_name}!*

I'm your multilingual translation assistant that supports *70+ languages*.

📝 *How to use me:*
• Send any *text message* → I'll translate it
• Send a *voice message* → I'll transcribe & translate it
• Reply to any message with `/tl` → Quick translation

⚙️ *Commands:*
/setlang - Choose your target language
/langlist - See all 70+ languages
/about - About this bot
/help - Show this help message

💡 *Default language is English.* Use /setlang to change it.

🔗 *Source Code:* [GitHub](https://github.com/yourusername/language70translator)
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown", disable_web_page_preview=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📖 *Help Guide - Language70 Translator*

🎯 *Translation Features:*

1️⃣ *Text Translation*
   Just send any text message and I'll translate it to your target language.

2️⃣ *Voice Translation*
   Send a voice message and I'll:
   • Transcribe what you said
   • Translate it to your target language
   • Send you the result

3️⃣ *Reply Translation*
   Reply to any message with `/tl` to translate it instantly.

🌍 *Supported Languages: 70+*
   Use /langlist to see all available languages.

⚙️ *Commands:*
/start - Welcome message
/help - This help menu
/setlang - Change target language
/langlist - List all languages
/about - Bot information
/tl - Translate replied message

🔧 *Tips:*
• Voice messages work best in quiet environments
• Clear speech gives better transcription accuracy
• You can change your target language anytime

📱 *Need help?* Contact @yourusername
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command."""
    about_text = """
🤖 *Language70 Translator Bot*

🌍 *Version:* 2.0.0
📅 *Released:* 2024
🎯 *Languages:* 70+

✨ *Features:*
• Real-time text translation
• Voice message transcription
• 70+ language support
• User language preferences
• Reply translation support
• Inline keyboard interface

🛠️ *Technology Stack:*
• Python 3.11
• python-telegram-bot 20.7
• Google Translate API
• Google Speech Recognition
• Railway Deployment
• GitHub Version Control

👨‍💻 *Developer:* @yourusername
📌 *Bot:* @language70translator
🔗 *Source:* [GitHub Repository](https://github.com/yourusername/language70translator)

📊 *Stats:*
• Deployed: Railway
• Uptime: 24/7
• Free to use

Made with ❤️ for the Telegram community
"""
    await update.message.reply_text(about_text, parse_mode="Markdown", disable_web_page_preview=True)

async def langlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /langlist command - show all languages."""
    # Group languages alphabetically
    languages = sorted(LANGUAGE_MAP.keys())
    
    # Create formatted list with pagination
    chunks = [languages[i:i+25] for i in range(0, len(languages), 25)]
    
    message = "🌍 *All Supported Languages (70+)*\n\n"
    for chunk in chunks[0]:  # Show first 25
        message += f"• {chunk.capitalize()}\n"
    
    if len(chunks) > 1:
        message += f"\n_+{sum(len(chunk) for chunk in chunks[1:])} more languages available_"
        message += "\n\n💡 Use /setlang to choose your target language interactively."
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def setlang_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setlang command - show language selection menu."""
    keyboard = []
    
    # Add popular languages in rows of 2
    row = []
    for i, lang in enumerate(POPULAR_LANGUAGES):
        display_name = lang.capitalize()
        row.append(InlineKeyboardButton(display_name, callback_data=f"lang_{lang}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Add "View All" button
    keyboard.append([InlineKeyboardButton("📋 View All Languages", callback_data="view_all_langs")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_lang = get_user_language(update.effective_user.id)
    message = f"""
🌍 *Select Your Target Language*

Current language: *{current_lang.capitalize()}*

Choose from popular languages below or click "View All Languages" to see the complete list.
"""
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def view_all_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all languages in a scrollable format."""
    query = update.callback_query
    await query.answer()
    
    # Create language list with callback data
    languages = sorted(LANGUAGE_MAP.keys())
    keyboard = []
    
    for lang in languages[:50]:  # Limit to 50 to avoid message size limits
        keyboard.append([InlineKeyboardButton(
            lang.capitalize(), 
            callback_data=f"lang_{lang}"
        )])
    
    # Add "Go Back" button
    keyboard.append([InlineKeyboardButton("🔙 Go Back", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🌍 *Select Your Target Language*\n\nChoose from the list below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action = query.data
    
    if action == "view_all_langs":
        await view_all_languages(update, context)
        return
    
    if action == "back_to_main":
        await setlang_command(update, context)
        return
    
    if action.startswith("lang_"):
        language = action.replace("lang_", "")
        if language in LANGUAGE_MAP:
            set_user_language(user_id, language)
            await query.edit_message_text(
                f"✅ *Language Updated!*\n\nYour target language is now: *{language.capitalize()}*\n\nSend me any text or voice message to translate!",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Invalid language selected. Please try again.")

# ============================================
# TRANSLATION HANDLERS
# ============================================

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text translation."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        return
    
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        # Detect source language
        detection = translator.detect(text)
        source_lang = detection.lang
        source_name = get_language_name(source_lang)
        
        # Translate
        translated = translator.translate(text, dest=target_code)
        
        response = f"""
🔄 *Translation*

📤 *Original:*
{text}

📥 *Translated to {target_lang.capitalize()}:*
{translated.text}

📊 *Detected Source:* {source_name.capitalize()}
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again or try a different text.")

async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice message translation."""
    user_id = update.effective_user.id
    voice = update.message.voice
    
    if not voice:
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🎵 *Processing voice message...*\n\nThis may take a few seconds.", parse_mode="Markdown")
    
    try:
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        
        # Create temp files
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
            await file.download_to_drive(ogg_file.name)
            ogg_path = ogg_file.name
        
        # Convert OGG to WAV for speech recognition
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            audio = AudioSegment.from_ogg(ogg_path)
            audio.export(wav_file.name, format="wav")
            wav_path = wav_file.name
        
        # Transcribe using Google Speech Recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        # Perform transcription
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            # Try with language detection if English fails
            try:
                # You can specify language here if needed
                text = recognizer.recognize_google(audio_data, language="en-US")
            except:
                raise sr.UnknownValueError()
        
        # Clean up temp files
        os.unlink(ogg_path)
        os.unlink(wav_path)
        
        # Translate the transcribed text
        target_lang = get_user_language(user_id)
        target_code = get_language_code(target_lang)
        
        translated = translator.translate(text, dest=target_code)
        
        response = f"""
🎙️ *Voice Translation*

🔊 *Transcribed Text:*
{text}

🌍 *Translated to {target_lang.capitalize()}:*
{translated.text}
"""
        await processing_msg.edit_text(response, parse_mode="Markdown")
        
    except sr.UnknownValueError:
        await processing_msg.edit_text("❌ Could not understand the voice message. Please ensure you speak clearly and try again.")
    except sr.RequestError:
        await processing_msg.edit_text("❌ Speech recognition service is unavailable. Please try again later or send text instead.")
    except Exception as e:
        logger.error(f"Voice translation error: {e}")
        await processing_msg.edit_text("❌ Voice processing failed. Please try again or send text instead.")

async def inline_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tl command - translate replied message."""
    user_id = update.effective_user.id
    
    if not update.message.reply_to_message:
        await update.message.reply_text("ℹ️ Reply to a message with /tl to translate it.")
        return
    
    text = update.message.reply_to_message.text
    if not text:
        await update.message.reply_text("❌ The replied message has no text to translate.")
        return
    
    target_lang = get_user_language(user_id)
    target_code = get_language_code(target_lang)
    
    try:
        translated = translator.translate(text, dest=target_code)
        
        response = f"""
🔄 *Translated to {target_lang.capitalize()}:*
{translated.text}
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Inline translation error: {e}")
        await update.message.reply_text("❌ Translation failed. Please try again.")

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# ============================================
# MAIN APPLICATION
# ============================================

def main() -> None:
    """Start the bot application."""
    logger.info("🚀 Starting Language70 Translator Bot...")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("langlist", langlist_command))
    application.add_handler(CommandHandler("setlang", setlang_command))
    application.add_handler(CommandHandler("tl", inline_translate))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^(lang_|view_all_langs|back_to_main)"))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    application.add_handler(MessageHandler(filters.VOICE, translate_voice))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("✅ Bot is running. Press Ctrl+C to stop.")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
