from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Configuration
API_ID = int(os.getenv("API_ID", ""))  # Get from environment variables
API_HASH = os.getenv("API_HASH", "")  # Get from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # Get from environment variables

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

# Initialize database on startup
init_database()

# Middleware: Track user data changes
@app.on_message(filters.private | filters.group)
async def track_user_changes(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "No Username"

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
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
        else:
            # New user
            should_insert = True

        if should_insert:
            cursor.execute("""
                INSERT INTO user_history (user_id, name, username, change_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, datetime.now()))
            conn.commit()
            
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# /start command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    welcome_text = """
🤖 **Welcome to SangMata Bot!**

I can track and display history of username and name changes on Telegram.

**Available Commands:**
• `/start` - Show this welcome message
• `/history` - View your name/username history
• `/find <user_id>` - Find history of other users
• `/help` - Get help information

**How to use:**
Simply add me to your group or chat with me privately, and I'll automatically track changes!
    """
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 GitHub", url="https://github.com")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/yourusername")],
            [InlineKeyboardButton("🔍 Try History", switch_inline_query_current_chat="history")]
        ])
    )

# /help command
@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    help_text = """
🆘 **Help Guide**

**Commands:**
• `/start` - Start the bot and see welcome message
• `/history` - View your personal name/username history
• `/find <user_id>` - Find history of specific user by ID
• `/help` - Show this help message

**Examples:**
• `/find 123456789` - Find history for user with ID 123456789

**Note:**
- The bot must be in the same group to track users
- User ID must be numeric
- Privacy settings may limit some functionality
    """
    await message.reply_text(help_text)

# /history command: View personal history
@app.on_message(filters.command("history"))
async def view_history(client: Client, message: Message):
    user_id = message.from_user.id

    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name, username, change_time
            FROM user_history
            WHERE user_id = ?
            ORDER BY change_time DESC
            LIMIT 50
        """, (user_id,))
        records = cursor.fetchall()
        
        if records:
            history = f"📜 **History of Changes for {message.from_user.first_name}:**\n\n"
            for i, (name, username, time) in enumerate(records, 1):
                history += f"**{i}.** Name: `{name}`\n"
                history += f"    Username: `{username}`\n"
                history += f"    Time: `{time}`\n\n"
            
            if len(history) > 4000:
                history = history[:4000] + "\n\n... (history truncated)"
                
            await message.reply_text(history)
        else:
            await message.reply_text("❌ No history found for your account.")
            
    except Exception as e:
        await message.reply_text("❌ Error retrieving history.")
        print(f"History error: {e}")
    finally:
        conn.close()

# /find command: View history of other users
@app.on_message(filters.command("find"))
async def find_user_history(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("""
❌ **Invalid Usage**

**Correct Usage:**
`/find <user_id>`

**Example:**
`/find 123456789`
        """)
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
            LIMIT 50
        """, (user_id,))
        records = cursor.fetchall()

        if records:
            history = f"📜 **History of Changes for User ID:** `{user_id}`\n\n"
            for i, (name, username, time) in enumerate(records, 1):
                history += f"**{i}.** Name: `{name}`\n"
                history += f"    Username: `{username}`\n"
                history += f"    Time: `{time}`\n\n"
            
            if len(history) > 4000:
                history = history[:4000] + "\n\n... (history truncated)"
                
            await message.reply_text(history)
        else:
            await message.reply_text(f"❌ No history found for user ID `{user_id}`.")
            
    except Exception as e:
        await message.reply_text("❌ Error retrieving user history.")
        print(f"Find error: {e}")
    finally:
        conn.close()

# Error handler
@app.on_errors()
async def error_handler(client: Client, error: Exception):
    print(f"Error occurred: {error}")

# Run the bot
if __name__ == "__main__":
    print("🤖 SangMata Bot is starting...")
    print("✅ Database initialized")
    print("✅ Handlers registered")
    print("🚀 Bot is now running...")
    app.run()