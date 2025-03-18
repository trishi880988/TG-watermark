import os
import time
import asyncio
import logging
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for API credentials
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

# Directory to store downloaded and merged files
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Initialize Pyrogram Client
app = Client("merge-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Memory store for outro video
outro_video_path = {}

# Progress bar function
async def progress_bar(current, total, status_message, stage, start_time):
    now = time.time()
    diff = now - start_time
    speed = current / diff if diff > 0 else 0
    percentage = (current * 100) / total
    eta = (total - current) / speed if speed > 0 else 0

    if speed > 1024 * 1024:
        speed_text = f"{speed / 1024 / 1024:.2f} MB/s"
    elif speed > 1024:
        speed_text = f"{speed / 1024:.2f} KB/s"
    else:
        speed_text = f"{speed:.2f} B/s"

    eta_text = time.strftime("%H:%M:%S", time.gmtime(eta))
    progress_length = 20
    filled_length = int(progress_length * (current / total))
    bar = "█" * filled_length + "░" * (progress_length - filled_length)

    try:
        await status_message.edit_text(
            f"**{stage}**\n"
            f"`{bar}` {percentage:.1f}%\n"
            f"**Speed:** {speed_text} | **ETA:** {eta_text}"
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Error updating progress bar: {e}")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 **Hi!** Send me your outro video first.\n"
        "Then send me your main video to merge with the outro.\n\n"
        "✅ I will handle watermarking + merging automatically!"
    )

@app.on_message(filters.video)
async def handle_videos(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id not in outro_video_path:
        # Save Outro
        status = await message.reply("📥 **Downloading outro video...**")
        outro_path = os.path.join(DOWNLOAD_DIR, f"outro_{message.video.file_unique_id}.mp4")
        start_time = time.time()
        try:
            await message.download(
                file_name=outro_path,
                progress=progress_bar,
                progress_args=(status, "⬇️ Downloading Outro", start_time)
            )
            outro_video_path[user_id] = outro_path
            await status.edit_text("✅ **Outro saved!**\nNow send me your main video.")
        except Exception as e:
            logger.error(f"Error downloading outro video: {e}")
            await status.edit_text("❌ **Failed to download outro video!**")
    else:
        # Save Main + Merge
        outro_path = outro_video_path.pop(user_id)
        status = await message.reply("📥 **Downloading main video...**")
        main_video_path = os.path.join(DOWNLOAD_DIR, f"main_{message.video.file_unique_id}.mp4")
        output_path = os.path.join(DOWNLOAD_DIR, f"merged_{message.video.file_unique_id}.mp4")
        start_time = time.time()

        try:
            await message.download(
                file_name=main_video_path,
                progress=progress_bar,
                progress_args=(status, "⬇️ Downloading Main Video", start_time)
            )
            await status.edit_text("🔄 **Merging videos...**")

            # Merge videos using subprocess
            ffmpeg_cmd = [
                "ffmpeg", "-i", main_video_path, "-i", outro_path,
                "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
                "-map", "[outv]", "-map", "[outa]",
                "-preset", "veryfast", "-crf", "24", output_path, "-y"
            ]
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if os.path.exists(output_path):
                await status.edit_text("📤 **Uploading merged video...**")
                start_time = time.time()
                await message.reply_video(
                    video=output_path,
                    caption="✅ **Successfully merged outro!**",
                    progress=progress_bar,
                    progress_args=(status, "⬆️ Uploading", start_time)
                )
                await status.delete()
            else:
                await status.edit_text("❌ **Merge failed!**")
        except Exception as e:
            logger.error(f"Error processing main video: {e}")
            await status.edit_text("❌ **Failed to process main video!**")
        finally:
            for path in [main_video_path, outro_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)

if __name__ == "__main__":
    app.run()
