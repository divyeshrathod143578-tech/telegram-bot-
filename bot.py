import os
import logging
import threading
import asyncio
from datetime import datetime

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", 10000))

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

@web.route("/health")
def health():
    return "OK", 200

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ AUTO DELETE FUNCTIONS ============

async def delete_message_after_delay(context, chat_id, message_id, delay=30):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def send_and_auto_delete(context, chat_id, text, reply_markup=None, parse_mode=None, delay=30, **kwargs):
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        **kwargs
    )
    asyncio.create_task(delete_message_after_delay(context, chat_id, message.message_id, delay))
    return message

async def send_photo_and_auto_delete(context, chat_id, photo, caption=None, reply_markup=None, parse_mode=None, delay=30):
    message = await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
    asyncio.create_task(delete_message_after_delay(context, chat_id, message.message_id, delay))
    return message

async def delete_previous_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'bot_message_ids' in context.user_data:
        chat_id = update.effective_chat.id
        for msg_id in context.user_data['bot_message_ids']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        context.user_data['bot_message_ids'] = []

async def store_message_id(context, chat_id, message_id):
    if 'bot_message_ids' not in context.user_data:
        context.user_data['bot_message_ids'] = []
    context.user_data['bot_message_ids'].append(message_id)
    if len(context.user_data['bot_message_ids']) > 10:
        context.user_data['bot_message_ids'] = context.user_data['bot_message_ids'][-10:]

# ============ KEYBOARDS ============

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")],
        [InlineKeyboardButton("ℹ️ ABOUT", callback_data="about")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])

def price_buttons():
    plans = [
        ("💰 ₹60 - 399 Videos", "pay_60"),
        ("💰 ₹89 - 499 Videos", "pay_89"),
        ("💰 ₹99 - 799 Videos", "pay_99"),
        ("💰 ₹130 - 1199 Videos", "pay_130"),
        ("💰 ₹149 - 2500 Group", "pay_149"),
        ("💰 ₹199 - 7999 Group", "pay_199"),
        ("💰 ₹249 - 14999 Group", "pay_249"),
        ("💰 ₹349 - Long Videos", "pay_349"),
        ("💰 ₹480 - Unlimited", "pay_480"),
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in plans]
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def price_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK TO PRICES", callback_data="price")]
    ])

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_caption = (
        f"👋 Welcome, {user.first_name}🦋🌷\n\n"
        "I am your Premium Subscription Bot. 🫣💗\n"
        "I can help you get instant access to our exclusive premium channels.\n\n"
        "👇 Click the button to browse our plans!"
    )
    
    try:
        with open("welcome.jpg", "rb") as photo:
            msg = await update.message.reply_photo(
                photo=photo,
                caption=welcome_caption,
                reply_markup=main_menu(),
                parse_mode='Markdown'
            )
    except FileNotFoundError:
        msg = await update.message.reply_text(
            welcome_caption,
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )
    
    await store_message_id(context, update.effective_chat.id, msg.message_id)

# ============ CALLBACK HANDLERS ============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    
    if query.data == "price":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="💰 **PRICE LIST**\n\nSelect your plan below:",
            reply_markup=price_buttons(),
            parse_mode='Markdown'
        )
        await store_message_id(context, chat_id, msg.message_id)
    
    elif query.data.startswith("pay_"):
        context.user_data['payment_time'] = datetime.now()
        
        try:
            with open("qr.jpg", "rb") as photo:
                qr_msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=(
                        "💳 **PAYMENT METHOD**\n\n"
                        "📲 Scan QR Code to pay\n"
                        "⏳ QR valid for 10 minutes\n\n"
                        "✅ After payment:\n"
                        "Send screenshot to @its_cuteiii\n\n"
                        "❌ Payment not received within 10 mins"
                    ),
                    reply_markup=price_back(),
                    parse_mode='Markdown'
                )
                await store_message_id(context, chat_id, qr_msg.message_id)
                
                # Auto delete QR after 10 minutes
                async def auto_delete_qr():
                    await asyncio.sleep(600)  # 10 minutes
                    try:
                        await qr_msg.delete()
                        timeout_msg = await context.bot.send_message(
                            chat_id=chat_id,
                            text="⏳ **PAYMENT TIMEOUT**\n\n"
                                 "❌ Payment not received.\n"
                                 "🔄 Please generate a new QR.",
                            reply_markup=price_back(),
                            parse_mode='Markdown'
                        )
                        await store_message_id(context, chat_id, timeout_msg.message_id)
                    except:
                        pass
                
                asyncio.create_task(auto_delete_qr())
                
        except FileNotFoundError:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text="❌ QR code not found!\nPlease contact @its_cuteiii",
                reply_markup=price_back()
            )
            await store_message_id(context, chat_id, msg.message_id)
    
    elif query.data == "demo":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🎬 **DEMO LINK**\n\n"
                 "👆 Click below to access:\n"
                 "https://t.me/+1u-iqI31ORI2ZTQ1\n\n"
                 "⏳ **Time Limit:** 15 minutes\n"
                 "🔒 Link will auto-expire\n\n"
                 "⚠️ For preview only",
            reply_markup=back_menu(),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        await store_message_id(context, chat_id, msg.message_id)
    
    elif query.data == "contact":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="📞 **CONTACT US**\n\n"
                 "👤 **Support:** @its_cuteiii\n\n"
                 "📱 **Telegram:**\n"
                 "https://t.me/its_cuteiii\n\n"
                 "⏰ **Response Time:** 5-10 mins\n"
                 "🕐 Available 24/7",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        await store_message_id(context, chat_id, msg.message_id)
    
    elif query.data == "about":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ **ABOUT US**\n\n"
                 "🌟 Premium Video Provider\n"
                 "----------------------\n"
                 "✅ High Quality Content\n"
                 "✅ Instant Delivery\n"
                 "✅ 24/7 Customer Support\n"
                 "✅ Secure Payment\n\n"
                 "📌 **Features:**\n"
                 "• Latest Videos\n"
                 "• Multiple Categories\n"
                 "• Lifetime Access Options\n"
                 "• Group Plans Available",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        await store_message_id(context, chat_id, msg.message_id)
    
    elif query.data == "back":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="👋 Welcome back!\n\nChoose an option below:",
            reply_markup=main_menu()
        )
        await store_message_id(context, chat_id, msg.message_id)
    
    try:
        await query.message.delete()
    except:
        pass

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_chat:
        chat_id = update.effective_chat.id
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="❌ An error occurred! Please try again later."
        )
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 10))

# ============ MAIN ============

def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    
    logging.info("🤖 Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
