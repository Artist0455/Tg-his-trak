import os
import re
import requests
import json
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuration
API_ID = int(os.getenv("API_ID", "25136703"))
API_HASH = os.getenv("API_HASH", "accfaf5ecd981c67e481328515c39f89")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244179451:AAER_dLg1rQT2E9wuE5XRqDumNzuBWU1JPE")

print("🚀 Starting Instagram Bot...")

app = Client("instagram_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def download_instagram_media(link):
    """Download Instagram media using multiple APIs"""
    try:
        # API 1: instagram-downloader-api (Most Reliable)
        try:
            api1_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
            querystring = {"url": link}
            headers = {
                "x-rapidapi-key": "your-rapidapi-key",  # Free tier available
                "x-rapidapi-host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
            }
            response = requests.get(api1_url, headers=headers, params=querystring, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('media'):
                    return data['media']
        except:
            pass

        # API 2: SocialDL API (Free)
        try:
            api2_url = "https://api.socialdl.com/api/instagram"
            payload = {"url": link}
            response = requests.post(api2_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('urls'):
                    return data['urls'][0] if isinstance(data['urls'], list) else data['urls']
        except:
            pass

        # API 3: SnapSave API (Backup)
        try:
            api3_url = "https://snapsave.app/action.php"
            payload = {"url": link}
            response = requests.post(api3_url, data=payload, timeout=10)
            if response.status_code == 200:
                # Extract download links from response
                urls = re.findall(r'https?://[^\s<>"]+?\.(mp4|jpg|jpeg|png)', response.text)
                if urls:
                    return urls[0]
        except:
            pass

        # API 4: InstaDP (Alternative)
        try:
            api4_url = f"https://instadp.com/api/instagram?url={link}"
            response = requests.get(api4_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('url'):
                    return data['url']
        except:
            pass

        return None

    except Exception as e:
        print(f"API Error: {e}")
        return None

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+') & filters.incoming)
async def instagram_handler(client, message: Message):
    link = message.matches[0].group(0)
    print(f"📥 Processing: {link}")
    
    m = await message.reply("🔄 Downloading your content...")
    
    try:
        # Get download URL
        media_url = download_instagram_media(link)
        
        if media_url:
            # Send media based on type
            if isinstance(media_url, list):
                # Multiple media (carousel)
                for i, url in enumerate(media_url[:5]):  # Limit to 5 items
                    try:
                        if url.endswith('.mp4'):
                            await message.reply_video(url, caption=f"📹 Part {i+1}")
                        else:
                            await message.reply_photo(url, caption=f"📸 Part {i+1}")
                    except:
                        await message.reply(f"🔗 Download Link {i+1}: {url}")
                await m.delete()
                
            else:
                # Single media
                if media_url.endswith('.mp4'):
                    await message.reply_video(media_url, caption="✅ Downloaded successfully!")
                    await m.delete()
                else:
                    await message.reply_photo(media_url, caption="✅ Downloaded successfully!")
                    await m.delete()
                    
        else:
            # Fallback to direct method
            try:
                # Try direct Instagram URL modification
                direct_url = link.replace("instagram.com", "ddinstagram.com")
                if direct_url != link:
                    await message.reply_video(direct_url, caption="✅ Downloaded via direct method!")
                    await m.delete()
                else:
                    await m.edit("❌ Could not download this content. Try another link!")
            except:
                await m.edit("❌ Could not download this content. Try another link!")
                
    except Exception as e:
        print(f"Error: {e}")
        await m.edit("❌ Download failed. Please try again later.")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "🤖 **Instagram Downloader Bot**\n\n"
        "Send me any Instagram link and I'll download it for you!\n\n"
        "**Supported:**\n"
        "• 📹 Reels\n• 📸 Posts\n• 🎬 Stories\n\n"
        "Just paste your link! 🚀"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "💡 **How to use:**\n\n"
        "1. Copy Instagram link\n"
        "2. Paste here\n"
        "3. Wait for download\n\n"
        "**Example links:**\n"
        "• Reel: https://instagram.com/reel/ABC123/\n"
        "• Post: https://instagram.com/p/XYZ789/\n"
        "• Story: https://instagram.com/stories/user/123/\n\n"
        "Bot is now working! ✅"
    )

@app.on_message(filters.command("test"))
async def test_command(client, message: Message):
    test_links = [
        "https://www.instagram.com/reel/C4j7XZGRQwV/",
        "https://www.instagram.com/p/C4j7XZGRQwV/",
        "https://www.instagram.com/stories/instagram/123/"
    ]
    
    await message.reply_text(
        "🧪 **Test Links:**\n\n" +
        "\n".join(test_links) +
        "\n\nTry any of these to test the bot!"
    )

if __name__ == "__main__":
    print("✅ Bot started successfully!")
    app.run()
