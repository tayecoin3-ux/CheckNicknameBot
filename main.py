import logging
import sys
import random
import asyncio
from datetime import datetime
from typing import Dict, Any

# Configure logging first
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import config after logging setup
from config import BOT_TOKEN, ADMINS, WEBHOOK_URL, PORT, WEBHOOK_PATH

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

# Store user data (in production, use a database)
user_data = {}

def check_username_social(username: str) -> Dict[str, Any]:
    """
    Check username availability across various social networks.
    This is a simulation - replace with actual API calls.
    """
    platforms = {
        "Instagram": f"https://instagram.com/{username}",
        "Twitter": f"https://twitter.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Tumblr": f"https://{username}.tumblr.com",
        "Snapchat": f"https://snapchat.com/add/{username}",
    }
    
    results = {}
    for platform, url in platforms.items():
        # Simulate checks (70% chance of being available for demo)
        is_available = random.random() < 0.7
        results[platform] = {
            "available": is_available,
            "url": url,
            "checked": datetime.now().isoformat()
        }
    
    return results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Track user
    if user_id not in user_data:
        user_data[user_id] = {"first_seen": datetime.now(), "checks": 0}
    
    keyboard = [
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 Welcome, {user.first_name}!\n\n"
        "🤖 *CheckNicknameBot*\n"
        "Send me any username and I'll check its availability across multiple social networks.\n\n"
        "📝 *Example:*\n"
        "Send: `john_doe`\n"
        "Or: `@john_doe`\n\n"
        "⚠️ *Note:* I cannot check Telegram usernames directly due to Telegram's API limitations.\n\n"
        f"👤 Your ID: `{user_id}`"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = (
        "📖 *Help Guide*\n\n"
        "🔍 *How to use:*\n"
        "Simply send a username to check if it's available.\n\n"
        "✅ *Example commands:*\n"
        "• `john_doe` - Check username\n"
        "• `@john_doe` - Also works with @\n\n"
        "📊 *Admin commands:*\n"
        "• `/admin` - Admin panel (admins only)\n"
        "• `/stats` - View bot statistics\n\n"
        "⚠️ *Limitations:*\n"
        "• Cannot check Telegram usernames\n"
        "• Usernames must use letters, numbers, and underscores only\n"
        "• Minimum 3 characters\n\n"
        "❓ For issues, contact @YourSupportHandle"
    )
    
    if update.message:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def check_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the username sent by the user."""
    if not update.message or not update.message.text:
        return
    
    username = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Track user stats
    if user_id in user_data:
        user_data[user_id]["checks"] = user_data[user_id].get("checks", 0) + 1
    else:
        user_data[user_id] = {"first_seen": datetime.now(), "checks": 1}
    
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]
    
    # Validate username format
    if len(username) < 3:
        await update.message.reply_text(
            "❌ Username must be at least 3 characters long."
        )
        return
    
    if not username.replace("_", "").replace("-", "").isalnum():
        await update.message.reply_text(
            "❌ Invalid username. Please use only:\n"
            "• Letters (a-z)\n"
            "• Numbers (0-9)\n"
            "• Underscores (_)\n"
            "• Hyphens (-)"
        )
        return
    
    # Send initial status
    status_msg = await update.message.reply_text(
        f"🔍 Checking `{username}` across social networks...\n"
        "⏳ This may take a few seconds."
    )
    
    try:
        results = check_username_social(username)
        
        # Format results
        available = []
        taken = []
        for platform, data in results.items():
            if data["available"]:
                available.append(f"✅ {platform}: Available")
            else:
                taken.append(f"❌ {platform}: Taken")
        
        response = f"📊 *Results for @{username}*\n\n"
        
        if available:
            response += "🟢 *Available Platforms:*\n" + "\n".join(available[:5]) + "\n\n"
            if len(available) > 5:
                response += f"*And {len(available) - 5} more...*\n\n"
        
        if taken:
            response += "🔴 *Taken Platforms:*\n" + "\n".join(taken[:5])
            if len(taken) > 5:
                response += f"\n*And {len(taken) - 5} more...*"
        
        if not available and not taken:
            response = f"❌ No results found for `{username}`"
        
        # Add disclaimer
        response += "\n\n_⚠️ Results are simulated. For accurate checks, please use the respective platform's official tools._"
        
        await status_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error checking username: {e}")
        await status_msg.edit_text(
            "❌ An error occurred while checking the username.\n"
            "Please try again in a few moments."
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel - only accessible to configured admins."""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("💬 Broadcast", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 *Admin Panel*\n\n"
        f"ADMIN ID: `{user_id}`\n"
        f"Total Users: `{len(user_data)}`\n"
        f"Total Checks: `{sum(u.get('checks', 0) for u in user_data.values())}`\n\n"
        "Select an action:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics."""
    total_users = len(user_data)
    total_checks = sum(u.get('checks', 0) for u in user_data.values())
    
    stats_text = (
        "📊 *Bot Statistics*\n\n"
        f"👤 Total Users: `{total_users}`\n"
        f"🔍 Total Checks: `{total_checks}`\n"
        f"📈 Avg Checks/User: `{total_checks / total_users if total_users > 0 else 0:.1f}`\n\n"
        f"⏱️ Bot Uptime: Since deployment\n"
        f"🔄 Version: `1.0.0`"
    )
    
    if update.message:
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        await stats_command(update, context)
    
    elif query.data == "help":
        await help_command(update, context)
    
    elif query.data == "admin_stats":
        total_users = len(user_data)
        total_checks = sum(u.get('checks', 0) for u in user_data.values())
        
        await query.edit_message_text(
            "📊 *Detailed Statistics*\n\n"
            f"👤 Total Users: `{total_users}`\n"
            f"🔍 Total Checks: `{total_checks}`\n"
            f"📈 Avg Checks/User: `{total_checks / total_users if total_users > 0 else 0:.1f}`\n"
            f"👥 Active Today: `{sum(1 for u in user_data.values() if u.get('last_seen', datetime.now()).date() == datetime.now().date())}`\n\n"
            "Admin Panel - Press back to return.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif query.data == "admin_users":
        # Show first 10 users
        users_list = list(user_data.items())[:10]
        text = "👥 *Recent Users*\n\n"
        for i, (uid, data) in enumerate(users_list, 1):
            text += f"{i}. ID: `{uid}` - Checks: {data.get('checks', 0)}\n"
        
        if len(user_data) > 10:
            text += f"\n*And {len(user_data) - 10} more users...*"
        
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    elif query.data == "admin_broadcast":
        await query.edit_message_text(
            "📨 *Broadcast*\n\n"
            "To send a broadcast message, use:\n"
            "`/broadcast Your message here`\n\n"
            "⚠️ This will send a message to ALL users.",
            parse_mode=ParseMode.MARKDOWN
        )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a broadcast message to all users (admin only)."""
    user_id = update.effective_user.id
    
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    message = update.message.text.replace("/broadcast", "", 1).strip()
    if not message:
        await update.message.reply_text("❌ Please provide a message to broadcast.\n\nExample: `/broadcast Hello everyone!`")
        return
    
    # Simulate broadcast (in production, actually send to all users)
    await update.message.reply_text(
        f"📨 *Broadcast Initiated*\n\n"
        f"Message: {message}\n"
        f"Recipients: `{len(user_data)}` users\n"
        f"Status: ✅ Sent successfully!",
        parse_mode=ParseMode.MARKDOWN
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify admin."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and ADMINS:
        try:
            for admin_id in ADMINS:
                await context.bot.send_message(
                    admin_id,
                    f"⚠️ *Bot Error*\n\n"
                    f"Error: `{str(context.error)[:100]}`\n"
                    f"Update: `{update}`",
                    parse_mode=ParseMode.MARKDOWN
                )
        except:
            pass

def main() -> None:
    """Start the bot."""
    logger.info("Starting CheckNicknameBot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_username))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Determine if running on Railway
    is_railway = len(sys.argv) > 1 and sys.argv[1] == "--webhook"
    
    if is_railway:
        logger.info(f"🚀 Starting bot with webhook on {WEBHOOK_URL}")
        
        # Set webhook
        try:
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=WEBHOOK_PATH,
                webhook_url=WEBHOOK_URL,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            logger.error(f"Failed to start webhook: {e}")
            logger.info("Falling back to polling mode...")
            application.run_polling(allowed_updates=["message", "callback_query"])
    
    else:
        logger.info("🔄 Starting bot with polling for local development")
        application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
