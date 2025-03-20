import os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask, redirect
from threading import Thread
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
 
API_ID = os.environ.get("API_ID","9301087")
API_HASH = os.environ.get("API_HASH","cbabdb3f23de6326352ef3ac26338d9c")
BOT_TOKEN = os.environ.get("BOT_TOKEN","7879064100:AAFRr4wHNLZaN-LN4E5JYeTi-Qtgc0q1HSc")
DATABASE_URL = os.environ.get("DATABASE_URL","mongodb+srv://bob:bobfiles1@bob.sp1vv.mongodb.net/?retryWrites=true&w=majority&appName=bob")
BOT_USERNAME = os.environ.get("BOT_USERNAME","autoo_deletee_bot") # Without @

#database
client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
groups = db['group_id']


bot = Client(
    "deletebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=10
)

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    button = [[
        InlineKeyboardButton("🎈 Aᴅᴅ ʏᴏᴜʀ Gʀᴏᴜᴘ 🎈", url=f"http://t.me/{BOT_USERNAME}?startgroup=none&admin=delete_messages"),
        ]]
    await message.reply_text(
        f"**I ᴀᴍ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Bᴏᴛ, I ᴄᴀɴ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘs ᴍᴇssᴀɢᴇs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴀғᴛᴇʀ ᴀ ᴄᴇʀᴛᴀɪɴ ᴘᴇʀɪᴏᴅ ᴏғ ᴛɪᴍᴇ.**",
        reply_markup=InlineKeyboardMarkup(button),
        parse_mode=enums.ParseMode.MARKDOWN
    )
    
@bot.on_message(filters.command("set_time"))
async def set_delete_time(_, message):

    # Check if the message is from a private chat
    if message.chat.type in [enums.ChatType.PRIVATE]:
        await message.reply("**Tʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ ɢʀᴏᴜᴘs....😒**")
        return
    
    # Extract group_id and delete_time from the message
    if len(message.text.split()) == 1:
        await message.reply_text("**Dᴇʟᴇᴛᴇ ᴛɪᴍᴇ ᴍᴜsᴛ ʙᴇ ᴀɴ ɴᴜᴍʙᴇʀ...\n\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 10\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 20\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 30\n\nOɴʟʏ Sᴇᴄᴏᴜɴᴅ 🙌**")
        return

    delete_time = message.text.split()[1]
    if not delete_time.isdigit():
        await message.reply_text("**Dᴇʟᴇᴛᴇ ᴛɪᴍᴇ ᴍᴜsᴛ ʙᴇ ᴀɴ ɴᴜᴍʙᴇʀ...\n\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 10\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 20\nExᴀᴍᴘʟᴇ : /sᴇᴛ_ᴛɪᴍᴇ 30\n\nOɴʟʏ Sᴇᴄᴏᴜɴᴅ 🙌**")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if the user is the group owner or an admin
    administrators = []
    async for m in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        administrators.append(m.user.id)

    if user_id not in administrators:
        await message.reply("**Oɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs....😘**")
        return
    
    # Save to the database
    await groups.update_one(
        {"group_id": chat_id},
        {"$set": {"delete_time": delete_time}},
        upsert=True
    )
    try:
        await message.reply_text(f"**Sᴜᴄᴄᴇssғᴜʟʟʏ Sᴇᴛ {delete_time} Sᴇᴄᴏᴜɴᴅ....✅**")
    except Exception as e:
        await message.reply_text(f"Erorr: {e}")
         
@bot.on_message(filters.group & filters.text)
async def delete_message(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_bot = message.from_user.is_bot

    # Check if the user is the group owner or an admin
    administrators = []
    async for m in bot.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        administrators.append(m.user.id)

    # If the user is an admin or a bot with admin permissions, don't delete the message
    if user_id in administrators and not is_bot:
        return

    # Check if the group has a delete time set
    group = await groups.find_one({"group_id": chat_id})
    if not group:
        return

    delete_time = int(group["delete_time"])

    try:
        # Delete the message
        await asyncio.sleep(delete_time)
        await message.delete()
    except Exception as e:
        print(f"An error occurred: {e}/nGroup ID: {chat_id}")    


# Flask configuration
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}", code=302)

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.run()    
