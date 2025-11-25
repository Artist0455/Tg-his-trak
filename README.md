# Instagram Downloader Telegram Bot

A Telegram bot that downloads Instagram Reels, Posts, and Stories.

## 🚀 Deploy on Render

### Method 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Method 2: Manual Deployment

1. **Fork this repository**
2. **Create a new Web Service on Render**
3. **Connect your GitHub repository**
4. **Add environment variables:**
   - `API_ID`: From https://my.telegram.org
   - `API_HASH`: From https://my.telegram.org  
   - `BOT_TOKEN`: From @BotFather on Telegram
   - `LOG_GROUP`: Optional - Group ID for logs
   - `DUMP_GROUP`: Optional - Group ID for storing media

5. **Build Command:**
   ```bash
   pip install -r requirements.txt
