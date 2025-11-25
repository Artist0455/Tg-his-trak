from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Configuration with your credentials
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

# Initialize bot
app = Client(
    "sangmata_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database setup
def init_database():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            username TEXT,
            change_time TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_id ON user_history(user_id)
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

# Initialize database on startup
init_database()

# Track user data changes
@app.on_message(filters.private | filters.group)
async def track_user_changes(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "No Username"

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
        # Get last record
        cursor.execute("""
            SELECT name, username FROM user_history 
            WHERE user_id = ? 
            ORDER BY change_time DESC LIMIT 1
        """, (user_id,))
        result = cursor.fetchone()

        should_insert = False
        if result:
            last_name, last_username = result
            if full_name != last_name or username != last_username:
                should_insert = True
                print(f"🔄 Change detected for user {user_id}")
        else:
            should_insert = True
            print(f"👤 New user tracked: {user_id}")

        if should_insert:
            cursor.execute("""
                INSERT INTO user_history (user_id, name, username, change_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, datetime.now()))
            conn.commit()
            print(f"✅ Recorded: {full_name} (@{username})")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

# Start command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    welcome_text = """
🤖 **Welcome to SangMata Bot!**

I track and display history of username and name changes on Telegram.

**Commands:**
• `/start` - Show this message
• `/history` - View your name history
• `/find <user_id>` - Find user history
• `/help` - Get help

**How to use:**
Add me to your group or chat with me privately!
    """
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Add to Group", url="http://t.me/SangMataTracker_Bot?startgroup=true")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/YourSupport")],
        ])
    )
    print(f"✅ Start command used by {message.from_user.id}")

# Help command
@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    help_text = """
🆘 **Help Guide**

**Commands:**
• `/start` - Start the bot
• `/history` - View your history
• `/find <user_id>` - Find user history
• `/help` - This message

**Example:**
`/find 123456789` - Find history for user ID 123456789

**Note:** I need to be in the group to track users!
    """
    await message.reply_text(help_text)

# History command
@app.on_message(filters.command("history"))
async def view_history(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, username, change_time
            FROM user_history
            WHERE user_id = ?
            ORDER BY change_time DESC
            LIMIT 20
        """, (user_id,))
        records = cursor.fetchall()
        
        if records:
            history_text = f"📜 **History for {user_name}:**\n\n"
            for i, (name, username, time) in enumerate(records, 1):
                history_text += f"**{i}.** 👤 `{name}`\n"
                history_text += f"    📱 `@{username}`\n"
                history_text += f"    🕐 `{time}`\n\n"
            
            await message.reply_text(history_text)
            print(f"✅ History sent to {user_id}")
        else:
            await message.reply_text("❌ No history found for your account.")
            
    except Exception as e:
        await message.reply_text("❌ Error retrieving history.")
        print(f"❌ History error: {e}")
    finally:
        conn.close()

# Find command
@app.on_message(filters.command("find"))
async def find_user_history(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/find 123456789`")
        return

    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ User ID must be a number!")
        return

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, username, change_time
            FROM user_history
            WHERE user_id = ?
            ORDER BY change_time DESC
            LIMIT 20
        """, (user_id,))
        records = cursor.fetchall()

        if records:
            history_text = f"📜 **History for User ID:** `{user_id}`\n\n"
            for i, (name, username, time) in enumerate(records, 1):
                history_text += f"**{i}.** 👤 `{name}`\n"
                history_text += f"    📱 `@{username}`\n"
                history_text += f"    🕐 `{time}`\n\n"
            
            await message.reply_text(history_text)
            print(f"✅ Found history for {user_id}")
        else:
            await message.reply_text(f"❌ No history found for user ID `{user_id}`.")
            
    except Exception as e:
        await message.reply_text("❌ Error retrieving user history.")
        print(f"❌ Find error: {e}")
    finally:
        conn.close()

# Test command to check if bot is alive
@app.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    await message.reply_text("🏓 **Pong!** Bot is alive and working!")
    print(f"✅ Ping from {message.from_user.id}")

print("🤖 Starting SangMata Bot...")
print("✅ Credentials loaded")
print("✅ Database ready")
print("🚀 Bot is running...")

app.run()
