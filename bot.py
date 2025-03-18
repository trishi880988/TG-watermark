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

# Download/Upload Progress Bar with speed
async def progress_bar(current, total, message: Message, stage: str, start_time):
    now = time.time()
    diff = now - start_time
    if diff == 0:
        diff = 0.1  # avoid division by zero
    speed = current / diff  # bytes per second
    speed_mb = speed / 1024 / 1024  # convert to MB/s
    percent = (current / total) * 100
    try:
        await message.edit_text(
            f"{stage}... {percent:.2f}%\n"
            f"⚡ Speed: {speed_mb:.2f} MB/s"
        )
    except:
        pass  # avoid flood wait errors

@bot.on_message(filters.video & filters.private)
async def watermark_video(client: Client, message: Message):
    start_time = time.time()
    msg = await message.reply_text("📥 Starting download...")

    # Download with progress + speed
    input_path = "./input.mp4"
    download_start = time.time()
    await message.download(
        file_name=input_path,
        progress=progress_bar,
        progress_args=(msg, "📥 Downloading", download_start)
    )
    download_end = time.time()

    await msg.edit_text("⚙️ Applying watermark...")

    # Watermark start time
    wm_start = time.time()
    output_path = "./output.mp4"

    # FFmpeg Command
    watermark_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"drawtext=text='{WATERMARK}':fontcolor=white:fontsize=24:x=10:y=H-th-10",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-c:a", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*watermark_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    wm_end = time.time()

    await msg.edit_text("📤 Uploading video...")

    # Upload with progress + speed
    upload_start = time.time()
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    await message.reply_video(
        video=output_path,
        caption=(
            f"✅ Watermark Added Successfully!\n"
            f"📥 Download Time: {int(download_end - download_start)} sec\n"
            f"⚙️ Watermark Time: {int(wm_end - wm_start)} sec\n"
            f"📤 Upload Done in: {int(time.time() - upload_start)} sec\n"
            f"⏱️ Total Time: {int(time.time() - start_time)} sec\n"
            f"By @skillwithgaurav"
        ),
        progress=progress_bar,
        progress_args=(msg, "📤 Uploading", upload_start)
    )

    await msg.delete()
    os.remove(input_path)
    os.remove(output_path)

bot.run()
