import os
import logging
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ LOGGING ============
logging.basicConfig(level=logging.INFO)

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000

# ============ SUPABASE ============
SUPABASE_URL = "https://fenfugidjisacajvqaxoa.supabase.co"
SUPABASE_KEY = "sb_publishable_5eO5_0miaJnq4Ia296cSqw_CXJOE-8-"

# ✅ YAHAN GROUP LINK DAALO
GROUP_LINK = "https://t.me/+67naOJSv9-Y3ZjY1"

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

def price_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK TO PRICES", callback_data="price")]
    ])

# ============ SAVE PAYMENT ============

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
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.status_code in [200, 201]
    except:
        return False

# ============ HANDLERS ============

async def start(update, context):
    if 'selected_plan' in context.user_data:
        del context.user_data['selected_plan']
    await update.message.reply_text(
        "👋 Welcome!\n\nChoose an option:",
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
                    caption=f"💳 Scan QR to pay ₹{plan}\n\nSend Transaction ID after payment:",
                    reply_markup=price_back()
                )
        except:
            await query.message.edit_text(
                f"💳 Pay ₹{plan}\n\nSend Transaction ID:",
                reply_markup=price_back()
            )
    
    elif query.data == "contact":
        await query.message.edit_text(
            "📞 Contact: @its_cuteiii",
            reply_markup=main_menu()
        )
    
    elif query.data == "back":
        await query.message.edit_text(
            "👋 Welcome back!",
            reply_markup=main_menu()
        )

async def handle_transaction(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Please select a plan first!",
            reply_markup=main_menu()
        )
        return
    
    plan = context.user_data['selected_plan']
    
    # ✅ SAVE TO SUPABASE
    success = save_payment(user_id, text, plan)
    
    if success:
        await update.message.delete()
        await update.message.reply_text(
            f"✅ PAYMENT CONFIRMED! 🎉\n\n"
            f"Plan: ₹{plan}\n"
            f"Transaction: {text}\n\n"
            f"🔗 JOIN GROUP:\n{GROUP_LINK}\n\n"
            f"⚠️ Link valid for 1 minute!"
        )
        del context.user_data['selected_plan']
    else:
        await update.message.reply_text(
            "❌ Payment failed!\nContact @its_cuteiii",
            reply_markup=main_menu()
        )

# ============ MAIN ============

import threading

def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    
    app.run_polling()

if __name__ == "__main__":
    main()
