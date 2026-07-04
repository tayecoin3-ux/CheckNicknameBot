import os

# Bot settings from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

# Admin user IDs (comma-separated)
ADMINS = []
admins_str = os.environ.get("ADMINS", "")
if admins_str:
    ADMINS = [int(id.strip()) for id in admins_str.split(",") if id.strip()]

# Webhook settings - Railway provides the URL dynamically
HOST = os.environ.get("HOST", "https://your-app-name.up.railway.app")
PORT = int(os.environ.get("PORT", 8080))  # Railway uses 8080 by default

# Webhook path
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{HOST}{WEBHOOK_PATH}"

# Logging level
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
