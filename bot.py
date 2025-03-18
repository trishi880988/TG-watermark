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

bot = Client("session_merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary storage per user
user_sessions = {}

@bot.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id

    if user_id not in user_sessions:
        await message.reply_text("⬇️ Downloading first video...")
        video_path = await message.download(file_name=f"./downloads/first_{user_id}.mp4")
        user_sessions[user_id] = video_path
        await message.reply_text("✅ First video saved! Now send me the second video to merge.")
    else:
        await message.reply_text("⬇️ Downloading second video...")
        second_video_path = await message.download(file_name=f"./downloads/second_{user_id}.mp4")
        
        # Merge both videos
        await message.reply_text("⚙️ Merging videos now... Please wait!")
        
        merged_output_path = f"./downloads/merged_{user_id}.mp4"
        file_list_path = f"./downloads/file_list_{user_id}.txt"
        with open(file_list_path, "w") as f:
            f.write(f"file '{os.path.abspath(user_sessions[user_id])}'\n")
            f.write(f"file '{os.path.abspath(second_video_path)}'\n")

        start_time = time.time()

        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", file_list_path,
            "-c", "copy",
            merged_output_path,
            "-y"
        ]
        subprocess.run(command, check=True)

        end_time = time.time()
        await message.reply_text(f"✅ Merged in {end_time - start_time:.2f} sec!")

        # Upload merged video
        await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
        with open(merged_output_path, "rb") as video_file:
            await message.reply_video(video=video_file, caption="🎉 Merged Successfully!")

        # Clean up
        os.remove(user_sessions[user_id])
        os.remove(second_video_path)
        os.remove(merged_output_path)
        os.remove(file_list_path)
        del user_sessions[user_id]

        await message.reply_text("🔄 Session reset! You can now send a new first video.")

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("👋 Send me the first video, then send the second video. I will merge them!")

bot.run()
