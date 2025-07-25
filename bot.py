import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL, OWNER_ID

# MongoDB Setup
client = AsyncIOMotorClient(DATABASE_URL)
db = client['autodelete']
groups = db['group_id']

bot = Client(
    "deletebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=10
)

# Flask Setup
app = Flask(__name__)
@app.route('/')
def index():
    return redirect(f"https://t.me/{BOT_USERNAME}", code=302)

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

# START COMMAND
@bot.on_message(filters.command("start"))
async def start(_, message):
    if message.chat.type != enums.ChatType.PRIVATE:
        return await message.reply("👋 Welcome! I can auto-delete messages in this group.")

    buttons = [
        [InlineKeyboardButton("ℹ️ About", callback_data="about"), InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    await message.reply_text(
        f"👋 **Welcome to Auto Delete Bot!**\n\nI automatically delete messages in your group after a custom time.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# HELP & ABOUT
@bot.on_callback_query(filters.regex("help"))
async def help_callback(_, query):
    text = "🛠️ **Help**\n\nUse /set_time to define delete time in seconds.\nMessages will auto-delete after that."
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    await query.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("about"))
async def about_callback(_, query):
    text = "ℹ️ **About**\n\nMade by @KissuRajput for managing group spam and clean chats."
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    await query.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("back"))
async def back_callback(_, query):
    buttons = [
        [InlineKeyboardButton("ℹ️ About", callback_data="about"), InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    await query.message.edit(
        "👋 **Welcome to Auto Delete Bot!**\n\nI automatically delete messages in your group after a custom time.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# SET TIME COMMAND
@bot.on_message(filters.command("set_time"))
async def set_delete_time(_, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply("❌ This command works only in groups.")

    if len(message.command) < 2:
        buttons = [[
            InlineKeyboardButton("2 min", callback_data="time_120"),
            InlineKeyboardButton("5 min", callback_data="time_300"),
            InlineKeyboardButton("15 min", callback_data="time_900")
        ], [
            InlineKeyboardButton("Custom", callback_data="custom")
        ]]
        return await message.reply("⏱️ Choose delete time:", reply_markup=InlineKeyboardMarkup(buttons))

    delete_time = message.text.split()[1]
    if not delete_time.isdigit():
        return await message.reply("❌ Time must be a number in seconds.")

    admins = [m.user.id async for m in bot.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if message.from_user.id not in admins:
        return await message.reply("🚫 Only admins can use this command.")

    await groups.update_one({"group_id": message.chat.id}, {"$set": {"delete_time": int(delete_time)}}, upsert=True)
    await message.reply(f"✅ Auto-delete time set to {delete_time} seconds.")

# CALLBACK FOR TIME
@bot.on_callback_query(filters.regex("^time_"))
async def time_callback(_, query):
    delete_time = int(query.data.split("_")[1])
    chat_id = query.message.chat.id
    await groups.update_one({"group_id": chat_id}, {"$set": {"delete_time": delete_time}}, upsert=True)
    await query.message.edit(f"✅ Auto-delete time set to {delete_time} seconds.")

# DELETE MESSAGES
@bot.on_message(filters.group & filters.text)
async def delete_message(_, message):
    if message.from_user.is_bot:
        return

    group = await groups.find_one({"group_id": message.chat.id})
    if not group:
        return

    delete_time = int(group.get("delete_time", 0))
    admins = [m.user.id async for m in bot.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if message.from_user.id in admins:
        return

    await asyncio.sleep(delete_time)
    try:
        await message.delete()
    except Exception as e:
        print(f"Delete error in {message.chat.id}: {e}")

# STATUS COMMAND
@bot.on_message(filters.command("status") & filters.private)
async def status_command(_, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("🚫 You are not allowed to use this command.")

    count = await groups.count_documents({})
    await message.reply(f"✅ Bot is running.\n\n📊 Groups using bot: {count}")

# BROADCAST COMMAND
@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast(_, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("🚫 You are not allowed to broadcast.")

    if len(message.command) < 2:
        return await message.reply("📢 Usage: /broadcast Your message here")

    text = message.text.split(None, 1)[1]
    success = 0
    fail = 0
    async for group in groups.find({}):
        try:
            await bot.send_message(group["group_id"], text)
            success += 1
        except:
            fail += 1
    await message.reply(f"✅ Broadcast completed.\nSent: {success}, Failed: {fail}")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
