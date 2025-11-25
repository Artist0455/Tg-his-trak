from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import sqlite3
import os
from datetime import datetime

# Tumhare credentials
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAFW8SLabiTyCuTge2fz5LL6VA5sNOH_3pQ"

print("🤖 Bot starting with real data tracking...")

# Bot initialize karo
app = Client(
    "sangmata_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database setup
def init_db():
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  name TEXT,
                  username TEXT, 
                  timestamp TEXT)''')
    conn.commit()
    conn.close()
    print("✅ Database ready for real data tracking")

init_db()

# User tracking function - improved
async def track_user(user):
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "No Username"
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Pehle check karo user ka last record kya hai
        c.execute("SELECT name, username FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        last_record = c.fetchone()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if last_record:
            last_name_db, last_username_db = last_record
            # Agar change hua hai toh naya record add karo
            if full_name != last_name_db or username != last_username_db:
                c.execute("INSERT INTO user_history (user_id, name, username, timestamp) VALUES (?, ?, ?, ?)", 
                         (user_id, full_name, username, current_time))
                conn.commit()
                print(f"🔄 Change detected: {user_id} - '{last_name_db}'→'{full_name}', '@{last_username_db}'→'@{username}'")
        else:
            # Pehli baar user track ho raha hai
            c.execute("INSERT INTO user_history (user_id, name, username, timestamp) VALUES (?, ?, ?, ?)", 
                     (user_id, full_name, username, current_time))
            conn.commit()
            print(f"👤 New user tracked: {user_id} - {full_name} (@{username})")
            
    except Exception as e:
        print(f"❌ Tracking error: {e}")
    finally:
        conn.close()

# /start command
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user = message.from_user
    print(f"🎯 Start from: {user.id} - {user.first_name}")
    
    # User ko track karo
    await track_user(user)
    
    welcome_msg = f"""
👋 **Hello {user.first_name}!**

🤖 **Real SangMata Bot** - Real Data Tracking

**Yeh Bot REAL DATA Track Karega:**
✅ Real username changes
✅ Real name changes  
✅ Real timestamp
❌ Fake data nahi

**📋 Commands:**
• /start - Start bot
• /history - Your REAL history  
• /find [user_id] - Find user's REAL history
• /myinfo - Your current info

**💡 Important:**
- Bot ko group mein add karo
- Users jab name/username change karenge tabhi history banega
- Abhi koi history nahi dikhega kyunki tracking abhi shuru hua hai
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url="http://t.me/SangMataTracker_Bot?startgroup=true")],
        [InlineKeyboardButton("📊 My History", callback_data="myhistory")],
    ])
    
    await message.reply_text(welcome_msg, reply_markup=keyboard)

# /myinfo command - current info dekho
@app.on_message(filters.command("myinfo"))
async def myinfo_cmd(client, message):
    user = message.from_user
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or "No Username"
    
    info_text = f"""
📱 **Your Current Info:**

**User ID:** `{user_id}`
**Full Name:** `{full_name}`
**Username:** `@{username}`
**First Name:** `{first_name}`
**Last Name:** `{last_name or 'None'}`

**💡 Tip:** 
Agar apna name ya username change karoge toh bot automatically track karega!
    """
    
    await message.reply_text(info_text)

# /history command - REAL history
@app.on_message(filters.command("history"))
async def history_cmd(client, message):
    user = message.from_user
    user_id = user.id
    
    print(f"📜 Real history requested by {user_id}")
    
    # Pehle current user ko track karo
    await track_user(user)
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 25", (user_id,))
        records = c.fetchall()
        
        if records:
            history_msg = f"📜 **Real History for {user.first_name}**\n\n"
            
            for i, (name, username, time) in enumerate(records, 1):
                history_msg += f"**{i}. 👤 {name}**\n"
                history_msg += f"   📱 @{username}\n" 
                history_msg += f"   🕐 {time}\n\n"
            
            # Agar sirf 1 record hai toh message different dikhao
            if len(records) == 1:
                history_msg += "**💡 Tip:** Name ya username change karo aur phir /history check karo!"
            
            await message.reply_text(history_msg)
            print(f"✅ Real history sent to {user_id} - {len(records)} records")
        else:
            await message.reply_text("""
❌ **No History Found Yet!**

**Kyun?** 
- Bot naya start hua hai
- Abhi tak koi name/username change nahi hua
- Tracking abhi shuru hua hai

**📝 Solution:**
1. Apna name ya username change karo
2. Phir /history check karo
3. Ya bot ko group mein add karo
            """)
            
    except Exception as e:
        await message.reply_text("❌ Error getting real history")
        print(f"❌ History error: {e}")
    finally:
        conn.close()

# /find command - REAL user data
@app.on_message(filters.command("find"))
async def find_cmd(client, message):
    user = message.from_user
    
    if len(message.command) < 2:
        await message.reply_text("""
❌ **Usage:** `/find USER_ID`

**Example:** `/find 5511953244`

**Note:** Sirf REAL data dikhega jo actually track hua hai
        """)
        return
    
    try:
        target_id = int(message.command[1])
    except:
        await message.reply_text("❌ User ID must be a number!")
        return
    
    print(f"🔍 {user.id} finding REAL history for {target_id}")
    
    conn = sqlite3.connect('sangmata.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        c.execute("SELECT name, username, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 25", (target_id,))
        records = c.fetchall()
        
        if records:
            history_msg = f"📜 **Real History for User ID:** `{target_id}`\n\n"
            
            for i, (name, username, time) in enumerate(records, 1):
                history_msg += f"**{i}. 👤 {name}**\n"
                history_msg += f"   📱 @{username}\n"
                history_msg += f"   🕐 {time}\n\n"
            
            await message.reply_text(history_msg)
            print(f"✅ Real history found for {target_id} - {len(records)} records")
        else:
            await message.reply_text(f"""
❌ **No Real History Found for** `{target_id}`

**Possible Reasons:**
- User ne abhi tak name/username change nahi kiya
- Bot ne user ko abhi tak track nahi kiya  
- User ID galat hai

**💡 Solution:**
- User ko bot ke saath interact karwao
- User apna name change kare
- Ya user ko group mein add karo jahan bot hai
            """)
            
    except Exception as e:
        await message.reply_text("❌ Error finding real user history")
        print(f"❌ Find error: {e}")
    finally:
        conn.close()

# Har message pe REAL tracking
@app.on_message(filters.all)
async def track_all_messages(client, message):
    if message.from_user:
        await track_user(message.from_user)

# Callback queries
@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    user = callback_query.from_user
    data = callback_query.data
    
    if data == "myhistory":
        await callback_query.message.edit_text("🔄 Getting your REAL history...")
        await history_cmd(client, callback_query.message)
    
    await callback_query.answer()

print("=" * 50)
print("🚀 REAL DATA BOT STARTING...")
print("✅ Only REAL data will be tracked")
print("✅ No fake data")
print("✅ Real user changes only")
print("🎯 Bot is NOW TRACKING REAL DATA!")
print("=" * 50)

# Bot run karo
app.run()
