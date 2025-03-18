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

bot = Client("watermark_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Hey! Bas ek video bhejo aur main uspe watermark laga ke bhej dunga.\n\n"
        "**Watermark:** Join-@skillwithgaurav | Website - Riyasmm.shop\n\n"
        "⏳ Please wait jab tak processing ho."
    )


@bot.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id

    await message.reply_text("⬇️ Downloading video...")
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    start_dl = time.time()

    # Download incoming video
    video_path = await message.download(file_name=f"./downloads/{user_id}_{int(time.time())}.mp4")
    end_dl = time.time()

    dl_time = end_dl - start_dl
    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    download_speed = video_size_mb / dl_time

    await message.reply_text(f"✅ Downloaded in **{dl_time:.2f} sec** | Speed: **{download_speed:.2f} MB/s**")

    # Watermarking process
    await message.reply_text("⚙️ **Adding watermark! Please wait...**")
    await message.reply_chat_action(ChatAction.RECORD_VIDEO)

    output_path = f"./downloads/watermarked_{user_id}_{int(time.time())}.mp4"

    watermark_text = "Join-@skillwithgaurav | Website - Riyasmm.shop"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf",
        f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x=10:y=H-th-10:box=1:boxcolor=black@0.5:boxborderw=5",
        "-c:a", "copy",
        output_path
    ]

    subprocess.run(command, check=True)

    await message.reply_text("📤 Uploading watermarked video...")
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

    upload_start = time.time()
    with open(output_path, "rb") as watermarked:
        await message.reply_video(
            video=watermarked,
            caption="✅ **Watermark Added Successfully!** 🎬"
        )
    upload_end = time.time()
    upload_time = upload_end - upload_start
    upload_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    upload_speed = upload_size_mb / upload_time

    await message.reply_text(f"✅ Uploaded in **{upload_time:.2f} sec** | Speed: **{upload_speed:.2f} MB/s** 🔥")

    # Clean up files
    os.remove(video_path)
    os.remove(output_path)


bot.run()
