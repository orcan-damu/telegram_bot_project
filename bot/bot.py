import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import speech_recognition as sr
from pydub import AudioSegment

# Global variables
serial_number = 0
transcriptions = {}  # Stores transcriptions with unique IDs

async def handle_voice(update: Update, context):
    global serial_number

    # Get current date and time
    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y")

    # Increment serial number for each new folder
    serial_number += 1

    # Generate folder name in the format {date : time : serial number}
    folder_name = f"{date_time}_{serial_number}"
    folder_path = os.path.join("voice_data", folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Download the voice message
    voice_file = await update.message.voice.get_file()
    audio_path = os.path.join(folder_path, "audio.ogg")
    await voice_file.download_to_drive(audio_path)

    # Convert OGG to WAV using pydub
    wav_path = os.path.join(folder_path, "audio.wav")
    audio = AudioSegment.from_file(audio_path, format="ogg")
    audio.export(wav_path, format="wav")

    # Transcribe the audio to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            # Try English first
            text = recognizer.recognize_google(audio_data, language="en-IN")
        except sr.UnknownValueError:
            try:
                # If English fails, try Tamil
                text = recognizer.recognize_google(audio_data, language="ta-IN")
            except sr.UnknownValueError:
                text = "Sorry, I could not understand the audio."

    # Save the transcribed text
    text_path = os.path.join(folder_path, "transcription.txt")
    with open(text_path, "w", encoding="utf-8") as text_file:  # Use UTF-8 encoding
        text_file.write(text)

    # Store transcription in the global dictionary
    transcription_id = f"trans_{serial_number}"
    transcriptions[transcription_id] = {
        "folder_name": folder_name,
        "text": text,
        "text_path": text_path
    }

    # Send the transcribed text back to the user with an inline keyboard
    keyboard = [
        [InlineKeyboardButton("Edit Transcription", callback_data=f"edit_{transcription_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Folder: {folder_name}\n\nTranscribed Text:\n{text}",
        reply_markup=reply_markup
    )

async def start(update: Update, context):
    await update.message.reply_text("Send me a voice message, and I'll transcribe it for you!")

async def handle_button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Extract the action and transcription_id from the callback data
    # Split on the first underscore only
    try:
        action, transcription_id = query.data.split("_", 1)
    except ValueError:
        await query.edit_message_text("Invalid button action. Please try again.")
        return

    transcription = transcriptions.get(transcription_id)

    if action == "edit":
        if transcription:
            # Ask the user to send the edited text
            await query.edit_message_text(
                f"Current Transcription:\n{transcription['text']}\n\nPlease reply with the edited text."
            )
            # Store the transcription ID in the user's context for later use
            context.user_data["editing_transcription_id"] = transcription_id
        else:
            await query.edit_message_text("Transcription not found. Please try again.")

async def handle_text(update: Update, context):
    # Check if the user is editing a transcription
    if "editing_transcription_id" in context.user_data:
        transcription_id = context.user_data["editing_transcription_id"]
        transcription = transcriptions.get(transcription_id)

        if transcription:
            # Save the edited text
            edited_text = update.message.text
            transcription["text"] = edited_text
            with open(transcription["text_path"], "w", encoding="utf-8") as text_file:
                text_file.write(edited_text)

            # Notify the user
            await update.message.reply_text("Transcription updated successfully!")
            # Clear the editing state
            del context.user_data["editing_transcription_id"]
    else:
        await update.message.reply_text("Send me a voice message to transcribe it!")