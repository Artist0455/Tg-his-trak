from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Tumhare credentials
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

print("🤖 Bot starting with your credentials...")
print("📱 API_ID:", API_ID)
print("🔑 API_HASH:", API_HASH)
print("🤖 BOT_TOKEN:", BOT_TOKEN[:10] + "..." + BOT_TOKEN[-5:])

# Bot initialize karo
app = Client(
    "sangmata_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database setup - improved
def init_db():
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  name TEXT,
                  username TEXT, 
                  timestamp TEXT)''')
    
    # Test ke liye kuch sample data add karo
    c.execute("SELECT COUNT(*) FROM user_history")
    count = c.fetchone()[0]
    
    if count == 0:
        # Sample data add karo testing ke liye
        sample_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO user_history (user_id, name, username, timestamp) VALUES (?, ?, ?, ?)",
                 (123456789, "Test User", "testuser", sample_time))
        print("✅ Sample data added for testing")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

# /start command - working
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user = message.from_user
    print(f"🎯 Start from: {user.id} - {user.first_name}")
    
    # User ko automatically track karo
    await track_user(user)
    
    welcome_msg = f"""
👋 **Hello {user.first_name}!**

🤖 **SangMata Bot** - Name History Tracker

I track and display username/name change history of Telegram users.

**📋 Commands:**
• /start - Start bot
• /history - Your name history  
• /find [user_id] - Find any user's history
• /help - Help guide
• /test - Test if bot is working

**🚀 Usage:**
1. Add me to any group
2. I'll automatically track name changes
3. Use /history to see your history
4. Use /find to see others' history

**Example:** `/find 123456789`
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url="http://t.me/SangMataTracker_Bot?startgroup=true")],
        [InlineKeyboardButton("📊 Check History", callback_data="history")],
        [InlineKeyboardButton("🔍 Find User", callback_data="find")]
    ])
    
    await message.reply_text(welcome_msg, reply_markup=keyboard)

# /test command - bot working hai ya nahi check karo
@app.on_message(filters.command("test"))
async def test_cmd(client, message):
    user = message.from_user
    await message.reply_text(f"✅ **Bot is Working!**\n\nYour ID: `{user.id}`\nYour Name: `{user.first_name}`\nUsername: `@{user.username or 'No Username'}`")
    print(f"✅ Test command from {user.id}")

# /help command
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    help_text = """
🆘 **Help Guide**

**📋 Commands:**
• /start - Start the bot
• /history - View your name history
• /find [user_id] - Find user's history
• /test - Test bot functionality
• /help - This message

**🔍 Examples:**
• `/find 123456789` - Find history for user ID 123456789
• `/history` - See your own history

**💡 Tips:**
- Add bot to group for automatic tracking
- User ID must be a number
- Bot will track all users in the group
    """
    await message.reply_text(help_text)

# User tracking function
async def track_user(user):
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "No Username"
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Pehle check karo user already exists ya nahi
        c.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        last_record = c.fetchone()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if last_record:
            last_name_db, last_username_db = last_record
            if full_name != last_name_db or username != last_username_db:
                # Change detect hua hai
                c.execute("INSERT INTO user_history (user_id, name, username, timestamp) VALUES (?, ?, ?, ?)", 
                         (user_id, full_name, username, current_time))
                conn.commit()
                print(f"🔄 Change: {user_id} - '{last_name_db}'→'{full_name}', '@{last_username_db}'→'@{username}'")
        else:
            # New user - pehli baar track ho raha hai
            c.execute("INSERT INTO user_history (user_id, name, username, timestamp) VALUES (?, ?, ?, ?)", 
                     (user_id, full_name, username, current_time))
            conn.commit()
            print(f"👤 New: {user_id} - {full_name} (@{username})")
            
    except Exception as e:
        print(f"❌ Tracking error: {e}")
    finally:
        conn.close()

# /history command - tumhara apna history
@app.on_message(filters.command("history"))
async def history_cmd(client, message):
    user = message.from_user
    user_id = user.id
    
    print(f"📜 History requested by {user_id}")
    
    # Pehle current user ko track karo
    await track_user(user)
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (user_id,))
        records = c.fetchall()
        
        if records:
            history_msg = f"📜 **Name History for {user.first_name}**\n\n"
            
            for i, (name, username, time) in enumerate(records, 1):
                history_msg += f"**{i}. 👤 {name}**\n"
                history_msg += f"   📱 @{username}\n" 
                history_msg += f"   🕐 {time}\n\n"
            
            await message.reply_text(history_msg)
            print(f"✅ History sent to {user_id} - {len(records)} records")
        else:
            await message.reply_text("❌ No history found! Try changing your name or username first.")
            
    except Exception as e:
        await message.reply_text("❌ Error getting history")
        print(f"❌ History error: {e}")
    finally:
        conn.close()

# /find command - kisi aur ka history dekho
@app.on_message(filters.command("find"))
async def find_cmd(client, message):
    user = message.from_user
    
    if len(message.command) < 2:
        await message.reply_text("""
❌ **Usage:** `/find USER_ID`

**Examples:**
• `/find 123456789`
• `/find 5511953244`
        """)
        return
    
    try:
        target_id = int(message.command[1])
    except:
        await message.reply_text("❌ User ID must be a number!")
        return
    
    print(f"🔍 {user.id} finding history for {target_id}")
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20", (target_id,))
        records = c.fetchall()
        
        if records:
            history_msg = f"📜 **History for User ID:** `{target_id}`\n\n"
            
            for i, (name, username, time) in enumerate(records, 1):
                history_msg += f"**{i}. 👤 {name}**\n"
                history_msg += f"   📱 @{username}\n"
                history_msg += f"   🕐 {time}\n\n"
            
            await message.reply_text(history_msg)
            print(f"✅ History found for {target_id} - {len(records)} records")
        else:
            await message.reply_text(f"❌ No history found for user ID `{target_id}`\n\nTry this ID for testing: `123456789`")
            
    except Exception as e:
        await message.reply_text("❌ Error finding user history")
        print(f"❌ Find error: {e}")
    finally:
        conn.close()

# Har message pe track karo
@app.on_message(filters.all)
async def track_all_messages(client, message):
    if message.from_user:
        await track_user(message.from_user)

# Callback queries handle karo
@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    user = callback_query.from_user
    data = callback_query.data
    
    if data == "history":
        await callback_query.message.edit_text("🔄 Getting your history...")
        # Simulate history command
        await history_cmd(client, callback_query.message)
    elif data == "find":
        await callback_query.message.edit_text("🔍 Use `/find USER_ID` to find any user's history\n\nExample: `/find 123456789`")
    
    await callback_query.answer()

print("=" * 50)
print("🚀 BOT STARTING...")
print("✅ Database Ready")
print("✅ Handlers Registered") 
print("✅ Credentials Loaded")
print("🎯 Bot is NOW RUNNING!")
print("=" * 50)

# Bot run karo
app.run()
