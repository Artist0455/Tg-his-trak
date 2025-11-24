from pyrogram import Client, filters
from pyrogram.types import Message
import sqlite3
import os
import asyncio
from datetime import datetime

print("🤖 Bot starting...")

# Your credentials directly
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

print(f"API_ID: {API_ID}")
print(f"BOT_TOKEN: {BOT_TOKEN}")

# Initialize bot
app = Client("sangmata", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Database setup
def init_db():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_history (
            user_id INTEGER,
            name TEXT,
            username TEXT,
            change_time TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database ready")

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    print(f"🎯 Start command from: {message.from_user.id}")
    await message.reply_text(
        "🚀 **SangMata Bot Active!**\n\n"
        "Available Commands:\n"
        "• /start - Bot info\n"
        "• /history - Your name history\n"
        "• /find <id> - Find user history\n"
        "• /stats - Bot stats\n\n"
        "✅ Bot is working!"
    )

# History command
@app.on_message(filters.command("history"))
async def history(client, message):
    user_id = message.from_user.id
    print(f"📜 History requested by: {user_id}")
    
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, username, change_time FROM user_history WHERE user_id = ? ORDER BY change_time DESC LIMIT 10", (user_id,))
    records = cursor.fetchall()
    conn.close()
    
    if records:
        text = "📜 **Your Name History:**\n\n"
        for name, username, time in records:
            text += f"• **Name:** `{name}`\n"
            text += f"  **Username:** `{username}`\n"
            text += f"  **Time:** `{time}`\n\n"
    else:
        text = "No history found for your account."
    
    await message.reply_text(text)

# Track name changes
@app.on_message(filters.private | filters.group)
async def track_names(client, message):
    try:
        user = message.from_user
        if not user:
            return
            
        user_id = user.id
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = user.username or "No Username"
        
        conn = sqlite3.connect("history.db")
        cursor = conn.cursor()
        
        # Check last record
        cursor.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY change_time DESC LIMIT 1", (user_id,))
        last = cursor.fetchone()
        
        if not last or last[0] != name or last[1] != username:
            cursor.execute("INSERT INTO user_history (user_id, name, username, change_time) VALUES (?, ?, ?, ?)",
                         (user_id, name, username, datetime.now()))
            print(f"📝 Recorded: {name} (@{username})")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

# Stats command
@app.on_message(filters.command("stats"))
async def stats(client, message):
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_history")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM user_history")
    records = cursor.fetchone()[0]
    conn.close()
    
    await message.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"• Users Tracked: `{users}`\n"
        f"• Total Records: `{records}`\n"
        f"• Status: `Active ✅`"
    )

print("🔄 Initializing bot...")

async def main():
    await app.start()
    print("✅ Bot started successfully!")
    
    init_db()
    
    me = await app.get_me()
    print(f"🤖 Bot Username: @{me.username}")
    print(f"🔗 Start Link: https://t.me/{me.username}")
    print("🟢 Bot is ready! Send /start to test")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
