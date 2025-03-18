import os
import asyncio
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("fast-watermark-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

WATERMARK_TEXT = "Join - @skillwithgaurav"

@bot.on_message(filters.video)
async def process_video(client, message):
    try:
        if message.video.file_size == 0:
            await message.reply("❌ वीडियो corrupt है या सही से अपलोड नहीं हुआ। कृपया दोबारा भेजें।")
            return

        await message.reply("📥 डाउनलोड कर रहा हूँ...")

        # Download video
        file_path = await message.download(file_name=f"/tmp/{message.video.file_name}")
        
        if os.path.getsize(file_path) == 0:
            await message.reply("❌ वीडियो डाउनलोड नहीं हो पाया, कृपया फिर से प्रयास करें।")
            return

        output_path = f"/tmp/watermarked_{message.video.file_name}"
        await message.reply("🎯 तेज़ी से watermark जोड़ रहा हूँ...")

        # Fast ffmpeg watermark logic
        await asyncio.to_thread(apply_ffmpeg_watermark, file_path, output_path)

        await message.reply("✅ Watermark तैयार है, भेज रहा हूँ...")
        await message.reply_video(output_path, caption="✅ Done! Watermark applied successfully.\n@skillwithgaurav")

        os.remove(file_path)
        os.remove(output_path)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply("❌ कोई त्रुटि आ गई, कृपया फिर से प्रयास करें।")

def apply_ffmpeg_watermark(input_path, output_path):
    # ffmpeg dynamic watermark expression (moves every 5 sec)
    command = f"""
    ffmpeg -i "{input_path}" -vf "
    drawtext=text='{WATERMARK_TEXT}':fontcolor=white:fontsize=24:borderw=1:
    x='if(lt(mod(t,20),5), (W/2-text_w/2), if(lt(mod(t,20),10), 0, if(lt(mod(t,20),15), W-text_w, (W/2-text_w/2))))':
    y='if(lt(mod(t,20),5), 0, if(lt(mod(t,20),10), H/2-text_h/2, if(lt(mod(t,20),15), H-text_h, H/2-text_h/2)))'
    " -c:a copy -preset veryfast -movflags +faststart "{output_path}" -y
    """
    os.system(command)

bot.run()

