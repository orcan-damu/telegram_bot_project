import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import speech_recognition as sr
from pydub import AudioSegment

# Global variables
transcriptions = {}  # Stores transcriptions with user-specific data

async def handle_voice(update: Update, context):
    user_id = update.message.from_user.id  # Get the user's unique ID

    # Create a user-specific folder if it doesn't exist
    user_folder = os.path.join("voice_data", f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)

    # Get current date and time
    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y")

    # Generate a unique folder name for this transcription
    transcription_id = f"{len(transcriptions.get(user_id, {})) + 1}"
    folder_name = f"{date_time}_{transcription_id}"
    folder_path = os.path.join(user_folder, folder_name)
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

    # Save the initial transcribed text as version 1
    version = 1
    text_path = os.path.join(folder_path, f"transcription_v{version}.txt")
    with open(text_path, "w", encoding="utf-8") as text_file:
        text_file.write(text)

    # Store transcription in the global dictionary
    if user_id not in transcriptions:
        transcriptions[user_id] = {}
    transcriptions[user_id][transcription_id] = {
        "folder_name": folder_name,
        "text": text,
        "text_path": text_path,
        "version": version
    }

    # Send the transcribed text back to the user with an inline keyboard
    keyboard = [
        [InlineKeyboardButton("Edit Transcription", callback_data=f"edit_{user_id}_{transcription_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Folder: {folder_name}\n\nTranscribed Text (v{version}):\n{text}",
        reply_markup=reply_markup
    )

async def start(update: Update, context):
    await update.message.reply_text("Hey Orcan,\n\nSend me a voice message, and I'll transcribe it for you!")

async def handle_button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Extract the action, user_id, and transcription_id from the callback data
    try:
        action, user_id, transcription_id = query.data.split("_", 2)
        user_id = int(user_id)  # Convert user_id to integer
    except ValueError:
        await query.edit_message_text("Invalid button action. Please try again.")
        return

    # Get the user's transcriptions
    user_transcriptions = transcriptions.get(user_id, {})
    transcription = user_transcriptions.get(transcription_id)

    if action == "edit":
        if transcription:
            # Ask the user to send the edited text
            await query.edit_message_text(
                f"Current Transcription (v{transcription['version']}):\n{transcription['text']}\n\nPlease reply with the edited text."
            )
            # Store the user_id and transcription_id in the user's context for later use
            context.user_data["editing_user_id"] = user_id
            context.user_data["editing_transcription_id"] = transcription_id
        else:
            await query.edit_message_text("Transcription not found. Please try again.")

async def handle_text(update: Update, context):
    # Check if the user is editing a transcription
    if "editing_user_id" in context.user_data and "editing_transcription_id" in context.user_data:
        user_id = context.user_data["editing_user_id"]
        transcription_id = context.user_data["editing_transcription_id"]

        # Get the user's transcriptions
        user_transcriptions = transcriptions.get(user_id, {})
        transcription = user_transcriptions.get(transcription_id)

        if transcription:
            # Get the edited text
            edited_text = update.message.text

            # Increment the version number
            new_version = transcription["version"] + 1

            # Save the new version of the transcript
            folder_path = os.path.dirname(transcription["text_path"])
            new_text_path = os.path.join(folder_path, f"transcription_v{new_version}.txt")
            with open(new_text_path, "w", encoding="utf-8") as text_file:
                text_file.write(edited_text)

            # Update the transcription in the global dictionary
            transcription["text"] = edited_text
            transcription["text_path"] = new_text_path
            transcription["version"] = new_version

            # Notify the user with the new version number
            await update.message.reply_text(
                f"Transcription updated successfully! (v{new_version})\n\nNew Text:\n{edited_text}"
            )

            # Clear the editing state
            del context.user_data["editing_user_id"]
            del context.user_data["editing_transcription_id"]
    else:
        await update.message.reply_text("Send me a voice message to transcribe it!")