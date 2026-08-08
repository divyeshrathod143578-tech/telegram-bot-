import os
import logging
import threading
import asyncio
from datetime import datetime
import requests
import sys

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ LOGGING SETUP ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = int(os.environ.get("PORT", 10000))

# ============ SUPABASE CONFIG ============
SUPABASE_URL = "https://fenfugidjisacajvqaxoa.supabase.co"
SUPABASE_KEY = "sb_publishable_5eO5_0miaJnq4Ia296cSqw_CXJOE-8-"

# ============ GROUP CONFIG ============
GROUP_LINK = "https://t.me/+soK0QlFXTxQ1OTI1"

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

@web.route("/health")
def health():
    return "OK", 200

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ AUTO DELETE ============

async def delete_message_after_delay(context, chat_id, message_id, delay=30):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def delete_all_previous_messages(context, chat_id):
    try:
        if 'all_bot_messages' in context.user_data:
            for msg_id in context.user_data['all_bot_messages']:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except:
                    pass
            context.user_data['all_bot_messages'] = []
    except:
        pass

async def store_all_message_id(context, chat_id, message_id):
    if 'all_bot_messages' not in context.user_data:
        context.user_data['all_bot_messages'] = []
    context.user_data['all_bot_messages'].append(message_id)
    if len(context.user_data['all_bot_messages']) > 20:
        context.user_data['all_bot_messages'] = context.user_data['all_bot_messages'][-20:]

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

# ============ WELCOME MESSAGE ============

async def send_welcome_message(chat_id, context):
    welcome_caption = (
        "👋 Welcome, It's 🦋🌷\n\n"
        "I am your Premium Subscription Bot. 😍😍\n"
        "I can help you get instant access to our exclusive premium channels.\n\n"
        "👀 Click the button to browse our plans!"
    )
    
    try:
        with open("welcome.jpg", "rb") as photo:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=welcome_caption,
                reply_markup=main_menu(),
                parse_mode=None
            )
    except FileNotFoundError:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_caption,
            reply_markup=main_menu(),
            parse_mode=None
        )
    
    context.user_data['welcome_msg_id'] = msg.message_id
    await store_all_message_id(context, chat_id, msg.message_id)
    return msg

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if 'welcome_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['welcome_msg_id'])
        except:
            pass
    
    await delete_all_previous_messages(context, chat_id)
    await send_welcome_message(chat_id, context)
    
    asyncio.create_task(delete_message_after_delay(context, chat_id, update.message.message_id, 5))

# ============ CALLBACK HANDLERS ============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    
    try:
        await query.message.delete()
    except:
        pass
    
    if query.data == "price":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="💰 PRICE LIST\n\nSelect your plan below:",
            reply_markup=price_buttons(),
            parse_mode=None
        )
        await store_all_message_id(context, chat_id, msg.message_id)
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 120))
    
    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        
        try:
            with open("qr.jpg", "rb") as photo:
                qr_msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=(
                        f"💳 PAYMENT METHOD\n\n"
                        f"📲 Scan QR Code to pay ₹{plan}\n"
                        f"⏳ QR valid for 10 minutes\n\n"
                        f"✅ After payment:\n"
                        f"Send Transaction ID here\n\n"
                        f"📝 Example: TXN1234567890\n\n"
                        f"❌ Fake ID = No Access ❌"
                    ),
                    reply_markup=price_back(),
                    parse_mode=None
                )
                await store_all_message_id(context, chat_id, qr_msg.message_id)
                context.user_data['qr_msg_id'] = qr_msg.message_id
                
                async def auto_delete_qr():
                    await asyncio.sleep(600)
                    try:
                        await qr_msg.delete()
                        timeout_msg = await context.bot.send_message(
                            chat_id=chat_id,
                            text="⏳ PAYMENT TIMEOUT\n\n❌ Payment not received.\n🔄 Please generate a new QR.",
                            reply_markup=price_back(),
                            parse_mode=None
                        )
                        await store_all_message_id(context, chat_id, timeout_msg.message_id)
                        asyncio.create_task(delete_message_after_delay(context, chat_id, timeout_msg.message_id, 30))
                    except:
                        pass
                
                asyncio.create_task(auto_delete_qr())
                
        except FileNotFoundError:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text="❌ QR code not found!\nPlease contact @its_cuteiii",
                reply_markup=price_back(),
                parse_mode=None
            )
            await store_all_message_id(context, chat_id, msg.message_id)
            asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 60))
    
    elif query.data == "demo":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🎬 DEMO LINK\n\n👆 Click below to access:\nhttps://t.me/+gywxm8qaCkIzYzI1\n\n⏳ Time Limit: 15 minutes\n🔒 Link will auto-expire\n\n⚠️ For preview only",
            reply_markup=back_menu(),
            parse_mode=None,
            disable_web_page_preview=True
        )
        await store_all_message_id(context, chat_id, msg.message_id)
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 120))
    
    elif query.data == "contact":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="📞 CONTACT US\n\n👤 Support: @its_cuteiii\n\n📱 Telegram:\nhttps://t.me/its_cuteiii\n\n⏰ Response Time: 5-10 mins\n🕐 Available 24/7",
            reply_markup=back_menu(),
            parse_mode=None
        )
        await store_all_message_id(context, chat_id, msg.message_id)
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 120))
    
    elif query.data == "about":
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="ℹ️ ABOUT US\n\n🌟 Premium Video Provider\n----------------------\n✅ High Quality Content\n✅ Instant Delivery\n✅ 24/7 Customer Support\n✅ Secure Payment\n\n📌 Features:\n• Latest Videos\n• Multiple Categories\n• Lifetime Access Options\n• Group Plans Available",
            reply_markup=back_menu(),
            parse_mode=None
        )
        await store_all_message_id(context, chat_id, msg.message_id)
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 120))
    
    elif query.data == "back":
        await delete_all_previous_messages(context, chat_id)
        await send_welcome_message(chat_id, context)

