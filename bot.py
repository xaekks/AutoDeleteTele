import os
import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIG ---
API_ID = os.environ.get("API_ID","9301087")
API_HASH = os.environ.get("API_HASH","cbabdb3f23de6326352ef3ac26338d9c")
BOT_TOKEN = os.environ.get("BOT_TOKEN","7879064100:AAFRr4wHNLZaN-LN4E5JYeTi-Qtgc0q1HSc")
DATABASE_URL = os.environ.get("DATABASE_URL","mongodb+srv://bob:bobfiles1@bob.sp1vv.mongodb.net/?retryWrites=true&w=majority&appName=bob")
BOT_USERNAME = os.environ.get("BOT_USERNAME","autoo_deletee_bot") # Without @
FORCE_SUB_CHANNEL = "kissuxbots"  # Without @
OWNER_ID = 7771222218  # Your Telegram user ID

# --- DB ---
client = AsyncIOMotorClient(DATABASE_URL)
db = client['autodelete']
groups = db['group_id']

# --- BOT ---
bot = Client("autodeletebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LANGUAGE SYSTEM ---
LANG = {
    "en": {
        "start": "**I'm an auto-delete bot. Add me to a group and set a delete time!**",
        "set_time_usage": "Send like this: `/set_time 10` (in seconds)",
        "set_success": "✅ Auto-delete set to {time}s!",
        "admin_only": "❌ Only group admins can use this.",
        "number_only": "❌ Time must be a number.",
        "private_only": "❌ Use this command only in groups.",
        "no_permission": "⚠️ I need 'Delete Messages' permission!",
        "settings_title": "🔧 Group Settings",
        "disable_success": "🛑 Auto-delete disabled in this group.",
        "status": "✅ Bot is active and running!",
        "force_sub": "🚫 All group admins must join [@{channel}](https://t.me/{channel}) to use me.",
        "total_groups": "📊 Total groups using bot: **{count}**"
    },
    "hi": {
        "start": "**मैं एक ऑटो-डिलीट बोट हूं, मुझे ग्रुप में जोड़ें और समय सेट करें!**",
        "set_time_usage": "ऐसे भेजें: `/set_time 10` (सेकंड में)",
        "set_success": "✅ डिलीट समय {time} सेकंड सेट कर दिया गया!",
        "admin_only": "❌ केवल ग्रुप एडमिन्स ही इसका उपयोग कर सकते हैं।",
        "number_only": "❌ समय केवल संख्या में होना चाहिए।",
        "private_only": "❌ यह कमांड केवल ग्रुप में उपयोग करें।",
        "no_permission": "⚠️ मुझे 'Delete Messages' की अनुमति दें!",
        "settings_title": "🔧 ग्रुप सेटिंग्स",
        "disable_success": "🛑 इस ग्रुप में ऑटो-डिलीट बंद कर दिया गया।",
        "status": "✅ बोट सक्रिय है!",
        "force_sub": "🚫 सभी एडमिन्स को [@{channel}](https://t.me/{channel}) में शामिल होना आवश्यक है।",
        "total_groups": "📊 बोट का उपयोग करने वाले ग्रुप्स की कुल संख्या: **{count}**"
    }
}

def tr(lang, key, **kwargs):
    return LANG.get(lang, LANG["en"])[key].format(**kwargs)

def get_lang(user):
    return "hi" if user.language_code == "hi" else "en"

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(_, msg):
    lang = get_lang(msg.from_user)
    btn = [[InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]]
    await msg.reply(tr(lang, "start"), reply_markup=InlineKeyboardMarkup(btn))

@bot.on_message(filters.command("set_time"))
async def set_time(_, msg):
    lang = get_lang(msg.from_user)

    if msg.chat.type == enums.ChatType.PRIVATE:
        return await msg.reply(tr(lang, "private_only"))

    if len(msg.command) < 2 or not msg.command[1].isdigit():
        return await msg.reply(tr(lang, "number_only") + "\n\n" + tr(lang, "set_time_usage"))

    delete_time = int(msg.command[1])
    admins = [m.user.id async for m in bot.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]

    if msg.from_user.id not in admins:
        return await msg.reply(tr(lang, "admin_only"))

    # Force Subscribe for Admins
    for admin_id in admins:
        try:
            member = await bot.get_chat_member(f"@{FORCE_SUB_CHANNEL}", admin_id)
            if member.status == enums.ChatMemberStatus.BANNED:
                raise Exception("Banned")
        except:
            return await msg.reply(tr(lang, "force_sub", channel=FORCE_SUB_CHANNEL), disable_web_page_preview=True)

    await groups.update_one({"group_id": msg.chat.id}, {"$set": {"delete_time": delete_time, "enabled": True}}, upsert=True)
    await msg.reply(tr(lang, "set_success", time=delete_time))

@bot.on_message(filters.command("disable"))
async def disable_handler(_, msg):
    lang = get_lang(msg.from_user)
    admins = [m.user.id async for m in bot.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if msg.from_user.id not in admins:
        return await msg.reply(tr(lang, "admin_only"))
    await groups.update_one({"group_id": msg.chat.id}, {"$set": {"enabled": False}})
    await msg.reply(tr(lang, "disable_success"))

@bot.on_message(filters.command("status"))
async def status_handler(_, msg):
    lang = get_lang(msg.from_user)
    admins = [m.user.id async for m in bot.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if msg.from_user.id not in admins:
        return await msg.reply(tr(lang, "admin_only"))
    await msg.reply(tr(lang, "status"))

@bot.on_message(filters.command("total_groups") & filters.user(OWNER_ID))
async def total_groups_handler(_, msg):
    count = await groups.count_documents({})
    await msg.reply(tr("en", "total_groups", count=count))

@bot.on_message(filters.command("settings"))
async def settings(_, msg):
    lang = get_lang(msg.from_user)
    if msg.chat.type == enums.ChatType.PRIVATE:
        return await msg.reply(tr(lang, "private_only"))

    btn = [
        [InlineKeyboardButton("🕒 Set 10s", callback_data="set_10")],
        [InlineKeyboardButton("🛑 Disable AutoDelete", callback_data="disable")]
    ]
    await msg.reply(tr(lang, "settings_title"), reply_markup=InlineKeyboardMarkup(btn))

@bot.on_callback_query()
async def callback_handler(_, cb):
    data = cb.data
    msg = cb.message
    lang = get_lang(cb.from_user)

    admins = [m.user.id async for m in bot.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS)]
    if cb.from_user.id not in admins:
        return await cb.answer("Admins only.", show_alert=True)

    if data.startswith("set_"):
        sec = int(data.split("_")[1])
        await groups.update_one({"group_id": msg.chat.id}, {"$set": {"delete_time": sec, "enabled": True}}, upsert=True)
        await cb.answer(tr(lang, "set_success", time=sec), show_alert=True)

    elif data == "disable":
        await groups.update_one({"group_id": msg.chat.id}, {"$set": {"enabled": False}})
        await cb.answer(tr(lang, "disable_success"), show_alert=True)

@bot.on_message(filters.group & filters.text)
async def auto_delete(_, msg):
    group = await groups.find_one({"group_id": msg.chat.id})
    if not group or not group.get("enabled"):
        return

    delete_time = int(group.get("delete_time", 10))

    try:
        await asyncio.sleep(delete_time)
        await msg.delete()
    except Exception as e:
        if "can't" in str(e) or "rights" in str(e):
            await msg.reply(tr(get_lang(msg.from_user), "no_permission"))
        logger.warning(f"Delete failed in {msg.chat.id}: {e}")

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
