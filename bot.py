
# main.py
import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient
from config import API_ID, API_HASH, BOT_TOKEN, DATABASE_URL, BOT_USERNAME, FORCE_SUB_CHANNEL

# MongoDB Setup
client = AsyncIOMotorClient(DATABASE_URL)
db = client['autodelete_db']
groups = db['group_data']

bot = Client(
    name="autodelete",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper Text
START_TEXT = """👋 **Welcome to the AutoDelete Bot!**\n
I can auto-delete group messages after a specific time.

Use /set_time in your group (admins only)."""

HELP_TEXT = """🆘 **Help**\n
1. Add me to your group
2. Promote me as admin with delete rights
3. Use /set_time 10 (to auto-delete after 10 seconds)
4. Use /status to check current settings"""

ABOUT_TEXT = """📖 **About**\n
- Developer: @kissubots\n- Language: Python + Pyrogram\n- Hosting: Flask + MongoDB"""

# Start Command
@bot.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 About", callback_data="about")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ])
        await message.reply(START_TEXT, reply_markup=keyboard)
    else:
        await message.reply("✅ AutoDelete Bot active in this group. Use /set_time (admins only).")

@bot.on_callback_query()
async def cb_handler(_, query):
    data = query.data
    if data == "help":
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif data == "about":
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif data == "home":
        await query.message.edit_text(START_TEXT, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 About", callback_data="about")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]))

# Set Time
@bot.on_message(filters.command("set_time") & filters.group)
async def set_time(_, message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    admins = [m.user.id async for m in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if user_id not in admins:
        return await message.reply("Only admins can set delete time!")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("2 Min", callback_data=f"time_120"),
         InlineKeyboardButton("5 Min", callback_data=f"time_300"),
         InlineKeyboardButton("15 Min", callback_data=f"time_900")],
        [InlineKeyboardButton("Custom", callback_data="time_custom")]
    ])
    await message.reply("⏱ Choose delete time:", reply_markup=keyboard)

@bot.on_callback_query(filters.regex("time_"))
async def set_time_buttons(_, query):
    data = query.data
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    admins = [m.user.id async for m in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if user_id not in admins:
        return await query.answer("Only admins can change time!", show_alert=True)

    if data.startswith("time_custom"):
        await query.message.edit("Send custom delete time in seconds")
        return

    seconds = int(data.split("_")[1])
    await groups.update_one({"group_id": chat_id}, {"$set": {"delete_time": seconds}}, upsert=True)
    await query.message.edit(f"✅ Delete time set to {seconds} seconds.")

@bot.on_message(filters.group & filters.text)
async def autodelete(_, message: Message):
    chat_id = message.chat.id
    group_data = await groups.find_one({"group_id": chat_id})
    if not group_data:
        return
    try:
        await asyncio.sleep(int(group_data['delete_time']))
        await message.delete()
    except:
        pass

# Force Subscribe Admin Only
@bot.on_chat_member_updated()
async def force_sub_check(_, member):
    if member.new_chat_member.status in ["member", "administrator"]:
        user_id = member.from_user.id
        if member.new_chat_member.status == "administrator":
            try:
                user = await bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
                if user.status not in ("member", "administrator", "creator"):
                    await bot.send_message(
                        member.chat.id,
                        f"🚫 Admin must join @kissubots to use me!"
                    )
            except:
                await bot.send_message(
                    member.chat.id,
                    f"❗ Couldn’t verify force-sub for admin."
                )

# Status
@bot.on_message(filters.command("status") & filters.group)
async def status(_, message):
    chat_id = message.chat.id
    group_data = await groups.find_one({"group_id": chat_id})
    if not group_data:
        return await message.reply("❌ No delete time set!")
    await message.reply(f"✅ Messages will be auto-deleted after {group_data['delete_time']} seconds.")

# Start
if __name__ == '__main__':
    Thread(target=run).start()
    bot.run()

# --- WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(f"https://t.me/{BOT_USERNAME}", code=302)

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- MAIN ---
if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