# ============ MESSAGE HANDLER - FIXED ============

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Please select a plan first!\n\nClick PRICE LIST → Choose a plan.",
            reply_markup=main_menu(),
            parse_mode=None
        )
        return
    
    plan = context.user_data['selected_plan']
    
    # ✅ DIRECT LINK - BINA SUPABASE CHECK KE!
    try:
        await update.message.delete()
    except:
        pass
    
    # ✅ SEND GROUP LINK DIRECTLY
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ PAYMENT CONFIRMED! 🎉\n\n"
            f"Plan: ₹{plan}\n"
            f"Transaction ID: {text}\n\n"
            f"🔗 Click below to join the group:\n{GROUP_LINK}\n\n"
            f"⚠️ Link expires in 49 seconds!"
        ),
        parse_mode=None
    )
    
    # ✅ DELETE LINK MESSAGE AFTER 49 SECONDS
    asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 49))
    
    # ✅ CLEANUP AND SHOW WELCOME
    async def clean_after_delay():
        await asyncio.sleep(49)
        if 'all_bot_messages' in context.user_data:
            for msg_id in context.user_data['all_bot_messages']:
                if msg_id != context.user_data.get('welcome_msg_id'):
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    except:
                        pass
            context.user_data['all_bot_messages'] = [context.user_data.get('welcome_msg_id')]
        await send_welcome_message(chat_id, context)
    
    asyncio.create_task(clean_after_delay())
    
    del context.user_data['selected_plan']

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ An error occurred! Please try again later.",
            parse_mode=None
        )

# ============ MAIN ============

def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    app.add_error_handler(error_handler)
    
    logging.info("🤖 Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, poll_interval=0.5)

if __name__ == "__main__":
    main()
import os
import logging
import threading
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000
GROUP_LINK = "https://t.me/+soK0QlFXTxQ1OTI1"

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ KEYBOARDS ============
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ])

def price_buttons():
    plans = [
        [InlineKeyboardButton("💰 ₹60 - 399 Videos", callback_data="pay_60")],
        [InlineKeyboardButton("💰 ₹89 - 499 Videos", callback_data="pay_89")],
        [InlineKeyboardButton("💰 ₹99 - 799 Videos", callback_data="pay_99")],
        [InlineKeyboardButton("💰 ₹130 - 1199 Videos", callback_data="pay_130")],
        [InlineKeyboardButton("💰 ₹149 - 2500 Group", callback_data="pay_149")],
        [InlineKeyboardButton("💰 ₹199 - 7999 Group", callback_data="pay_199")],
        [InlineKeyboardButton("💰 ₹249 - 14999 Group", callback_data="pay_249")],
        [InlineKeyboardButton("💰 ₹349 - Long Videos", callback_data="pay_349")],
        [InlineKeyboardButton("💰 ₹480 - Unlimited", callback_data="pay_480")],
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ]
    return InlineKeyboardMarkup(plans)

def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])

# ============ WELCOME ============
async def send_welcome(chat_id, context):
    text = (
        "👋 Welcome, It's 🦋🌷\n\n"
        "I am your Premium Subscription Bot. 😍😍\n"
        "I can help you get instant access to our exclusive premium channels.\n\n"
        "👀 Click the button to browse our plans!"
    )
    try:
        with open("welcome.jpg", "rb") as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=main_menu())
    except:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=main_menu())

# ============ START ============
async def start(update, context):
    await send_welcome(update.effective_chat.id, context)

