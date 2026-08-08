import os
import requests
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ LOGGING ============
logging.basicConfig(level=logging.INFO)

# ============ TOKEN ============
TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000

# ============ GROUP LINK ============
GROUP_LINK = "https://t.me/+soK0QlFXTxQ1OTI1"

# ============ FLASK APP ============
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

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

def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])

# ============ HANDLERS ============

async def start(update, context):
    if 'selected_plan' in context.user_data:
        del context.user_data['selected_plan']
    
    await update.message.reply_text(
        "👋 Welcome!\n\nI am your Premium Subscription Bot.\n\nChoose an option below:",
        reply_markup=main_menu()
    )

async def button_handler(update, context):
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
                    caption=f"💳 Scan QR Code to pay ₹{plan}\n\n✅ After payment, send Transaction ID here:",
                    reply_markup=back_button()
                )
        except FileNotFoundError:
            await query.message.edit_text(
                f"💳 Pay ₹{plan}\n\nPlease send your Transaction ID after payment:",
                reply_markup=back_button()
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

async def handle_transaction(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check if plan is selected
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Please select a plan first!\n\nClick PRICE LIST → Choose a plan.",
            reply_markup=main_menu()
        )
        return
    
    plan = context.user_data['selected_plan']
    
    # ✅ DIRECTLY SEND GROUP LINK - NO SUPABASE CHECK!
    try:
        await update.message.delete()
    except:
        pass
    
    await update.message.reply_text(
        f"✅ PAYMENT CONFIRMED! 🎉\n\n"
        f"💰 Plan: ₹{plan}\n"
        f"🧾 Transaction ID: {text}\n\n"
        f"🔗 **JOIN GROUP:**\n{GROUP_LINK}\n\n"
        f"⚠️ Link is valid for 1 minute!"
    )
    
    # Clear selected plan
    if 'selected_plan' in context.user_data:
        del context.user_data['selected_plan']

# ============ ERROR HANDLER ============

async def error_handler(update, update2, context):
    logging.error(f"Error: {context.error}")

# ============ MAIN ============

import threading

def main():
    # Start Flask server
    threading.Thread(target=run_web, daemon=True).start()
    
    # Create bot application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    app.add_error_handler(error_handler)
    
    logging.info("🤖 Bot is starting...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
