import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

app = Client("watermark_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Human-readable size
def human_readable_size(size):
    for unit in ['B','KB','MB','GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

# Progress function
async def progress(current, total, message, start_time, process_type="Downloading"):
    now = time.time()
    elapsed = now - start_time
    speed = current / elapsed
    percentage = current * 100 / total
    speed_human = human_readable_size(speed)
    total_human = human_readable_size(total)
    current_human = human_readable_size(current)
    eta = (total - current) / speed if speed != 0 else 0
    eta_formatted = time.strftime("%H:%M:%S", time.gmtime(eta))

    text = (f"{process_type}... {percentage:.2f}%\n"
            f"📥 {current_human} / {total_human}\n"
            f"⚡ Speed: {speed_human}/s\n"
            f"⏳ ETA: {eta_formatted}")

    await message.edit(text)

@app.on_message(filters.video & filters.private)
async def watermark_video(client, message: Message):
    video = message.video
    start_time = time.time()
    sent_msg = await message.reply_text("🔄 Starting download...")

    # Download with progress
    file_path = await message.download(progress=progress, progress_args=(sent_msg, start_time, "📥 Downloading"))

    # File Size
    size = os.path.getsize(file_path)
    size_human = human_readable_size(size)
    await sent_msg.edit(f"✅ Downloaded {size_human}\n⚙️ Watermarking...")

    # Watermark
    output_path = "./output.mp4"
    watermark_text = "Join @skillwithgaurav"

    # ffmpeg command with overwrite
    cmd = f'ffmpeg -i "{file_path}" -vf "drawtext=text=\'{watermark_text}\':fontcolor=white:fontsize=24:x=10:y=H-th-10" -codec:a copy "{output_path}" -y'
    os.system(cmd)

    # Check if output exists
    if os.path.exists(output_path):
        await sent_msg.edit("📤 Uploading...")
        start_upload = time.time()
        await message.reply_video(output_path, caption="✅ Watermark added!",
                                  progress=progress, progress_args=(sent_msg, start_upload, "📤 Uploading"))
        await sent_msg.delete()
    else:
        await sent_msg.edit("❌ Watermark failed!")

    # Cleanup
    os.remove(file_path)
    os.remove(output_path)

app.run()
