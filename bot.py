import os
import requests
import re
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# YOUR CREDENTIALS
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAER_dLg1rQT2E9wuE5XRqDumNzuBWU1JPE"

# API ENDPOINT
API_URL = "https://mazid-download-api.vercel.app/"

print("🚀 Starting Advanced Instagram Downloader Bot...")

app = Client(
    "instagram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

class InstagramDownloader:
    def __init__(self):
        self.api_url = API_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def download_reels(self, url):
        """Download Instagram Reels using API"""
        try:
            # API call
            api_endpoint = f"{self.api_url}instagram"
            params = {"url": url}
            
            response = requests.get(api_endpoint, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return {"error": f"API returned status code: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"API Error: {str(e)}"}
    
    async def get_media_links(self, data):
        """Extract media links from API response"""
        try:
            # Check different possible response formats
            if data.get('url'):
                return [data['url']]
            elif data.get('video_url'):
                return [data['video_url']]
            elif data.get('media'):
                if isinstance(data['media'], list):
                    return data['media']
                else:
                    return [data['media']]
            elif data.get('urls'):
                return data['urls']
            else:
                # Try to find any video/photo URLs in the response
                media_links = []
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith(('http', 'https')):
                        if any(ext in value for ext in ['.mp4', '.jpg', '.jpeg', '.png']):
                            media_links.append(value)
                return media_links if media_links else None
                
        except Exception as e:
            return None

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "🤖 **Advanced Instagram Downloader**\n\n"
        "I can download:\n"
        "• 📹 Instagram Reels\n"
        "• 📸 Instagram Posts\n"
        "• 🎬 Instagram Stories\n"
        "• 📱 IGTV Videos\n\n"
        "**How to use:**\n"
        "Just send me any Instagram link!\n\n"
        "**Examples:**\n"
        "• Reels: `https://instagram.com/reel/ABC123/`\n"
        "• Posts: `https://instagram.com/p/XYZ789/`\n"
        "• Stories: `https://instagram.com/stories/username/123/`\n\n"
        "Made with ❤️ for Telegram"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "📖 **Help Guide**\n\n"
        "**Supported Links:**\n"
        "• Reels, Posts, Stories, IGTV\n"
        "• Public accounts only\n\n"
        "**How to download:**\n"
        "1. Copy Instagram link\n"
        "2. Paste here\n"
        "3. Wait for download\n\n"
        "**Features:**\n"
        "• High quality downloads\n"
        "• Fast processing\n"
        "• Multiple formats support\n\n"
        "Send me a link to get started! 🚀"
    )

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+'))
async def download_instagram(client, message: Message):
    link = message.matches[0].group(0)
    
    # Show processing message
    progress_msg = await message.reply_text("🔄 Processing your Instagram link...")
    
    downloader = InstagramDownloader()
    
    try:
        # Get data from API
        api_data = await downloader.download_reels(link)
        
        if "error" in api_data:
            await progress_msg.edit_text(f"❌ API Error: {api_data['error']}")
            return
        
        # Extract media links
        media_links = await downloader.get_media_links(api_data)
        
        if not media_links:
            await progress_msg.edit_text("❌ No media found in the response. Trying alternative method...")
            # Fallback to alternative method
            await fallback_download(client, message, link, progress_msg)
            return
        
        # Download and send media
        success_count = 0
        total_media = len(media_links)
        
        await progress_msg.edit_text(f"📦 Found {total_media} media files. Downloading...")
        
        for i, media_url in enumerate(media_links):
            try:
                if media_url.endswith('.mp4') or 'video' in media_url.lower():
                    # It's a video
                    caption = f"🎬 **Instagram Reel**\n\n✅ Downloaded via @InstaReelsDownloaderBot\n📊 Quality: HD\n🔢 Item: {i+1}/{total_media}"
                    
                    await message.reply_video(
                        media_url,
                        caption=caption,
                        supports_streaming=True,
                        reply_to_message_id=message.id
                    )
                    success_count += 1
                    
                else:
                    # It's a photo
                    caption = f"📸 **Instagram Post**\n\n✅ Downloaded via @InstaReelsDownloaderBot\n🔢 Item: {i+1}/{total_media}"
                    
                    await message.reply_photo(
                        media_url,
                        caption=caption,
                        reply_to_message_id=message.id
                    )
                    success_count += 1
                
                # Small delay between sends
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error sending media {i+1}: {e}")
                continue
        
        if success_count > 0:
            await progress_msg.edit_text(f"✅ Successfully downloaded {success_count}/{total_media} files!")
        else:
            await progress_msg.edit_text("❌ Failed to download any media. Trying alternative method...")
            await fallback_download(client, message, link, progress_msg)
            
    except Exception as e:
        print(f"Main error: {e}")
        await progress_msg.edit_text("❌ Download failed. Trying alternative method...")
        await fallback_download(client, message, link, progress_msg)

async def fallback_download(client, message, link, progress_msg):
    """Fallback download method using DDInstagram"""
    try:
        await progress_msg.edit_text("🔄 Trying alternative download method...")
        
        # Use DDInstagram as fallback
        dd_url = link.replace("instagram.com", "ddinstagram.com")
        dd_url = dd_url.replace("www.", "")
        
        # Determine content type
        if "/reel/" in link or "/p/" in link:
            try:
                await message.reply_video(
                    dd_url,
                    caption="🎬 **Instagram Video**\n\n✅ Downloaded via Alternative Method\n📊 Quality: Standard",
                    supports_streaming=True,
                    reply_to_message_id=message.id
                )
                await progress_msg.delete()
                return
            except:
                pass
        
        # Try as photo
        try:
            await message.reply_photo(
                dd_url,
                caption="📸 **Instagram Photo**\n\n✅ Downloaded via Alternative Method",
                reply_to_message_id=message.id
            )
            await progress_msg.delete()
            return
        except:
            pass
            
        await progress_msg.edit_text("❌ Sorry, couldn't download this content. Possible reasons:\n\n• Private account\n• Content removed\n• Invalid link\n• Server issue\n\nTry another public Instagram link!")
        
    except Exception as e:
        await progress_msg.edit_text("❌ All download methods failed. Please try again later.")

@app.on_message(filters.command("stats"))
async def stats_command(client, message: Message):
    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        "• **Status:** ✅ Running\n"
        "• **API:** Mazid Download API\n"
        "• **Version:** 2.0\n"
        "• **Support:** Reels, Posts, Stories\n"
        "• **Quality:** HD\n\n"
        "Bot is working perfectly! 🚀"
    )

@app.on_message(filters.command("donate"))
async def donate_command(client, message: Message):
    await message.reply_text(
        "❤️ **Support This Project**\n\n"
        "If you find this bot useful, consider supporting its development and maintenance:\n\n"
        "Your support helps cover:\n"
        "• Server costs\n"
        "• API expenses\n"
        "• Development time\n\n"
        "Thank you for your support! 🙏",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("☕ Buy Me a Coffee", url="https://buymeacoffee.com")],
            [InlineKeyboardButton("💰 Donate via PayPal", url="https://paypal.com")]
        ])
    )

if __name__ == '__main__':
    print("✅ Bot started successfully with Mazid API!")
    app.run()
