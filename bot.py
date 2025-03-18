import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
BOT_TOKEN = os.environ.get("BOT_TOKEN"))

DOWNLOAD_DIR = "./downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

app = Client("watermark-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T"]:
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}P{suffix}"


@app.on_message(filters.video)
async def watermark_video(client: Client, message: Message):
    start_time = time.time()
    status = await message.reply("⏳ Downloading video...")

    video_path = os.path.join(DOWNLOAD_DIR, f"{message.video.file_unique_id}.mp4")
    output_path = os.path.join(DOWNLOAD_DIR, f"output_{message.video.file_unique_id}.mp4")

    try:
        await message.download(file_name=video_path)
        downloaded_size = os.path.getsize(video_path)
        await status.edit_text(f"✅ Downloaded: {sizeof_fmt(downloaded_size)}\n🔄 Adding watermark...")

        # Process with moviepy
        clip = VideoFileClip(video_path)
        txt_clip = TextClip("Join @YourChannel", fontsize=30, color='white', bg_color='black', font="DejaVu-Sans")

        txt_clip = txt_clip.set_pos(('center', 'bottom')).set_duration(clip.duration)
        video = CompositeVideoClip([clip, txt_clip])

        # Start watermark timer
        process_start = time.time()
        video.write_videofile(output_path, codec='libx264', audio_codec='aac')
        process_end = time.time()

        await status.edit_text(
            f"✅ Watermark added!\n⚡ Processing Time: {int(process_end - process_start)}s\n⬆️ Uploading video..."
        )

        await message.reply_video(
            video=output_path,
            caption=f"✅ Done! ⏱ Total time: {int(time.time() - start_time)}s"
        )
        await status.delete()

    except Exception as e:
        await status.edit_text(f"⚠️ Error: `{e}`")

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)


app.run()
