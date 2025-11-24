# SangMata Telegram Bot

A Telegram bot that tracks username and name changes of users.

## Features
- Track name and username changes automatically
- View your own history with `/history`
- Find other users' history with `/find <user_id>`
- Privacy focused - only stores name/username data

## Deployment on Render

1. **Fork this repository**
2. **Create a new Web Service on Render**
3. **Connect your GitHub repository**
4. **Set environment variables:**
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API Hash  
   - `BOT_TOKEN`: Your Bot Token from @BotFather

5. **Deploy!**

## Environment Variables
Get these from https://my.telegram.org:
- `API_ID`
- `API_HASH` 

Get Bot Token from @BotFather on Telegram:
- `BOT_TOKEN`

## Commands
- `/start` - Start the bot
- `/history` - View your name history
- `/find <user_id>` - Find user's history
- `/stats` - Bot statistics

## Privacy
This bot only stores name and username changes, no personal messages or media.
