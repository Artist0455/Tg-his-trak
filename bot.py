import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackContext
from telegram.ext import filters
import csv
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest

# Configuration
BOT_TOKEN = "8244179451:AAHHEGodxWX51iWPnbdM2pggIISRISrQeRc"
TELEGRAM_API_ID = 25136703
TELEGRAM_API_HASH = "accfaf5ecd981c67e481328515c39f89"

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user sessions
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    welcome_message = """
🤖 **Telegram Group Manager Bot**

Available Commands:
/start - Show this menu
/add_members - Add members to group from CSV
/list_members - List members from a group
/help - Get help

**Note:** This bot helps manage Telegram groups efficiently.
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when the command /help is issued."""
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
    await update.message.reply_text(help_text)

async def add_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the process of adding members from CSV."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {'action': 'waiting_for_csv'}
    
    await update.message.reply_text(
        "📤 Please send me a CSV file with user data in this format:\n\n"
        "username,user_id,access_hash\n"
        "example_user,123456789,1234567890123456789\n\n"
        "Or send /cancel to cancel this operation."
    )

async def list_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the process of listing group members."""
    user_id = update.effective_user.id
    user_sessions[user_id] = {'action': 'list_members'}
    
    await update.message.reply_text(
        "👥 I'll help you list members from a group.\n"
        "Please make sure I'm added as admin in the target group.\n\n"
        "Starting member scraping..."
    )
    
    # Process in background
    await process_list_members(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the current operation."""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("❌ Operation cancelled.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle CSV document upload."""
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ Please start with /add_members first.")
        return
    
    if user_sessions[user_id].get('action') != 'waiting_for_csv':
        return
    
    document = update.message.document
    file_name = document.file_name
    
    if not file_name or not file_name.endswith('.csv'):
        await update.message.reply_text("❌ Please send a CSV file.")
        return
    
    await update.message.reply_text("🔄 Processing your CSV file...")
    
    try:
        # Download the file
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{user_id}_{file_name}"
        await file.download_to_drive(file_path)
        
        user_sessions[user_id]['csv_file'] = file_path
        
        # Process the CSV
        await process_csv_file(update, context, user_id)
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        await update.message.reply_text("❌ Error downloading file.")

async def process_csv_file(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Process the uploaded CSV file."""
    try:
        csv_file = user_sessions[user_id]['csv_file']
        
        # Read CSV file
        users = []
        with open(csv_file, encoding='UTF-8') as f:
            rows = csv.reader(f, delimiter=",", lineterminator="\n")
            next(rows, None)  # Skip header
            for row in rows:
                if len(row) >= 3 and row[0] and row[1] and row[2]:
                    try:
                        user = {
                            'username': row[0],
                            'id': int(row[1]),
                            'access_hash': int(row[2])
                        }
                        users.append(user)
                    except ValueError:
                        continue
        
        if not users:
            await update.message.reply_text("❌ No valid users found in CSV file.")
            return
        
        await update.message.reply_text(f"📊 Found {len(users)} valid users in CSV.")
        
        # Show sample of users
        sample_text = "Sample users from your CSV:\n"
        for user in users[:3]:  # Show first 3 users
            sample_text += f"👤 {user['username']} (ID: {user['id']})\n"
        
        await update.message.reply_text(sample_text)
        
        # Store users in session for later use
        user_sessions[user_id]['users'] = users
        
        await update.message.reply_text(
            "✅ CSV processed successfully!\n"
            "Now use /start_add to begin adding members to group (feature in development)."
        )
        
        # Cleanup
        import os
        if os.path.exists(csv_file):
            os.remove(csv_file)
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        await update.message.reply_text("❌ Error processing CSV file.")

async def process_list_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process listing members from a group."""
    try:
        user_id = update.effective_user.id
        
        await update.message.reply_text("🔄 Connecting to Telegram...")
        
        # Initialize Telegram Client
        with TelegramClient(f"session_{user_id}", TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
            await update.message.reply_text("🔍 Fetching your groups...")
            
            chats = client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=50,
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
                await update.message.reply_text("❌ No groups found where you're admin.")
                return
            
            # Use first group for demo
            target_group = groups[0]
            await update.message.reply_text(f"📋 Fetching members from: {target_group.title}")
            
            members = client.get_participants(target_group, limit=50)  # Reduced limit for stability
            
            # Create CSV
            csv_file = f"members_{user_id}.csv"
            with open(csv_file, "w", encoding='UTF-8', newline='') as f:
                writer = csv.writer(f, delimiter=",", lineterminator="\n")
                writer.writerow(['username', 'user_id', 'access_hash', 'name'])
                for user in members:
                    username = user.username if user.username else ""
                    first_name = user.first_name if user.first_name else ""
                    last_name = user.last_name if user.last_name else ""
                    name = f"{first_name} {last_name}".strip()
                    writer.writerow([username, user.id, user.access_hash, name])
            
            # Send file back to user
            await update.message.reply_text(f"✅ Found {len(members)} members. Sending CSV...")
            
            with open(csv_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"members_{target_group.title}.csv",
                    caption=f"📊 {len(members)} members from {target_group.title}"
                )
            
            # Cleanup
            import os
            if os.path.exists(csv_file):
                os.remove(csv_file)
                
            # Clear session
            if user_id in user_sessions:
                del user_sessions[user_id]
                
    except Exception as e:
        logger.error(f"Error in process_list_members: {e}")
        await update.message.reply_text("❌ An error occurred while fetching members.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    user_id = update.effective_user.id
    
    # Check if user has active session
    if user_id in user_sessions:
        action = user_sessions[user_id].get('action')
        if action == 'waiting_for_csv':
            await update.message.reply_text("📤 I'm waiting for a CSV file. Please send a CSV file or /cancel to cancel.")
            return
    
    await update.message.reply_text("Send /start to see available commands.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_members", add_members))
    application.add_handler(CommandHandler("list_members", list_members))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Document handler for CSV files
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("🤖 Bot is running...")
    print("Press Ctrl+C to stop")
    application.run_polling()

if __name__ == '__main__':
    main()
