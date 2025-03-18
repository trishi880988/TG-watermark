import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from configs import Config
from core.ffmpeg import add_watermark
from core.clean import delete_all

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
try:
    mongo_client = MongoClient(Config.MONGO_URI)
    db = mongo_client[Config.DB_NAME]
    users = db["user_settings"]
    logger.info("MongoDB connected successfully.")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit(1)

# Ensure download directory exists
os.makedirs(Config.DOWN_PATH, exist_ok=True)

bot = Client("watermark_bot", bot_token=Config.BOT_TOKEN, api_id=Config.API_ID, api_hash=Config.API_HASH)

# --- COMMAND HANDLERS ---

@bot.on_message(filters.command(["start", "help"]) & filters.private)
async def start_help(client, message):
    await message.reply_text(
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "📌 Send me a PNG/JPG/GIF image as a watermark, then send me your video.\n\n"
        "⚙️ Customize your watermark below 👇",
        reply_markup=main_menu()
    )

def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🧭 Set Position", callback_data="set_position")],
            [InlineKeyboardButton("📏 Set Size", callback_data="set_size")],
            [InlineKeyboardButton("🎞️ Set Quality", callback_data="set_quality")]
        ]
    )

# --- POSITION SETTER ---

@bot.on_callback_query(filters.regex("set_position"))
async def position_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "📍 Choose Watermark Position:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("↖ Top-Left", callback_data="pos_10_10"),
                 InlineKeyboardButton("↗ Top-Right", callback_data="pos_-10_10")],
                [InlineKeyboardButton("↙ Bottom-Left", callback_data="pos_10_-10"),
                 InlineKeyboardButton("↘ Bottom-Right", callback_data="pos_-10_-10")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("pos_"))
async def set_position(client, callback_query):
    pos = callback_query.data.split("_")[1:]
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"position": [int(pos[0]), int(pos[1])]}}
    )
    await callback_query.answer("✅ Position updated!")
    await callback_query.message.edit_text("✔️ Position set successfully!", reply_markup=main_menu())

# --- SIZE SETTER ---

@bot.on_callback_query(filters.regex("set_size"))
async def size_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "🔍 Choose Watermark Size:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("50%", callback_data="size_50"),
                 InlineKeyboardButton("75%", callback_data="size_75"),
                 InlineKeyboardButton("100%", callback_data="size_100")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("size_"))
async def set_size(client, callback_query):
    size = int(callback_query.data.split("_")[1])
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"size": size}}
    )
    await callback_query.answer("✅ Size updated!")
    await callback_query.message.edit_text("✔️ Size set successfully!", reply_markup=main_menu())

# --- QUALITY SETTER ---

@bot.on_callback_query(filters.regex("set_quality"))
async def quality_buttons(client, callback_query):
    await callback_query.message.edit_text(
        "🎚️ Choose Video Quality:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Low", callback_data="quality_30"),
                 InlineKeyboardButton("Medium", callback_data="quality_23"),
                 InlineKeyboardButton("High", callback_data="quality_18")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]
        )
    )

@bot.on_callback_query(filters.regex("quality_"))
async def set_quality(client, callback_query):
    quality = int(callback_query.data.split("_")[1])
    users.update_one(
        {"user_id": callback_query.from_user.id},
        {"$set": {"quality": quality}}
    )
    await callback_query.answer("✅ Quality updated!")
    await callback_query.message.edit_text("✔️ Quality set successfully!", reply_markup=main_menu())

# --- BACK BUTTON ---

@bot.on_callback_query(filters.regex("back_main"))
async def back_main_menu(client, callback_query):
    await callback_query.message.edit_text("⚙️ Customize your watermark below 👇", reply_markup=main_menu())

# --- PHOTO HANDLER ---

@bot.on_message(filters.photo & filters.private)
async def handle_watermark_image(client, message):
    watermark_path = f"{Config.DOWN_PATH}/{message.from_user.id}_watermark.png"
    await message.download(file_name=watermark_path)
    await message.reply_text("✅ Watermark saved!\n\n🎥 Now send me your video to apply this watermark.")

# --- VIDEO HANDLER ---

@bot.on_message(filters.video & filters.private)
async def handle_video(client, message):
    user_id = message.from_user.id
    watermark_path = f"{Config.DOWN_PATH}/{user_id}_watermark.png"
    if not os.path.exists(watermark_path):
        await message.reply_text("⚠️ No watermark found!\n\nPlease send me a watermark image first.")
        return

    video_path = f"{Config.DOWN_PATH}/{user_id}_video.mp4"
    await message.download(file_name=video_path)

    output_path = f"{Config.DOWN_PATH}/{user_id}_output.mp4"
    user_data = users.find_one({"user_id": user_id}) or {}

    position = user_data.get('position', [10, 10])
    size = user_data.get('size', 100)
    quality = user_data.get('quality', 23)

    await message.reply_text("🛠️ Applying watermark... Please wait ⏳")

    try:
        await add_watermark(video_path, watermark_path, output_path, tuple(position), size, quality)
        await client.send_video(message.chat.id, video=output_path, caption="✅ Here is your watermarked video.")
    except Exception as e:
        logger.error(f"Watermark processing failed: {e}")
        await message.reply_text("❌ Failed to process video. Please try again.")
    finally:
        delete_all(Config.DOWN_PATH, user_id)

# --- START BOT ---
bot.run()
