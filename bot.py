import os
import re
import asyncio
import requests
import bs4
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuration from environment variables
API_ID = int(os.getenv("API_ID", "25136703"))
API_HASH = os.getenv("API_HASH", "accfaf5ecd981c67e481328515c39f89")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244179451:AAER_dLg1rQT2E9wuE5XRqDumNzuBWU1JPE")
LOG_GROUP = os.getenv("LOG_GROUP", "")
DUMP_GROUP = os.getenv("DUMP_GROUP", "")

# Headers for requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://saveig.app",
    "Connection": "keep-alive",
    "Referer": "https://saveig.app/en",
}

print("🚀 Starting Instagram Bot...")
print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
print(f"🔑 API ID: {API_ID}")

# Initialize Pyrogram Client
app = Client(
    "instagram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+') & filters.incoming)
async def instagram_downloader(client, message: Message):
    link = message.matches[0].group(0)
    print(f"📥 Received Instagram link: {link}")
    
    try:
        # Send processing message
        m = await message.reply("🔄 Processing your Instagram link...")
        
        # Method 1: Try ddinstagram.com first
        url = link.replace("instagram.com", "ddinstagram.com")
        url = url.replace("==", "%3D%3D")
        
        try:
            print("🔧 Trying ddinstagram method...")
            if url.endswith("="):
                dump_file = await message.reply_video(url[:-1], caption="✅ Downloaded via @InstaDownloaderBot")
            else:
                dump_file = await message.reply_video(url, caption="✅ Downloaded via @InstaDownloaderBot")
            
            if DUMP_GROUP:
                await dump_file.copy(int(DUMP_GROUP))
            await m.delete()
            print("✅ Success with ddinstagram method")
            return
            
        except Exception as e:
            print(f"❌ ddinstagram failed: {e}")
            
            # Method 2: Use saveig.app API
            await m.edit("🔍 Trying alternative method...")
            
            if "/reel/" in url or "/p/" in url or "stories" in url:
                try:
                    print("🌐 Using saveig.app API...")
                    # Make API request to saveig.app
                    response = requests.post(
                        "https://saveig.app/api/ajaxSearch",
                        data={"q": link, "t": "media", "lang": "en"},
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        json_data = response.json()
                        print("📦 API response received")
                        
                        if 'data' in json_data:
                            # Extract all media links
                            media_links = re.findall(r'href="(https?://[^"]+)"', json_data['data'])
                            print(f"📷 Found {len(media_links)} media files")
                            
                            if media_links:
                                success_count = 0
                                for media_url in media_links[:5]:  # Limit to 5 media files
                                    try:
                                        if media_url.endswith(('.mp4', '.mov', '.avi')):
                                            sent_msg = await message.reply_video(
                                                media_url, 
                                                caption=f"🎥 Media {success_count + 1} | Downloaded via @InstaDownloaderBot"
                                            )
                                        else:
                                            sent_msg = await message.reply_photo(
                                                media_url,
                                                caption=f"📸 Photo {success_count + 1} | Downloaded via @InstaDownloaderBot"
                                            )
                                        
                                        success_count += 1
                                        
                                        # Forward to dump group if configured
                                        if DUMP_GROUP and success_count == 1:
                                            await sent_msg.copy(int(DUMP_GROUP))
                                            
                                        await asyncio.sleep(1)  # Delay between sends
                                        
                                    except Exception as media_error:
                                        print(f"❌ Media error: {media_error}")
                                        continue
                                
                                if success_count > 0:
                                    await m.delete()
                                    await message.reply(f"✅ Successfully downloaded {success_count} files!")
                                    return
                                else:
                                    await m.edit("❌ All media downloads failed")
                            else:
                                await m.edit("❌ No media links found in the response")
                        else:
                            await m.edit("❌ Invalid API response format")
                    else:
                        await m.edit(f"❌ API request failed with status {response.status_code}")
                        
                except Exception as api_error:
                    error_msg = f"API Error: {str(api_error)}"
                    print(f"❌ API Error: {api_error}")
                    await m.edit("❌ API service temporarily unavailable")
                    
                    if LOG_GROUP:
                        await client.send_message(int(LOG_GROUP), error_msg)
        
        # If all methods fail
        await m.edit("❌ Sorry, couldn't download this content. Possible reasons:\n• Private account\n• Invalid link\n• Server issue\n\nTry another link!")
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(f"💥 Critical error: {e}")
        await message.reply("❌ An internal error occurred. Please try again later.")
        
        # Log error if LOG_GROUP is set
        if LOG_GROUP:
            await client.send_message(int(LOG_GROUP), f"Error for {link}:\n{error_message}")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "🤖 **Instagram Downloader Bot**\n\n"
        "Send me any Instagram link and I'll download it for you!\n\n"
        "**Supported Links:**\n"
        "• 📹 Instagram Reels\n"
        "• 📸 Instagram Posts\n" 
        "• 🎬 Instagram Stories\n\n"
        "**How to use:**\n"
        "1. Copy Instagram link\n"
        "2. Paste here\n"
        "3. Wait for download\n\n"
        "Made with ❤️ for Telegram"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "📖 **Help Guide**\n\n"
        "**Supported Links:**\n"
        "• Reels: `https://instagram.com/reel/ABC123/`\n"
        "• Posts: `https://instagram.com/p/XYZ789/`\n"
        "• Stories: `https://instagram.com/stories/username/123/`\n\n"
        "**Features:**\n"
        "• Fast downloads\n"
        "• Multiple media support\n"
        "• High quality\n\n"
        "Just paste your link and enjoy! 🎉"
    )

@app.on_message(filters.command("status"))
async def status_command(client, message: Message):
    await message.reply_text("🤖 Bot is running perfectly! ✅")

if __name__ == "__main__":
    print("✅ Bot started successfully!")
    app.run()
