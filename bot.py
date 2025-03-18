import os
import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("watermark_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

@app.on_message(filters.private & filters.video)
async def watermark(client: Client, message: Message):
    await message.reply_chat_action(ChatAction.RECORD_VIDEO)
    
    video = message.video or message.document
    file_name = video.file_name or "video.mp4"
    if not file_name.endswith(".mp4"):
        file_name += ".mp4"
    
    input_path = f"./downloads/{file_name}"
    output_path = f"./downloads/watermarked_{file_name}"
    
    # Download video
    download_start = time.time()
    downloading = await message.reply_text("📥 Downloading video...")
    await message.download(input_path)
    download_end = time.time()
    await downloading.edit(f"✅ Video downloaded in {download_end - download_start:.2f} seconds.")
    
    # Apply watermark
    watermark_start = time.time()
    processing = await message.reply_text("⚙️ Applying watermark...")

    watermark_text = "Join-@skillwithgaurav"
    command = (
        f"ffmpeg -i '{input_path}' -vf "
        f"drawtext=text='{watermark_text}':fontcolor=white:fontsize=24:x='if(gte(mod(t,5),0), rand(0, main_w-text_w))':y='if(gte(mod(t,5),0), rand(0, main_h-text_h))':enable='gt(t,0)',"
        f"format=yuv420p -c:a copy '{output_path}' -y"
    )

    logging.info(f"Running command: {command}")
    os.system(command)

    watermark_end = time.time()
    await processing.edit(f"✅ Watermark applied in {watermark_end - watermark_start:.2f} seconds.")

    # Upload video
    upload_start = time.time()
    uploading = await message.reply_text("📤 Uploading watermarked video...")
    await message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    await message.reply_video(video=output_path, caption="✅ Watermarked Successfully!")
    upload_end = time.time()
    await uploading.edit(f"✅ Uploaded in {upload_end - upload_start:.2f} seconds.")

    # Cleanup
    os.remove(input_path)
    os.remove(output_path)

if __name__ == "__main__":
    app.run()
