import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs import Config
from core.clean import delete_all

bot = Client("watermark_bot", bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)
user_settings = {}

# Start & Help command
@bot.on_message(filters.command(["start", "help"]) & filters.private)
async def start_help(client, message):
    await message.reply_text(
        "Send me a video and I will add a rotating watermark text on it.\n\n"
        "Default watermark text: 'Join @yourchannel'\n"
        "You can customize watermark text using the button below.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Set Watermark Text", callback_data="set_text")]
            ]
        )
    )

# Set watermark text button
@bot.on_callback_query(filters.regex("set_text"))
async def set_text_prompt(client, callback_query):
    await callback_query.message.edit_text("Please send me the watermark text you want to use.")
    user_settings[callback_query.from_user.id] = user_settings.get(callback_query.from_user.id, {})
    user_settings[callback_query.from_user.id]['awaiting_text'] = True

# Receive watermark text
@bot.on_message(filters.text & filters.private)
async def save_text(client, message):
    user_id = message.from_user.id
    if user_settings.get(user_id, {}).get('awaiting_text'):
        user_settings[user_id]['text'] = message.text
        user_settings[user_id]['awaiting_text'] = False
        await message.reply_text(f"Watermark text set to: {message.text}")
    else:
        await message.reply_text("Send me a video now to apply watermark.")

# Handle video
@bot.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id
    video_path = f"{Config.DOWN_PATH}/{user_id}_video.mp4"
    await message.download(file_name=video_path)

    output_path = f"{Config.DOWN_PATH}/{user_id}_output.mp4"
    settings = user_settings.get(user_id, {})
    text = settings.get('text', 'Join @yourchannel')
    await add_watermark(video_path, output_path, text=text)

    await client.send_video(message.chat.id, video=output_path, caption="Here is your watermarked video.")
    delete_all(Config.DOWN_PATH, user_id)

# Watermark Function
async def add_watermark(input_video, output_video, text="Join @yourchannel", font="Poppins-Regular.ttf", size=24, quality=23):
    cmd = [
        "ffmpeg",
        "-i", input_video,
        "-vf",
        f"drawtext=fontfile={font}: text='{text}': fontcolor=white: fontsize={size}: " +
        "x='if(lt(mod(t,20),5),10, if(lt(mod(t,20),10),W-tw-10, if(lt(mod(t,20),15),10, W-tw-10)))': " +
        "y='if(lt(mod(t,20),5),10, if(lt(mod(t,20),10),10, if(lt(mod(t,20),15),H-th-10, H-th-10)))': " +
        "enable='between(t,0,99999)'," +
        "fade=t=in:st=0:d=0.5:alpha=1",
        "-c:a", "copy",
        "-crf", str(quality),
        output_video
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()

bot.run()
