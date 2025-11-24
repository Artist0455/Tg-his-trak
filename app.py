from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
import asyncio
from datetime import datetime
from flask import Flask
import threading

# Configuration - Tumhara data use karo
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

print("🚀 Starting SangMata Bot...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")
print(f"BOT_TOKEN: {BOT_TOKEN}")

# Flask app for web server
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 SangMata Bot is running!"

@web_app.route('/health')
def health():
    return "OK"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    web_app.run(host='0.0.0.0', port=port, debug=False)

# Telegram Bot
app = Client("sangmata_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Database setup
def init_db():
    try:
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
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database error: {e}")

# User changes tracker
@app.on_message(filters.private | filters.group)
async def track_user_changes(client: Client, message: Message):
    try:
        user = message.from_user
        if not user:
            return

        user_id = user.id
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = user.username or "None"

        conn = sqlite3.connect("history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY change_time DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()

        if result:
            last_name, last_username = result
            if full_name != last_name or username != last_username:
                cursor.execute("""
                    INSERT INTO user_history (user_id, name, username, change_time)
                    VALUES (?, ?, ?, ?)
                """, (user_id, full_name, username, datetime.now()))
                print(f"🔄 Change detected for user {user_id}")
        else:
            cursor.execute("""
                INSERT INTO user_history (user_id, name, username, change_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, datetime.now()))
            print(f"👤 New user added: {user_id}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Tracking error: {e}")

# Start command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome to SangMata Bot!\n\n"
        "I track username and name changes of Telegram users.\n\n"
        "**Commands:**\n"
        "• `/history` - View your name history\n"
        "• `/find <user_id>` - Find user's history\n"
        "• `/stats` - Bot statistics\n\n"
        "**Privacy:** Only stores name/username changes",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Check History", callback_data="history")]
        ])
    )
    print(f"✅ Start command from user: {message.from_user.id}")

# History command
@app.on_message(filters.command("history"))
async def view_history(client: Client, message: Message):
    user_id = message.from_user.id
    print(f"📜 History requested by: {user_id}")

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, username, change_time
        FROM user_history
        WHERE user_id = ?
        ORDER BY change_time DESC
        LIMIT 20
    """, (user_id,))
    records = cursor.fetchall()
    conn.close()

    if records:
        history = f"📜 **Name History for {message.from_user.first_name}:**\n\n"
        for i, (name, username, time) in enumerate(records, 1):
            history += f"**{i}.** Name: `{name}`\n"
            history += f"    Username: `{username}`\n"
            history += f"    Time: `{time}`\n\n"
        await message.reply_text(history)
    else:
        await message.reply_text("No history found for your account.")

# Find command
@app.on_message(filters.command("find"))
async def find_user_history(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a user ID.\nUsage: `/find 123456789`")
        return

    try:
        user_id = int(message.command[1])
        print(f"🔍 Find requested for user: {user_id}")

        conn = sqlite3.connect("history.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, username, change_time
            FROM user_history
            WHERE user_id = ?
            ORDER BY change_time DESC
            LIMIT 15
        """, (user_id,))
        records = cursor.fetchall()
        conn.close()

        if records:
            history = f"📜 **History for User {user_id}:**\n\n"
            for i, (name, username, time) in enumerate(records, 1):
                history += f"**{i}.** Name: `{name}`\n"
                history += f"    Username: `{username}`\n"
                history += f"    Time: `{time}`\n\n"
            await message.reply_text(history)
        else:
            await message.reply_text(f"No history found for user ID `{user_id}`.")
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")

# Stats command
@app.on_message(filters.command("stats"))
async def bot_stats(client: Client, message: Message):
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_history")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_history")
    total_records = cursor.fetchone()[0]
    
    conn.close()
    
    await message.reply_text(
        f"🤖 **Bot Statistics:**\n\n"
        f"• Total Users Tracked: `{total_users}`\n"
        f"• Total Records: `{total_records}`\n"
        f"• Status: `Online ✅`\n"
        f"• Database: `history.db`"
    )
    print("📊 Stats command executed")

# Callback query handler
@app.on_callback_query()
async def handle_callback(client, callback_query):
    if callback_query.data == "history":
        await callback_query.message.edit_text("Use `/history` command to view your name history.")

# Main function
async def main():
    print("🔄 Starting bot...")
    await app.start()
    print("✅ Bot started successfully!")
    
    # Initialize database
    init_db()
    
    # Get bot info
    me = await app.get_me()
    print(f"🤖 Bot Username: @{me.username}")
    print(f"🔗 Start Link: https://t.me/{me.username}")
    
    # Keep running
    print("🟢 Bot is now running and ready!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Start web server in background
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("🌐 Web server started")
    
    # Run bot
    asyncio.run(main())