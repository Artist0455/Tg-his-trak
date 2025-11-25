from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Tumhare credentials directly use karo
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

print("🤖 Bot starting...")
print(f"📱 API_ID: {API_ID}")
print(f"🔑 API_HASH: {API_HASH}")
print(f"🤖 BOT_TOKEN: {BOT_TOKEN}")

# Bot initialize karo
app = Client(
    "my_sangmata_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database setup - simple and working
def init_db():
    conn = sqlite3.connect('sangmata.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_history
                 (user_id INTEGER, name TEXT, username TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()
    print("✅ Database ready")

init_db()

# /start command - yeh pakka kaam karega
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    print(f"🎯 Start command received from {message.from_user.id}")
    
    welcome_msg = """
🚀 **SangMata Bot Started!**

I can track username and name history of Telegram users.

**Available Commands:**
• /start - Show this message
• /history - Your name history  
• /find [user_id] - Find user's history
• /help - Help guide

**How to use:**
Just add me to any group and I'll start tracking!
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url="http://t.me/SangMataTracker_Bot?startgroup=true")],
        [InlineKeyboardButton("📞 Support", url="https://t.me/YourChannel")]
    ])
    
    await message.reply_text(welcome_msg, reply_markup=keyboard)
    print(f"✅ Welcome sent to {message.from_user.id}")

# /help command
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    help_text = """
📖 **Help Guide**

**Commands:**
• /start - Start the bot
• /history - View your name history
• /find [user_id] - Find any user's history
• /help - This message

**Examples:**
• /find 123456789
• /history

**Note:** Bot ko group mein add karo tracking ke liye!
    """
    await message.reply_text(help_text)

# /history command - tumhara apna history
@app.on_message(filters.command("history"))
async def history_cmd(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    print(f"📜 History requested by {user_id}")
    
    conn = sqlite3.connect('sangmata.db')
    c = conn.cursor()
    
    c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15", (user_id,))
    records = c.fetchall()
    conn.close()
    
    if records:
        history_msg = f"📜 **Name History for {user_name}**\n\n"
        
        for i, (name, username, time) in enumerate(records, 1):
            history_msg += f"**{i}. 👤 {name}**\n"
            history_msg += f"   📱 @{username}\n"
            history_msg += f"   🕐 {time}\n\n"
        
        await message.reply_text(history_msg)
        print(f"✅ History sent to {user_id}")
    else:
        await message.reply_text("❌ No history found for your account!")

# /find command - kisi aur ka history dekho
@app.on_message(filters.command("find"))
async def find_cmd(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** `/find 123456789`")
        return
    
    try:
        target_id = int(message.command[1])
    except:
        await message.reply_text("❌ User ID must be a number!")
        return
    
    print(f"🔍 Finding history for {target_id}")
    
    conn = sqlite3.connect('sangmata.db')
    c = conn.cursor()
    
    c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15", (target_id,))
    records = c.fetchall()
    conn.close()
    
    if records:
        history_msg = f"📜 **Name History for User ID:** `{target_id}`\n\n"
        
        for i, (name, username, time) in enumerate(records, 1):
            history_msg += f"**{i}. 👤 {name}**\n"
            history_msg += f"   📱 @{username}\n"
            history_msg += f"   🕐 {time}\n\n"
        
        await message.reply_text(history_msg)
        print(f"✅ History found for {target_id}")
    else:
        await message.reply_text(f"❌ No history found for user ID `{target_id}`")

# User tracking - har message pe track karo
@app.on_message(filters.all)
async def track_users(client, message):
    if not message.from_user:
        return
    
    user = message.from_user
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "No Username"
    
    conn = sqlite3.connect('sangmata.db')
    c = conn.cursor()
    
    # Last record dekho
    c.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    last_record = c.fetchone()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if last_record:
        last_name, last_username = last_record
        if full_name != last_name or username != last_username:
            # Change detect hua hai
            c.execute("INSERT INTO user_history VALUES (?, ?, ?, ?)", 
                     (user_id, full_name, username, current_time))
            conn.commit()
            print(f"🔄 Change detected: {user_id} - {full_name} (@{username})")
    else:
        # New user
        c.execute("INSERT INTO user_history VALUES (?, ?, ?, ?)", 
                 (user_id, full_name, username, current_time))
        conn.commit()
        print(f"👤 New user: {user_id} - {full_name} (@{username})")
    
    conn.close()

# Bot start karne se pehle
print("🚀 Starting bot...")
print("✅ All handlers ready")
print("🎯 Bot is now running!")

# Bot run karo
app.run()
