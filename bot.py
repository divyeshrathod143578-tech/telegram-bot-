import os
import logging
import threading
import asyncio
import requests
import sys

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ LOGGING ============
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000

# ============ SUPABASE - FIXED URL ============
SUPABASE_URL = "https://fenfugidjisacajvqaxoa.supabase.co"
SUPABASE_KEY = "sb_publishable_5eO5_0miaJnq4Ia296cSqw_CXJOE-8-"

# ============ GROUP LINK ============
GROUP_LINK = "https://t.me/+67naOJSv9-Y3ZjY1"

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

@web.route("/health")
def health():
    return "OK", 200

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ KEYBOARDS ============

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
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
    await update.message.reply_text(
        "👋 Welcome!\n\nI am your Premium Subscription Bot.\n\nChoose an option below:",
        reply_markup=main_menu()
    )

# ============ CALLBACK HANDLERS ============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "price":
        await query.message.edit_text(
            "💰 PRICE LIST\n\nSelect your plan:",
            reply_markup=price_buttons()
        )
    
    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                await query.message.reply_photo(
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
                    reply_markup=price_back()
                )
        except FileNotFoundError:
            await query.message.edit_text(
                "❌ QR code not found!\nPlease contact @its_cuteiii",
                reply_markup=price_back()
            )
    
    elif query.data == "contact":
        await query.message.edit_text(
            "📞 CONTACT US\n\n👤 Support: @its_cuteiii",
            reply_markup=main_menu()
        )
    
    elif query.data == "back":
        await query.message.edit_text(
            "👋 Welcome back!\n\nChoose an option:",
            reply_markup=main_menu()
        )

# ============ MESSAGE HANDLER ============

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Please select a plan first!\n\nClick PRICE LIST → Choose a plan.",
            reply_markup=main_menu()
        )
        return
    
    plan = context.user_data['selected_plan']
    
    # ✅ SAVE PAYMENT
    url = f"{SUPABASE_URL}/rest/v1/paid_users"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "user_id": str(user_id),
        "transaction_id": str(text),
        "plan": str(plan),
        "payment_status": "completed"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 201:
            try:
                await update.message.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"✅ PAYMENT CONFIRMED! 🎉\n\n"
                f"Plan: ₹{plan}\n"
                f"Transaction ID: {text}\n\n"
                f"🔗 Click below to join the group:\n{GROUP_LINK}\n\n"
                f"⚠️ Link expires in 1 minute!"
            )
            
            if 'selected_plan' in context.user_data:
                del context.user_data['selected_plan']
        else:
            await update.message.reply_text(
                f"❌ Payment verification failed!\nError: {response.status_code}\nPlease contact @its_cuteiii",
                reply_markup=main_menu()
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\nPlease contact @its_cuteiii",
            reply_markup=main_menu()
        )

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")

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
