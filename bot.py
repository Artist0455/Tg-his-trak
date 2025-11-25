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

@app.on_message(filters.regex(r'ℹ Help'))
async def help_command(client, message: Message):
    await message.reply_text(
        'Send an Instagram link for a PUBLIC Post, Video, IGTV or Reel to download it! Stories are not currently supported.\n\n'
        'To download a user profile image, just send its username',
        reply_markup=main_keyboard
    )

@app.on_message(filters.regex(r'💰 Donate'))
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

@app.on_message(filters.regex(r'https?://.*instagram[^\s]+'))
async def send_post(client, message: Message):
    url = message.text
    
    if '?' in url:
        url += '&__a=1'
    else:
        url += '?__a=1'

    try:
        response = requests.get(url)
        if response.status_code != 200:
            await message.reply_text('❌ Could not fetch Instagram data. Make sure the account is public.')
            return
            
        visit = response.json()
        is_video = visit['graphql']['shortcode_media']['is_video']

        try:
            # Multiple posts (carousel)
            posts = visit["graphql"]["shortcode_media"]["edge_sidecar_to_children"]["edges"]

            for post in posts:
                is_video = post["node"]["is_video"]

                if is_video is True:
                    video_url = post["node"]["video_url"]
                    await message.reply_video(video_url, caption="✅ Downloaded via Instagram Bot")

                elif is_video is False:
                    post_url = post["node"]["display_url"]
                    await message.reply_photo(post_url, caption="✅ Downloaded via Instagram Bot")

        except KeyError:
            # Single post
            if is_video is True:
                video_url = visit["graphql"]["shortcode_media"]["video_url"]
                await message.reply_video(video_url, caption="✅ Downloaded via Instagram Bot")

            elif is_video is False:
                post_url = visit["graphql"]["shortcode_media"]["display_url"]
                await message.reply_photo(post_url, caption="✅ Downloaded via Instagram Bot")

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text('❌ Send Me Only Public Instagram Posts')

@app.on_message(filters.text & ~filters.command & ~filters.regex(r'https?://') & ~filters.regex(r'ℹ Help') & ~filters.regex(r'💰 Donate'))
async def send_dp(client, message: Message):
    username = message.text.strip()
    
    # Check if it looks like a username (no spaces, no special chars except _ and .)
    if not re.match(r'^[a-zA-Z0-9_.]+$', username):
        return
    
    url = f'https://instagram.com/{username}/?__a=1'

    try:
        response = requests.get(url)
        if response.status_code != 200:
            await message.reply_text('❌ User not found or account is private')
            return
            
        visit = response.json()
        user_profile = visit['graphql']['user']['profile_pic_url_hd']
        await message.reply_photo(
            user_profile, 
            caption=f"📸 Profile picture of @{username}\n\nDownloaded via Instagram Bot"
        )
        
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text('❌ Send Me Only Existing Instagram Username')

if __name__ == '__main__':
    print('✅ Bot is running with YOUR credentials...')
    app.run()
