import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import speech_recognition as sr
from pydub import AudioSegment

# Global variable to keep track of the serial number
serial_number = 0

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

    # Send the transcribed text back to the user
    response = f"Folder: {folder_name}\n\nTranscribed Text:\n{text}"
    await update.message.reply_text(response)

async def start(update: Update, context):
    await update.message.reply_text("Send me a voice message, and I'll transcribe it for you!")