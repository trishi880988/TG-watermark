import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("speed_watermark_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

WATERMARK = "Join @skillwithgaurav"

# Download Progress Bar
async def progress_bar(current, total, message, stage):
    percent = (current / total) * 100
    await message.edit(f"{stage}... {percent:.2f}%")

@bot.on_message(filters.video & filters.private)
async def watermark_video(client: Client, message: Message):
    start_time = time.time()
    msg = await message.reply("📥 Starting download...")

    # Download with progress
    video = await message.download(file_name="./input.mp4", progress=progress_bar, progress_args=(msg, "📥 Downloading"))

    await msg.edit("⚙️ Applying watermark...")

    # Watermark process start time
    wm_start = time.time()
    output = "./output.mp4"

    # FFmpeg Command - Fast Mode
    watermark_cmd = [
        "ffmpeg", "-y", "-i", video,
        "-vf", f"drawtext=text='{WATERMARK}':fontcolor=white:fontsize=24:x=10:y=H-th-10",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-c:a", "copy", output
    ]
    process = await asyncio.create_subprocess_exec(*watermark_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    wm_end = time.time()

    await msg.edit("📤 Uploading video...")

    # Upload with progress
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    await message.reply_video(output, caption=(
        f"✅ Watermark Added Successfully!\n"
        f"📥 Download Time: {int(wm_start - start_time)} sec\n"
        f"⚙️ Watermark Time: {int(wm_end - wm_start)} sec\n"
        f"📤 Upload Done in: {int(time.time() - wm_end)} sec\n"
        f"⏱️ Total Time: {int(time.time() - start_time)} sec\n"
        f"By @skillwithgaurav"
    ), progress=progress_bar, progress_args=(msg, "📤 Uploading"))

    await msg.delete()
    os.remove(video)
    os.remove(output)

bot.run()


