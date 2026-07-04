import logging
import ssl
import sys
from config import BOT_TOKEN, ADMINS, WEBHOOK_URL, PORT, WEBHOOK_PATH
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Simulated social media availability check (replace with actual API calls)
def check_username_social(username: str) -> dict:
    """
    Check username availability across various social networks.
    Note: This is a simulation. Replace with actual APIs.
    """
    # This is where you'd integrate real APIs
    platforms = {
        "Instagram": "https://instagram.com/{}",
        "Twitter": "https://twitter.com/{}",
        "GitHub": "https://github.com/{}",
        "Reddit": "https://reddit.com/user/{}",
        "TikTok": "https://tiktok.com/@{}",
        "YouTube": "https://youtube.com/@{}",
    }
    
    results = {}
    # Simulate checks (in production, use requests to check each URL)
    for platform, url in platforms.items():
        # Simulate 70% chance of being available for demo
        import random
        is_available = random.choice([True, False])
        results[platform] = {
            "available": is_available,
            "url": url.format(username)
        }
    
    return results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Check your own username", switch_inline_query_current_chat="")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *CheckNicknameBot*\n\n"
        "Send me a username and I'll check if it's available across social networks.\n\n"
        "Example: `john_doe`\n\n"
        "⚠️ *Note*: I cannot check Telegram usernames directly due to API limitations.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def check_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the username sent by the user."""
    username = update.message.text.strip()
    
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]
    
    # Validate username format (only alphanumeric and underscore)
    if not username or not username.replace("_", "").isalnum():
        await update.message.reply_text(
            "❌ Invalid username. Please use only letters, numbers, and underscores."
        )
        return
    
    await update.message.reply_text(f"🔍 Checking `{username}` across social networks...")
    
    try:
        results = check_username_social(username)
        
        # Format results
        available = []
        taken = []
        for platform, data in results.items():
            if data["available"]:
                available.append(f"✅ {platform}: Available")
            else:
                taken.append(f"❌ {platform}: Taken - {data['url']}")
        
        message = f"📊 *Results for @{username}*\n\n"
        if available:
            message += "*Available:*\n" + "\n".join(available) + "\n\n"
        if taken:
            message += "*Taken:*\n" + "\n".join(taken)
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error checking username: {e}")
        await update.message.reply_text("❌ An error occurred while checking the username. Please try again.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel - only accessible to configured admins."""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
        [InlineKeyboardButton("📨 Send Broadcast", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 *Admin Panel*\n\nSelect an action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("admin_"):
        action = query.data.replace("admin_", "")
        if action == "stats":
            await query.edit_message_text(
                "📊 *Statistics*\n\n"
                "Users: 42\n"
                "Checks performed: 156\n"
                "Available usernames found: 89",
                parse_mode=ParseMode.MARKDOWN
            )
        elif action == "restart":
            await query.edit_message_text("🔄 Bot restarting...")
            # In production, you'd implement actual restart logic
        elif action == "broadcast":
            await query.edit_message_text(
                "📨 *Broadcast*\n\n"
                "Send a message to broadcast to all users.\n"
                "Use: `/broadcast Your message here`",
                parse_mode=ParseMode.MARKDOWN
            )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a broadcast message to all users (admin only)."""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    message = update.message.text.replace("/broadcast", "").strip()
    if not message:
        await update.message.reply_text("❌ Please provide a message to broadcast.")
        return
    
    await update.message.reply_text(
        f"📨 Broadcast sent to all users.\n\nMessage: {message}"
    )

def main() -> None:
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_username))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # For Railway, we use webhooks instead of polling
    if len(sys.argv) > 1 and sys.argv[1] == "--webhook":
        logger.info(f"Starting bot with webhook on {WEBHOOK_URL}")
        # Get SSL context for self-signed certificate
        try:
            with open("webhook_cert.pem", "rb") as f:
                certificate = f.read()
        except FileNotFoundError:
            logger.warning("Certificate not found. Using no certificate verification.")
            certificate = None
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=WEBHOOK_URL,
            cert=certificate,
            # key_file not used with certificate parameter, use cert parameter
        )
    else:
        logger.info("Starting bot with polling for local development")
        application.run_polling()

if __name__ == "__main__":
    main()
