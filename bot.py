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

bot = Client("video_merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

video_store = {}  # Store user-wise first video


@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Hey! Send me the **first video**.\n\n"
        "- Then send the **second video** and I will merge them.\n"
        "- Output will be in **16:9 YouTube ratio**.\n"
        "- Speed + progress sab dikhega! 🚀"
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

    # FIRST video case
    if user_id not in video_store:
        video_store[user_id] = video_path
        await message.reply_text("✅ First video saved!\n\nNow send me the **second video**.")
    else:
        await message.reply_text("⚙️ **Merging videos now! Please wait...**")
        await message.reply_chat_action(ChatAction.RECORD_VIDEO)

        first_video = video_store.pop(user_id)
        second_video = video_path
        output_path = f"./downloads/merged_{user_id}_{int(time.time())}.mp4"

        merge_start = time.time()

        # 16:9 scaling + merge command
        command = [
            "ffmpeg",
            "-i", first_video,
            "-i", second_video,
            "-filter_complex",
            "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];" +
            "[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];" +
            "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]

        subprocess.run(command, check=True)
        merge_end = time.time()
        merge_time = merge_end - merge_start

        await message.reply_text(f"✅ Merged in **{merge_time:.2f} sec** 🚀")

        # Upload merged video
        await message.reply_text("📤 Uploading final merged video...")
        await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

        upload_start = time.time()
        with open(output_path, "rb") as merged:
            await message.reply_video(
                video=merged,
                caption="✅ **Merged Successfully!** 🎬\n_YouTube friendly 16:9 ratio_"
            )
        upload_end = time.time()
        upload_time = upload_end - upload_start
        upload_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        upload_speed = upload_size_mb / upload_time

        await message.reply_text(f"✅ Uploaded in **{upload_time:.2f} sec** | Speed: **{upload_speed:.2f} MB/s** 🔥")

        # Clean up files
        os.remove(first_video)
        os.remove(second_video)
        os.remove(output_path)


bot.run()
