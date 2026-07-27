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

TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# ============ SUPABASE CONFIG ============
SUPABASE_URL = "https://fenfugidjsacajvqaxoa.supabase.co"
SUPABASE_KEY = "sb_publishable_5eO5_0miaJnq4Ia296cSqw_CXJOE-8-"

# ============ GROUP CONFIG ============
GROUP_LINK = "https://t.me/+67naOJSv9-Y3ZjY1"
GROUP_CHAT_ID = -1004378712024

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

@web.route("/health")
def health():
    return "OK", 200

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ SUPABASE FUNCTIONS ============

def save_payment(user_id, transaction_id, plan):
    url = f"{SUPABASE_URL}/rest/v1/paid_users"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "user_id": str(user_id),
        "transaction_id": str(transaction_id),
        "plan": str(plan),
        "payment_status": "completed"
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        return response.status_code == 201
    except:
        return False

def check_transaction(transaction_id):
    url = f"{SUPABASE_URL}/rest/v1/paid_users?transaction_id=eq.{transaction_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return len(data) > 0
        return False
    except:
        return False

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
    
    await store_all_message_id(context, chat_id, msg.message_id)
    return msg

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
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

# ============ MESSAGE HANDLER ============

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
    
    if check_transaction(text):
        msg = await update.message.reply_text(
            "❌ This Transaction ID is already used!\n\nPlease use a valid ID.",
            parse_mode=None
        )
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 30))
        return
    
    plan = context.user_data['selected_plan']
    success = save_payment(user_id, text, plan)
    
    if success:
        # Delete user's message instantly
        try:
            await update.message.delete()
        except:
            pass
        
        # ============ FORCE ADD USER TO GROUP ============
        added_to_group = False
        try:
            # Method 1: Ban + Unban (100% working)
            await context.bot.ban_chat_member(GROUP_CHAT_ID, user_id)
            await asyncio.sleep(0.5)
            await context.bot.unban_chat_member(GROUP_CHAT_ID, user_id)
            added_to_group = True
            logging.info(f"✅ User {user_id} force added to group")
        except Exception as e:
            logging.error(f"❌ Add error: {e}")
            
            # Method 2: Try approve if ban fails
            try:
                await context.bot.approve_chat_join_request(GROUP_CHAT_ID, user_id)
                added_to_group = True
                logging.info(f"✅ User {user_id} approved")
            except:
                pass
        
        # ============ SEND CONFIRMATION (NO LINK) ============
        if added_to_group:
            msg_text = (
                f"✅ PAYMENT CONFIRMED! 🎉\n\n"
                f"Plan: ₹{plan}\n"
                f"Transaction ID: {text}\n\n"
                f"🔥 You have been added to the Premium Group!\n"
                f"📌 Check your group list."
            )
        else:
            msg_text = (
                f"✅ PAYMENT CONFIRMED! 🎉\n\n"
                f"Plan: ₹{plan}\n"
                f"Transaction ID: {text}\n\n"
                f"⚠️ Please contact @its_cuteiii to join the group."
            )
        
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=msg_text,
            parse_mode=None
        )
        
        # Delete confirmation after 60 seconds
        asyncio.create_task(delete_message_after_delay(context, chat_id, msg.message_id, 60))
        
        # After 60 seconds, show welcome
        async def show_welcome_after_delay():
            await asyncio.sleep(60)
            await delete_all_previous_messages(context, chat_id)
            await send_welcome_message(chat_id, context)
        
        asyncio.create_task(show_welcome_after_delay())
        
        del context.user_data['selected_plan']
    else:
        await update.message.reply_text(
            "❌ Payment verification failed!\nPlease contact @its_cuteiii",
            parse_mode=None
        )

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
