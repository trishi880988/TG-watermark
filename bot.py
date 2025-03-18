import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import ChatAction
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("watermark_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.video & filters.private)
async def watermark(client, message):
    start_time = time.time()
    
    await message.reply_text("⬇️ Downloading video...")
    await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)

    # Download video
    download_start = time.time()
    video_path = await message.download(file_name="./downloads/input_video.mp4")
    download_end = time.time()

    download_time = download_end - download_start
    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    download_speed = video_size_mb / download_time

    await message.reply_text(
        f"✅ Downloaded in {download_time:.2f} sec | Speed: {download_speed:.2f} MB/s"
    )

    # Watermark process
    processing_start = time.time()
    await message.reply_text("⚙️ Adding watermark, please wait...")

    output_path = "./downloads/watermarked_video.mp4"
    watermark_text = "Join-@skillwithgaurav"

    # FFmpeg command
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x='if(gte(mod(t,5),0), mod(t*30, W-text_w), 0)':y='if(gte(mod(t,5),0), mod(t*20, H-text_h), 0)':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(command, check=True)
    processing_end = time.time()
    processing_time = processing_end - processing_start

    await message.reply_text(f"✅ Watermark added in {processing_time:.2f} sec")

    # Upload video
    upload_start = time.time()
    await message.reply_text("📤 Uploading watermarked video...")
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

    with open(output_path, "rb") as video_file:
        msg = await message.reply_video(video=video_file, caption="✅ Watermarked Successfully!")

    upload_end = time.time()
    upload_time = upload_end - upload_start
    upload_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    upload_speed = upload_size_mb / upload_time

    await message.reply_text(
        f"✅ Uploaded in {upload_time:.2f} sec | Speed: {upload_speed:.2f} MB/s"
    )

    end_time = time.time()
    total_time = end_time - start_time

    await message.reply_text(f"🎉 Total time: {total_time:.2f} seconds ✅")

    # Cleanup
    os.remove(video_path)
    os.remove(output_path)


@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("👋 Send me a video and I'll add a watermark!")

bot.run()
