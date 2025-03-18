import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess

# Config
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WATERMARK_TEXT = "Join-@skillwithgaurav"

# Create bot client
bot = Client("watermark_bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

DOWNLOADS = "downloads"
os.makedirs(DOWNLOADS, exist_ok=True)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text("👋 Send me a video and I'll add a rotating watermark and show speeds!")

@bot.on_message(filters.video & filters.private)
async def process_video(client, message: Message):
    msg = await message.reply_text("⬇️ Downloading your video...")

    video_path = f"{DOWNLOADS}/{message.video.file_id}.mp4"
    output_path = f"{DOWNLOADS}/watermarked_{message.video.file_id}.mp4"

    # Download with speed
    download_start = time.time()
    await message.download(file_name=video_path)
    download_end = time.time()
    download_speed = round(message.video.file_size / (download_end - download_start) / 1024 / 1024, 2)

    await msg.edit(f"✨ Applying watermark...\n📥 Download Speed: {download_speed} MB/s")

    # Apply watermark
    ffmpeg_cmd = f"""
    ffmpeg -i "{video_path}" -vf "
    drawtext=text='{WATERMARK_TEXT}':fontfile='Poppins-Regular.ttf':fontsize=30:fontcolor=white:borderw=2:
    shadowcolor=black:shadowx=2:shadowy=2:
    x='if(lt(mod(t\\,10)\\,5)\\, 10\\, W-tw-10)':
    y='if(lt(mod(t\\,10)\\,5)\\, 10\\, H-th-10)':
    alpha='if(lt(mod(t\\,10)\\,5)\\, 0.9\\, 0.9)'
    " -c:a copy "{output_path}" -y
    """
    subprocess.run(ffmpeg_cmd, shell=True, check=True)

    # Upload with speed
    upload_start = time.time()
    await msg.edit("⏫ Uploading your video...")
    sent_msg = await message.reply_video(video=output_path, caption="✅ Watermarked video")
    upload_end = time.time()
    upload_speed = round(os.path.getsize(output_path) / (upload_end - upload_start) / 1024 / 1024, 2)

    await msg.edit(f"✅ Done!\n📥 Download Speed: {download_speed} MB/s\n⏫ Upload Speed: {upload_speed} MB/s")

    # Clean up
    os.remove(video_path)
    os.remove(output_path)

bot.run()

