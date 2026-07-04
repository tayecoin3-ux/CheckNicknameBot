import os

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMINS = [int(id) for id in os.getenv("ADMINS", "123456789").split(",")]

# Webhook settings - Railway provides the URL dynamically
# Set this to your Railway app URL, e.g., "https://your-app-name.up.railway.app"
HOST = os.getenv("HOST", "YOUR_RAILWAY_APP_URL")
PORT = int(os.getenv("PORT", 443))

# Set webhook path
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{HOST}{WEBHOOK_PATH}"
