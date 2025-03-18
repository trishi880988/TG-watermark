import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

DOWN_PATH = "./downloads"

if not os.path.exists(DOWN_PATH):
    os.makedirs(DOWN_PATH)

app = Client("watermark-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


async def progress_bar(current, total, message, stage):
    percentage = (current / total) * 100
    progress = f"[{'█' * int(percentage // 10)}{'░' * (10 - int(percentage // 10))}] {percentage:.1f}%"
    try:
        await message.edit_text(f"{stage}...\n{progress}")
    except FloodWait as e:
        await asyncio.sleep(e.value)


@app.on_message(filters.video)
async def watermark_video(client: Client, message: Message):
    try:
        status = await message.reply("⏳ Starting download...")

        video_path = os.path.join(DOWN_PATH, f"{message.video.file_id}.mp4")
        output_path = os.path.join(DOWN_PATH, f"output_{message.video.file_id}.mp4")

        # Download with progress
        await message.download(
            file_name=video_path,
            progress=progress_bar,
            progress_args=(status, "⬇️ Downloading")
        )

        await status.edit_text("✅ Download complete!\n🔄 Applying watermark...")

        # Apply watermark
        os.system(f"./bin/ffmpeg -i {video_path} -vf drawtext=\"text='Join @YourChannel':x=10:y=H-th-10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5\" -codec:a copy {output_path}")

        if os.path.exists(output_path):
            await status.edit_text("✅ Watermark applied!\n⬆️ Uploading video...")

            # Upload with progress
            await message.reply_video(
                video=output_path,
                caption="✅ Done! Watermark successfully added ✅",
                progress=progress_bar,
                progress_args=(status, "⬆️ Uploading")
            )
            await status.delete()
        else:
            await status.edit_text("❌ Watermark failed, output not found!")

        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)

    except Exception as e:
        await status.edit_text(f"⚠️ Error: `{e}`")


app.run()
