import os
import re
import requests
from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# YOUR CREDENTIALS
API_ID = 25136703
API_HASH = "accfaf5ecd981c67e481328515c39f89"
BOT_TOKEN = "8244179451:AAER_dLg1rQT2E9wuE5XRqDumNzuBWU1JPE"

print("🚀 Starting Instagram Bot with YOUR Credentials...")

app = Client(
    "instagram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Main Keyboard
main_keyboard = ReplyKeyboardMarkup([
    ['ℹ Help', '💰 Donate']
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        '👋 Welcome to my bot! It can download any type of media on Instagram! (Public accounts only)',
        reply_markup=main_keyboard
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        'Send an Instagram link for a PUBLIC Post, Video, IGTV or Reel to download it! Stories are not currently supported.\n\n'
        'To download a user profile image, just send its username',
        reply_markup=main_keyboard
    )

@app.on_message(filters.command("donate"))
async def donate_command(client, message: Message):
    await message.reply_text(
        'Thank you for donating! ❤\n\nThis will help covering the costs of the hosting',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    'Buy Me A Coffee', 
                    url='https://www.buymeacoffee.com/simonfarah'
                )
            ]
        ])
    )

# Handle Help button
@app.on_message(filters.regex("ℹ Help"))
async def help_button(client, message: Message):
    await help_command(client, message)

# Handle Donate button  
@app.on_message(filters.regex("💰 Donate"))
async def donate_button(client, message: Message):
    await donate_command(client, message)

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+'))
async def send_post(client, message: Message):
    url = message.text
    
    # Show processing message
    processing_msg = await message.reply_text("🔄 Downloading from Instagram...")
    
    if '?' in url:
        url += '&__a=1'
    else:
        url += '?__a=1'

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            await processing_msg.edit_text('❌ Could not fetch Instagram data. Make sure:\n• Account is public\n• Link is correct\n• Post exists')
            return
            
        visit = response.json()
        
        # Check if media exists
        if 'graphql' not in visit or 'shortcode_media' not in visit['graphql']:
            await processing_msg.edit_text('❌ This Instagram post is not accessible')
            return
            
        is_video = visit['graphql']['shortcode_media']['is_video']

        try:
            # Multiple posts (carousel)
            posts = visit["graphql"]["shortcode_media"]["edge_sidecar_to_children"]["edges"]
            await processing_msg.edit_text(f"📦 Found {len(posts)} media files. Downloading...")

            for index, post in enumerate(posts):
                is_video = post["node"]["is_video"]

                if is_video is True:
                    video_url = post["node"]["video_url"]
                    await message.reply_video(
                        video_url, 
                        caption=f"🎬 Video {index+1}/{len(posts)}\n✅ Downloaded via Instagram Bot"
                    )

                elif is_video is False:
                    post_url = post["node"]["display_url"]
                    await message.reply_photo(
                        post_url, 
                        caption=f"📸 Photo {index+1}/{len(posts)}\n✅ Downloaded via Instagram Bot"
                    )

            await processing_msg.delete()

        except KeyError:
            # Single post
            await processing_msg.edit_text("📥 Downloading media...")
            
            if is_video is True:
                video_url = visit["graphql"]["shortcode_media"]["video_url"]
                await message.reply_video(
                    video_url, 
                    caption="🎬 Video Downloaded\n✅ Downloaded via Instagram Bot"
                )
            else:
                post_url = visit["graphql"]["shortcode_media"]["display_url"]
                await message.reply_photo(
                    post_url, 
                    caption="📸 Photo Downloaded\n✅ Downloaded via Instagram Bot"
                )
            
            await processing_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await processing_msg.edit_text('❌ Error downloading. Make sure:\n• Instagram account is public\n• Link is correct\n• Try again later')

# Handle all text messages (for usernames)
@app.on_message(filters.text)
async def handle_all_text(client, message: Message):
    text = message.text.strip()
    
    # Skip if it's a command
    if text.startswith('/'):
        return
        
    # Skip if it's a button text (already handled by separate handlers)
    if text in ['ℹ Help', '💰 Donate']:
        return
        
    # Skip if it's a URL (already handled by URL handler)
    if text.startswith('http'):
        return
    
    # Check if it looks like a username
    if re.match(r'^[a-zA-Z0-9_.]{1,30}$', text):
        await download_profile_pic(client, message, text)
    else:
        await message.reply_text(
            "❌ Please send:\n"
            "• Instagram link (to download posts/reels)\n"
            "• Instagram username (to download profile picture)\n"
            "• Or use buttons below",
            reply_markup=main_keyboard
        )

async def download_profile_pic(client, message: Message, username: str):
    """Download Instagram profile picture"""
    
    processing_msg = await message.reply_text(f"👤 Fetching profile picture of @{username}...")
    
    url = f'https://instagram.com/{username}/?__a=1'

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            await processing_msg.edit_text('❌ User not found or account is private')
            return
            
        visit = response.json()
        user_profile = visit['graphql']['user']['profile_pic_url_hd']
        
        await processing_msg.edit_text("📸 Downloading profile picture...")
        await message.reply_photo(
            user_profile, 
            caption=f"👤 Profile picture of @{username}\n✅ Downloaded via Instagram Bot"
        )
        await processing_msg.delete()
        
    except Exception as e:
        print(f"Error: {e}")
        await processing_msg.edit_text('❌ User not found or account is private')

if __name__ == '__main__':
    print('✅ Bot is running with YOUR credentials...')
    app.run()
