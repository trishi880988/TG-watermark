import os
import time
import math
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"

DOWN_PATH = "./downloads"
if not os.path.exists(DOWN_PATH):
    os.makedirs(DOWN_PATH)

app = Client("watermark-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def human_readable(size):
    if size == 0:
        return "0B"
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size,2)} {Dic_powerN[n]}B"

async def progress(current, total, message, start):
    now = time.time()
    diff = now - start
    speed = human_readable(current / diff) + "/s"
    percentage = current * 100 / total
    time_left = (total - current) / (current / diff)
    progress_bar = "[" + ("=" * int(percentage / 10)) + (" " * (10 - int(percentage / 10))) + "]"
    await message.edit_text(
        f"{progress_bar} {round(percentage, 2)}%\n"
        f"Speed: {speed}\n"
        f"ETA: {round(time_left)}s"
    )

@app.on_message(filters.video)
async def watermark_video(client, message: Message):
    try:
        msg = await message.reply("📥 Downloading video...")
        start_time = time.time()

        video_path = os.path.join(DOWN_PATH, f"{message.video.file_id}.mp4")
        output_path = os.path.join(DOWN_PATH, f"output_{message.video.file_id}.mp4")

        # Download with progress
        await message.download(
            file_name=video_path,
            progress=progress,
            progress_args=(msg, start_time)
        )

        await msg.edit_text("✅ Download complete!\n🎯 Applying watermark...")

        # Apply watermark with ffmpeg
        os.system(f"./bin/ffmpeg -i {video_path} -vf drawtext=\"text='Join @YourChannel':x=10:y=H-th-10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5\" -codec:a copy {output_path}")

        if os.path.exists(output_path):
            await msg.edit_text("🚀 Uploading video...")
            upload_start = time.time()

            # Upload with progress
            await message.reply_video(
                video=output_path,
                caption="✅ Watermark applied!",
                progress=progress,
                progress_args=(msg, upload_start)
            )

            await msg.edit_text("✅ Done! 🎉")
            os.remove(output_path)
            os.remove(video_path)
        else:
            await msg.edit_text("❌ Watermark failed!")

    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")

app.run()

