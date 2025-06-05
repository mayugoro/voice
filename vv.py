import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
import subprocess  # Menambahkan untuk mengonversi video dengan ffmpeg

BOT_TOKEN = "TOKEN_KAMU"

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirimkan file audio atau video untuk saya konversi.")

# Fungsi untuk mengonversi file menjadi voice chat
async def convert_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None
    ext = None

    # Cek jenis file (audio, voice, document, atau video)
    if update.message.audio:
        file = await update.message.audio.get_file()
        ext = "mp3"
    elif update.message.voice:
        file = await update.message.voice.get_file()
        ext = "ogg"
    elif update.message.document:
        file = await update.message.document.get_file()
        ext = update.message.document.file_name.split(".")[-1].lower()
    elif update.message.video:
        # Proses untuk video
        await update.message.reply_text("Mohon tunggu... Proses konversi video ke audio sedang berjalan.")
        file = await update.message.video.get_file()
        ext = "mp4"
    else:
        await update.message.reply_text("Kirim file audio atau video ya.")
        return

    input_path = f"{file.file_id}.{ext}"
    output_path = f"{file.file_id}.ogg"

    # Download file
    await file.download_to_drive(input_path)

    try:
        # Jika video, konversi ke audio dengan ffmpeg
        if ext == "mp4":
            audio_path = f"{file.file_id}.mp3"
            # Mengonversi video ke audio menggunakan ffmpeg
            subprocess.run(['ffmpeg', '-i', input_path, audio_path])
            input_path = audio_path  # Ganti input_path dengan file audio yang dihasilkan

        # Konversi file audio (mp3 atau ogg) menjadi ogg format untuk voice chat
        audio = AudioSegment.from_file(input_path)

        # Peningkatan kualitas suara
        audio = audio.set_frame_rate(48000).set_channels(2)
        audio = audio.normalize()

        # Ekspor ke ogg dengan bitrate tinggi
        audio.export(output_path, format="ogg", codec="libopus", bitrate="128k")

        # Mengirimkan file voice chat ke pengguna
        with open(output_path, "rb") as voice:
            await update.message.reply_voice(voice=voice)

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan saat konversi: {e}")

    finally:
        # Menghapus file sementara setelah proses selesai
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Fungsi utama untuk memulai bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL | filters.VIDEO, convert_to_voice))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()