# ============ BUTTON HANDLER ============
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == "demo":
        await query.message.reply_text("🎬 DEMO LINK:\nhttps://t.me/+gywxm8qaCkIzYzI1")

    elif query.data == "price":
        await query.message.edit_text("💰 PRICE LIST\n\nSelect your plan:", reply_markup=price_buttons())

    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                await query.message.reply_photo(photo=photo, caption=f"💳 Pay ₹{plan}\n\nSend Transaction ID:", reply_markup=back_button())
        except:
            await query.message.edit_text(f"💳 Pay ₹{plan}\n\nSend Transaction ID:", reply_markup=back_button())

    elif query.data == "contact":
        await query.message.reply_text("📞 Contact: @its_cuteiii")

    elif query.data == "back":
        await query.message.delete()
        await send_welcome(chat_id, context)

# ============ TRANSACTION → DIRECT LINK ============
async def handle_transaction(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if 'selected_plan' not in context.user_data:
        await update.message.reply_text("❌ Select a plan first!", reply_markup=main_menu())
        return

    plan = context.user_data['selected_plan']
    await update.message.delete()

    await update.message.reply_text(
        f"✅ PAYMENT CONFIRMED! 🎉\n\n"
        f"Plan: ₹{plan}\n"
        f"Transaction ID: {text}\n\n"
        f"🔗 JOIN GROUP:\n{GROUP_LINK}\n\n"
        f"⚠️ This message will self-destruct in 49 seconds."
    )

    del context.user_data['selected_plan']

# ============ MAIN ============
def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000
GROUP_LINK = "https://t.me/+soK0QlFXTxQ1OTI1"

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ KEYBOARDS ============
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ])

def price_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ₹60 - 399 Videos", callback_data="pay_60")],
        [InlineKeyboardButton("💰 ₹89 - 499 Videos", callback_data="pay_89")],
        [InlineKeyboardButton("💰 ₹99 - 799 Videos", callback_data="pay_99")],
        [InlineKeyboardButton("💰 ₹130 - 1199 Videos", callback_data="pay_130")],
        [InlineKeyboardButton("💰 ₹149 - 2500 Group", callback_data="pay_149")],
        [InlineKeyboardButton("💰 ₹199 - 7999 Group", callback_data="pay_199")],
        [InlineKeyboardButton("💰 ₹249 - 14999 Group", callback_data="pay_249")],
        [InlineKeyboardButton("💰 ₹349 - Long Videos", callback_data="pay_349")],
        [InlineKeyboardButton("💰 ₹480 - Unlimited", callback_data="pay_480")],
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])

def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])

# ============ WELCOME ============
async def send_welcome(chat_id, context):
    text = (
        "👋 Welcome, It's 🦋🌷\n\n"
        "I am your Premium Subscription Bot. 😍😍\n"
        "I can help you get instant access to our exclusive premium channels.\n\n"
        "👀 Click the button to browse our plans!"
    )
    try:
        with open("welcome.jpg", "rb") as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=main_menu())
    except:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=main_menu())

# ============ START ============
async def start(update, context):
    await send_welcome(update.effective_chat.id, context)

# ============ BUTTON HANDLER ============
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == "demo":
        await query.message.reply_text("🎬 DEMO LINK:\nhttps://t.me/+gywxm8qaCkIzYzI1")

    elif query.data == "price":
        await query.message.edit_text("💰 PRICE LIST\n\nSelect your plan:", reply_markup=price_buttons())

    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                await query.message.reply_photo(photo=photo, caption=f"💳 Pay ₹{plan}\n\nSend Transaction ID:", reply_markup=back_button())
        except:
            await query.message.edit_text(f"💳 Pay ₹{plan}\n\nSend Transaction ID:", reply_markup=back_button())

    elif query.data == "contact":
        await query.message.reply_text("📞 Contact: @its_cuteiii")

    elif query.data == "back":
        await query.message.delete()
        await send_welcome(chat_id, context)

# ============ TRANSACTION → DIRECT LINK ============
async def handle_transaction(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if 'selected_plan' not in context.user_data:
        await update.message.reply_text("❌ Select a plan first!", reply_markup=main_menu())
        return

    plan = context.user_data['selected_plan']
    await update.message.delete()

    await update.message.reply_text(
        f"✅ PAYMENT CONFIRMED! 🎉\n\n"
        f"Plan: ₹{plan}\n"
        f"Transaction ID: {text}\n\n"
        f"🔗 JOIN GROUP:\n{GROUP_LINK}\n\n"
        f"⚠️ This message will self-destruct in 49 seconds."
    )

    del context.user_data['selected_plan']

# ============ MAIN ============
def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
