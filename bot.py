from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, Dispatcher
import logging
import os
import csv
import time
import random
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import threading

# Initialize Flask App
app = Flask(__name__)

# Telegram Bot Configuration
BOT_TOKEN = "8244179451:AAHHEGodxWX51iWPnbdM2pggIISRISrQeRc"
TELEGRAM_API_ID = 25136703
TELEGRAM_API_HASH = "accfaf5ecd981c67e481328515c39f89"

# Initialize Telegram Bot
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user sessions
user_sessions = {}

# Start Command
def start(update, context):
    user_id = update.effective_user.id
    welcome_message = """
🤖 **Telegram Group Manager Bot**

Available Commands:
/start - Show this menu
/add_members - Add members to group from CSV
/list_members - List members from a group
/help - Get help

**Note:** This bot helps manage Telegram groups efficiently.
    """
    update.message.reply_text(welcome_message, parse_mode='Markdown')

# Help Command
def help_command(update, context):
    help_text = """
📖 **How to Use This Bot:**

1. **Add Members to Group:**
   - Use /add_members command
   - Send CSV file with user data
   - Select target group
   - Bot will add members automatically

2. **List Group Members:**
   - Use /list_members command
   - Select group to scrape
   - Get CSV with member details

📁 **CSV Format for Adding Members:**
username,user_id,access_hash

⚠️ **Important:**
- Follow Telegram's Terms of Service
- Don't spam users
- Respect privacy settings
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

# Add Members Command
def add_members(update, context):
    user_id = update.effective_user.id
    user_sessions[user_id] = {'action': 'waiting_for_csv'}
    
    update.message.reply_text(
        "📤 Please send me a CSV file with user data in this format:\n\n"
        "username,user_id,access_hash\n"
        "example_user,123456789,1234567890123456789\n\n"
        "Or send /cancel to cancel this operation."
    )

# List Members Command
def list_members(update, context):
    user_id = update.effective_user.id
    user_sessions[user_id] = {'action': 'list_members'}
    
    update.message.reply_text(
        "👥 I'll help you list members from a group.\n"
        "Please make sure I'm added as admin in the target group.\n\n"
        "Send /cancel to cancel this operation."
    )

# Cancel Command
def cancel(update, context):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    update.message.reply_text("❌ Operation cancelled.")

# Handle Document (CSV files)
def handle_document(update, context):
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        update.message.reply_text("❌ Please start with /add_members first.")
        return
    
    if user_sessions[user_id].get('action') != 'waiting_for_csv':
        return
    
    document = update.message.document
    file_name = document.file_name
    
    if not file_name.endswith('.csv'):
        update.message.reply_text("❌ Please send a CSV file.")
        return
    
    # Download the file
    file = context.bot.get_file(document.file_id)
    file_path = f"temp_{user_id}_{file_name}"
    file.download(file_path)
    
    user_sessions[user_id]['csv_file'] = file_path
    user_sessions[user_id]['action'] = 'processing_csv'
    
    # Start processing in background
    threading.Thread(target=process_add_members, args=(update, context, user_id)).start()

def process_add_members(update, context, user_id):
    try:
        session_data = user_sessions[user_id]
        csv_file = session_data['csv_file']
        
        update.message.reply_text("🔄 Processing your CSV file...")
        
        # Read CSV file
        users = []
        with open(csv_file, encoding='UTF-8') as f:
            rows = csv.reader(f, delimiter=",", lineterminator="\n")
            next(rows, None)  # Skip header
            for row in rows:
                if len(row) >= 3:
                    user = {
                        'username': row[0],
                        'id': int(row[1]),
                        'access_hash': int(row[2])
                    }
                    users.append(user)
        
        if not users:
            update.message.reply_text("❌ No valid users found in CSV file.")
            return
        
        update.message.reply_text(f"📊 Found {len(users)} users in CSV. Starting to add...")
        
        # Initialize Telegram Client
        with TelegramClient(f"session_{user_id}", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            # Get groups
            chats = client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=100,
                hash=0
            ))
            
            groups = []
            for chat in chats.chats:
                try:
                    if hasattr(chat, 'megagroup') and chat.megagroup:
                        groups.append(chat)
                except:
                    continue
            
            if not groups:
                update.message.reply_text("❌ No groups found where you're admin.")
                return
            
            # For demo, use first group (in real scenario, implement group selection)
            target_group = groups[0]
            target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
            
            success_count = 0
            error_count = 0
            
            for user in users[:5]:  # Limit to 5 for demo
                try:
                    if user['username']:
                        user_to_add = client.get_input_entity(user['username'])
                    else:
                        user_to_add = InputPeerUser(user['id'], user['access_hash'])
                    
                    client(InviteToChannelRequest(target_group_entity, [user_to_add]))
                    success_count += 1
                    time.sleep(10)  # Reduced delay for demo
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error adding user: {e}")
            
            # Cleanup
            import os
            if os.path.exists(csv_file):
                os.remove(csv_file)
            
            update.message.reply_text(
                f"✅ Operation completed!\n"
                f"Successfully added: {success_count}\n"
                f"Errors: {error_count}"
            )
    
    except Exception as e:
        logger.error(f"Error in process_add_members: {e}")
        update.message.reply_text("❌ An error occurred while processing your request.")

# Handle Messages
def handle_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id in user_sessions:
        if user_sessions[user_id].get('action') == 'list_members':
            threading.Thread(target=process_list_members, args=(update, context, user_id)).start()
        return
    
    update.message.reply_text("Send /start to see available commands.")

def process_list_members(update, context, user_id):
    try:
        update.message.reply_text("🔄 Fetching group members...")
        
        with TelegramClient(f"session_{user_id}", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            chats = client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=100,
                hash=0
            ))
            
            groups = []
            for chat in chats.chats:
                try:
                    if hasattr(chat, 'megagroup') and chat.megagroup:
                        groups.append(chat)
                except:
                    continue
            
            if not groups:
                update.message.reply_text("❌ No groups found.")
                return
            
            # Use first group for demo
            target_group = groups[0]
            members = client.get_participants(target_group, limit=50)  # Limit for demo
            
            # Create CSV
            csv_file = f"members_{user_id}.csv"
            with open(csv_file, "w", encoding='UTF-8') as f:
                writer = csv.writer(f, delimiter=",", lineterminator="\n")
                writer.writerow(['username', 'user_id', 'access_hash', 'name'])
                for user in members:
                    username = user.username if user.username else ""
                    first_name = user.first_name if user.first_name else ""
                    last_name = user.last_name if user.last_name else ""
                    name = f"{first_name} {last_name}".strip()
                    writer.writerow([username, user.id, user.access_hash, name])
            
            # Send file back to user
            with open(csv_file, 'rb') as f:
                context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=f"members_{target_group.title}.csv",
                    caption=f"📊 Members list for {target_group.title}"
                )
            
            # Cleanup
            import os
            if os.path.exists(csv_file):
                os.remove(csv_file)
                
            del user_sessions[user_id]
    
    except Exception as e:
        logger.error(f"Error in process_list_members: {e}")
        update.message.reply_text("❌ An error occurred while fetching members.")

# Error Handler
def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

# Set up handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("add_members", add_members))
dispatcher.add_handler(CommandHandler("list_members", list_members))
dispatcher.add_handler(CommandHandler("cancel", cancel))
dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_error_handler(error_handler)

# Webhook route for Render
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return 'OK'

# Health check route
@app.route('/')
def home():
    return '🤖 Telegram Group Manager Bot is Running!'

# Set webhook (for production)
@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    success = bot.set_webhook(webhook_url)
    if success:
        return f"Webhook set successfully: {webhook_url}"
    else:
        return "Failed to set webhook"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
