import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video and I'll add watermark!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    file = await video.get_file()
    await update.message.reply_text("Downloading...")

    input_path = "input.mp4"
    output_path = "output.mp4"

    await file.download_to_drive(input_path)

    clip = VideoFileClip(input_path)
    txt = TextClip("Join @skillwithgaurav", fontsize=40, color='white', font='Poppins-Bold')
    txt = txt.set_pos(("center", "bottom")).set_duration(clip.duration)

    final = CompositeVideoClip([clip, txt])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    await update.message.reply_video(video=open(output_path, 'rb'))

    os.remove(input_path)
    os.remove(output_path)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

app.run_polling()
