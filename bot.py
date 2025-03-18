import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from pyrogram import Client, filters

bot = Client("watermarkbot",
             api_id=int(os.environ.get("API_ID")),
             api_hash=os.environ.get("API_HASH"),
             bot_token=os.environ.get("BOT_TOKEN"))

@bot.on_message(filters.video)
async def watermark(client, message):
    video = await message.download()
    file_name = f"watermarked_{message.chat.id}_{message.id}.mp4"

    clip = VideoFileClip(video)
    
    # Watermark Text
    txt = TextClip("Join-@skillwithgaurav | Website - Riyasmm.shop", fontsize=40, color='white', font='Arial')
    txt = txt.set_position(('center', 'bottom')).set_duration(clip.duration).margin(bottom=20, opacity=0)
    
    # Combine Video and Watermark
    final = CompositeVideoClip([clip, txt])
    final.write_videofile(file_name, codec='libx264', audio_codec='aac')

    await message.reply_video(file_name, caption="✅ Watermark done!")
    
    # Cleanup
    os.remove(video)
    os.remove(file_name)

bot.run()
