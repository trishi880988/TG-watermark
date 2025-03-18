import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

DOWNLOAD_DIR = "./downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

app = Client("watermark-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


async def progress_bar(current, total, status_message, stage):
    try:
        percentage = (current / total) * 100
        progress = f"[{'█' * int(percentage // 10)}{'░' * (10 - int(percentage // 10))}] {percentage:.1f}%"
        await status_message.edit_text(f"{stage}\n{progress}")
    except FloodWait as e:
        await asyncio.sleep(e.value)


@app.on_message(filters.video)
async def watermark_video(client: Client, message: Message):
    status = await message.reply("⏳ Downloading video...")

    video_path = os.path.join(DOWNLOAD_DIR, f"{message.video.file_unique_id}.mp4")
    output_path = os.path.join(DOWNLOAD_DIR, f"output_{message.video.file_unique_id}.mp4")

    try:
        # Download video
        await message.download(
            file_name=video_path,
            progress=progress_bar,
            progress_args=(status, "⬇️ Downloading")
        )

        await status.edit_text("✅ Download complete!\n🔄 Adding watermark...")

        # Watermark via ffmpeg
        watermark_text = "website-Riyasmm.shop"
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        ffmpeg_cmd = (
            f'ffmpeg -i "{video_path}" -vf '
            f'"drawtext=fontfile={font_path}:text=\'{watermark_text}\':x=10:y=H-th-20:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5" '
            f'-c:a copy "{output_path}" -y'
        )

        os.system(ffmpeg_cmd)

        if os.path.exists(output_path):
            await status.edit_text("✅ Watermark added!\n⬆️ Uploading video...")

            await message.reply_video(
                video=output_path,
                caption="✅ Watermark successfully added!",
                progress=progress_bar,
                progress_args=(status, "⬆️ Uploading")
            )
            await status.delete()
        else:
            await status.edit_text("❌ Watermark failed!")

    except Exception as e:
        await status.edit_text(f"⚠️ Error: `{e}`")

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)


app.run()
