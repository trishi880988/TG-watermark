import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from configs import Config
from core.ffmpeg import add_watermark
from core.clean import delete_all

# Create downloads folder if not exists
os.makedirs(Config.DOWN_PATH, exist_ok=True)

# MongoDB setup
mongo_client = MongoClient(Config.MONGO_URI)
db = mongo_client[Config.DB_NAME]
users = db["user_settings"]

bot = Client("watermark_bot", bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)

@bot.on_message(filters.command(["start", "help"]) & filters.private)
async def start_help(client, message):
    await message.reply_text(
        "Send me a PNG/JPG/GIF to use as a watermark, followed by a video.\n"
        "You can customize the watermark using the buttons below.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Set Position", callback_data="set_position")],
                [InlineKeyboardButton("Set Size", callback_data="set_size")],
                [InlineKeyboardButton("Set Quality", callback_data="set_quality")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("set_position"))
async def position_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "Choose Position:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Top-Left", callback_data="pos_10_10")],
                [InlineKeyboardButton("Top-Right", callback_data="pos_-10_10")],
                [InlineKeyboardButton("Bottom-Left", callback_data="pos_10_-10")],
                [InlineKeyboardButton("Bottom-Right", callback_data="pos_-10_-10")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("pos_"))
async def set_position(client, callback_query):
    pos = callback_query.data.split("_")[1:]
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"position": [int(pos[0]), int(pos[1])]}},
        upsert=True
    )
    await callback_query.message.edit_text(f"Watermark position set to {pos}.")

@bot.on_callback_query(filters.regex("set_size"))
async def size_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "Choose Size:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("50%", callback_data="size_50")],
                [InlineKeyboardButton("75%", callback_data="size_75")],
                [InlineKeyboardButton("100%", callback_data="size_100")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("size_"))
async def set_size(client, callback_query):
    size = int(callback_query.data.split("_")[1])
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"size": size}},
        upsert=True
    )
    await callback_query.message.edit_text(f"Watermark size set to {size}%.")

@bot.on_callback_query(filters.regex("set_quality"))
async def quality_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "Choose Quality:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Low", callback_data="quality_30")],
                [InlineKeyboardButton("Medium", callback_data="quality_23")],
                [InlineKeyboardButton("High", callback_data="quality_18")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("quality_"))
async def set_quality(client, callback_query):
    quality = int(callback_query.data.split("_")[1])
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"quality": quality}},
        upsert=True
    )
    await callback_query.message.edit_text(f"Video quality set to {quality}.")

@bot.on_message(filters.photo & filters.private)
async def handle_watermark_image(client, message):
    watermark_path = f"{Config.DOWN_PATH}/{message.from_user.id}_watermark.png"
    await message.download(file_name=watermark_path)
    await message.reply_text("Watermark saved. Now send a video to apply this watermark.")

@bot.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id
    watermark_path = f"{Config.DOWN_PATH}/{user_id}_watermark.png"
    if not os.path.exists(watermark_path):
        await message.reply_text("No watermark image found. Please send a watermark image first.")
        return

    video_path = f"{Config.DOWN_PATH}/{user_id}_video.mp4"
    await message.download(file_name=video_path)

    output_path = f"{Config.DOWN_PATH}/{user_id}_output.mp4"
    user_data = users.find_one({"user_id": user_id}) or {}

    position = user_data.get('position', [10, 10])
    size = user_data.get('size', 100)
    quality = user_data.get('quality', 23)

    await add_watermark(video_path, watermark_path, output_path, tuple(position), size, quality)
    await client.send_video(message.chat.id, video=output_path, caption="Here is your watermarked video.")
    delete_all(Config.DOWN_PATH, user_id)

bot.run()

