from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Configuration - Environment variables se lega
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Bot initialize karega
app = Client("sangmata_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# User changes track karega
@app.on_message(filters.private | filters.group)
async def track_user_changes(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "None"

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    # Last record check karega
    cursor.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY change_time DESC LIMIT 1", (user_id,))
    result = cursor.fetchone()

    if result:
        last_name, last_username = result
        if full_name != last_name or username != last_username:
            # Naya record add karega agar change hua hai
            cursor.execute("""
                INSERT INTO user_history (user_id, name, username, change_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, datetime.now()))
    else:
        # Naya user hai toh pehla record banayega
        cursor.execute("""
            INSERT INTO user_history (user_id, name, username, change_time)
            VALUES (?, ?, ?, ?)
        """, (user_id, full_name, username, datetime.now()))

    conn.commit()
    conn.close()

# Start command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome to SangMata Bot!\n\n"
        "I track username and name changes of Telegram users.\n\n"
        "**Commands:**\n"
        "• `/history` - View your name history\n"
        "• `/find <user_id>` - Find user's history\n\n"
        "**Privacy:** Only stores name/username changes",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Source Code", url="https://github.com/yourusername/sangmata-bot")]
        ])
    )

# History command
@app.on_message(filters.command("history"))
async def view_history(client: Client, message: Message):
    user_id = message.from_user.id

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
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
        return

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
        history = f"📜 **Name History for User ID {user_id}:**\n\n"
        for i, (name, username, time) in enumerate(records, 1):
            history += f"**{i}.** Name: `{name}`\n"
            history += f"    Username: `{username}`\n"
            history += f"    Time: `{time}`\n\n"
        await message.reply_text(history)
    else:
        await message.reply_text(f"No history found for user ID `{user_id}`.")

# Bot start hone par
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
        f"• Database: `history.db`"
    )

# Initialize database when bot starts
with app:
    init_db()
    print("✅ Database initialized successfully!")
    print("🤖 Bot is ready!")

# Web server for Render
from flask import Flask
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 SangMata Bot is running!"

if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=5000)