import os
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Path of the second video to append
SECOND_VIDEO_PATH = "./static/second_video.mp4"

@bot.on_message(filters.video & filters.private)
async def merge_videos(client, message):
    start_time = time.time()
    
    await message.reply_text("⬇️ Downloading video...")
    await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)

    # Download user video
    download_start = time.time()
    input_video_path = await message.download(file_name="./downloads/input_video.mp4")
    download_end = time.time()

    download_time = download_end - download_start
    video_size_mb = os.path.getsize(input_video_path) / (1024 * 1024)
    download_speed = video_size_mb / download_time

    await message.reply_text(
        f"✅ Downloaded in {download_time:.2f} sec | Speed: {download_speed:.2f} MB/s"
    )

    # Merge process
    processing_start = time.time()
    await message.reply_text("⚙️ Merging videos, please wait...")

    merged_output_path = "./downloads/merged_video.mp4"

    # Create file list for FFmpeg concat
    file_list_path = "./downloads/file_list.txt"
    with open(file_list_path, "w") as f:
        f.write(f"file '{os.path.abspath(input_video_path)}'\n")
        f.write(f"file '{os.path.abspath(SECOND_VIDEO_PATH)}'\n")

    # FFmpeg merge command
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", file_list_path,
        "-c", "copy",
        merged_output_path
    ]
    subprocess.run(command, check=True)
    processing_end = time.time()
    processing_time = processing_end - processing_start

    await message.reply_text(f"✅ Merged in {processing_time:.2f} sec")

    # Upload merged video
    upload_start = time.time()
    await message.reply_text("📤 Uploading merged video...")
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

    with open(merged_output_path, "rb") as video_file:
        await message.reply_video(video=video_file, caption="✅ Merged Successfully!")

    upload_end = time.time()
    upload_time = upload_end - upload_start
    upload_size_mb = os.path.getsize(merged_output_path) / (1024 * 1024)
    upload_speed = upload_size_mb / upload_time

    await message.reply_text(
        f"✅ Uploaded in {upload_time:.2f} sec | Speed: {upload_speed:.2f} MB/s"
    )

    end_time = time.time()
    total_time = end_time - start_time

    await message.reply_text(f"🎉 Total time: {total_time:.2f} seconds ✅")

    # Cleanup
    os.remove(input_video_path)
    os.remove(merged_output_path)
    os.remove(file_list_path)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("👋 Send me a video and I'll merge it with my custom video!")

bot.run()
