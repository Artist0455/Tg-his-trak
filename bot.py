import os
import requests
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuration
API_ID = int(os.getenv("API_ID", "25136703"))
API_HASH = os.getenv("API_HASH", "accfaf5ecd981c67e481328515c39f89")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244179451:AAER_dLg1rQT2E9wuE5XRqDumNzuBWU1JPE")

print("🚀 Starting Instagram Bot...")

app = Client("ig_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_instagram_media(instagram_url):
    """Get Instagram media using multiple working methods"""
    
    # Method 1: YouTubeDL Method (Most Reliable)
    try:
        ytdl_url = f"https://api.vevioz.com/api/button/mp3?url={instagram_url}"
        response = requests.get(ytdl_url, timeout=10)
        if response.status_code == 200:
            # Extract download links
            download_links = re.findall(r'href="(https?://[^"]+\.mp4)"', response.text)
            if download_links:
                return download_links[0]
    except:
        pass
    
    # Method 2: SnapTik Method
    try:
        snaptik_url = f"https://www.snaptik.app/abc.php?url={instagram_url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(snaptik_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Find video URL in response
            video_urls = re.findall(r'https?://[^"]+\.mp4[^"]*', response.text)
            if video_urls:
                return video_urls[0]
    except:
        pass
    
    # Method 3: SSSTik Method
    try:
        ssstik_url = f"https://ssstik.io/abc?url={instagram_url}"
        response = requests.get(ssstik_url, timeout=10)
        if response.status_code == 200:
            video_urls = re.findall(r'https://[^"]+\.mp4', response.text)
            if video_urls:
                return video_urls[0]
    except:
        pass
    
    # Method 4: Direct Instagram API (For public content)
    try:
        # Extract shortcode from URL
        shortcode = re.findall(r'instagram\.com/(?:p|reel)/([^/?]+)', instagram_url)
        if shortcode:
            shortcode = shortcode[0]
            graphql_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(graphql_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Extract video URL from GraphQL response
                media = data.get('graphql', {}).get('shortcode_media', {})
                if media.get('is_video'):
                    return media.get('video_url')
                else:
                    # For images
                    return media.get('display_url')
    except:
        pass
    
    return None

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+') & filters.incoming)
async def instagram_downloader(client, message: Message):
    link = message.matches[0].group(0)
    print(f"📥 Processing: {link}")
    
    m = await message.reply("🔄 Downloading your content...")
    
    try:
        # Get media URL
        media_url = get_instagram_media(link)
        
        if media_url:
            print(f"✅ Found media: {media_url}")
            
            # Send media based on type
            if media_url.endswith('.mp4') or 'video' in media_url:
                try:
                    await message.reply_video(
                        media_url, 
                        caption="✅ Downloaded successfully! 🎬\n\nBot by @YourBot",
                        supports_streaming=True
                    )
                    await m.delete()
                except Exception as video_error:
                    # If video fails, try as document
                    try:
                        await message.reply_document(
                            media_url,
                            caption="✅ Downloaded as file! 📁\n\nBot by @YourBot"
                        )
                        await m.delete()
                    except:
                        await message.reply(f"📥 Download Link:\n{media_url}")
                        await m.delete()
            else:
                # For images
                try:
                    await message.reply_photo(
                        media_url,
                        caption="✅ Downloaded successfully! 📸\n\nBot by @YourBot"
                    )
                    await m.delete()
                except:
                    await message.reply(f"📸 Image Link:\n{media_url}")
                    await m.delete()
                    
        else:
            # Final fallback - DDInstagram
            try:
                dd_url = link.replace("instagram.com", "ddinstagram.com")
                dd_url = dd_url.replace("www.", "")
                dd_url = dd_url.replace("reel/", "reel/")
                
                await message.reply_video(
                    dd_url,
                    caption="✅ Downloaded via alternative method! 🎬\n\nBot by @YourBot",
                    supports_streaming=True
                )
                await m.delete()
                
            except Exception as dd_error:
                print(f"DDInstagram failed: {dd_error}")
                await m.edit("❌ Sorry, this content cannot be downloaded. Possible reasons:\n\n• Private account\n• Content removed\n• Temporary issue\n\nTry another public Instagram link!")
                
    except Exception as e:
        print(f"Error: {e}")
        await m.edit("❌ Download failed. Please try again with a different link.")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "🤖 **Instagram Downloader Bot**\n\n"
        "I can download:\n"
        "• 📹 Instagram Reels\n"
        "• 📸 Instagram Posts\n" 
        "• 🎬 Instagram Stories\n\n"
        "**How to use:**\n"
        "1. Copy Instagram link\n"
        "2. Paste here\n"
        "3. Wait for download\n\n"
        "Send me any Instagram link now! 🚀"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "💡 **Need Help?**\n\n"
        "**Supported Links:**\n"
        "• Reels: `https://instagram.com/reel/ABC123/`\n"
        "• Posts: `https://instagram.com/p/XYZ789/`\n"
        "• Stories: `https://instagram.com/stories/username/123/`\n\n"
        "**If download fails:**\n"
        "• Make sure account is public\n"
        "• Try different link\n"
        "• Wait few minutes\n\n"
        "Bot is working perfectly! ✅"
    )

@app.on_message(filters.command("test"))
async def test_command(client, message: Message):
    """Test with sample links"""
    test_msg = """🧪 **Test the bot with these sample links:**
    
📹 Reel Example:
`https://www.instagram.com/reel/C4j7XZGRQwV/`

📸 Post Example:  
`https://www.instagram.com/p/C4j7XZGRQwV/`

Try copying a public Instagram link and paste it here!"""
    
    await message.reply_text(test_msg)

if __name__ == "__main__":
    print("✅ Bot started successfully!")
    app.run()
