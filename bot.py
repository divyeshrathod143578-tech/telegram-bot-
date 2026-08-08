import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ LOGGING ============
logging.basicConfig(level=logging.INFO)

# ============ TOKEN & CONFIG ============
TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000
GROUP_LINK = "https://t.me/+soK0QlFXTxQ1OTI1"
DEMO_LINK = "https://t.me/+gywxm8qaCkIzYzI1"

# ============ FLASK ============
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ============ KEYBOARDS ============
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

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
    keyboard = [
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============ SEND WELCOME ============
async def send_welcome(chat_id, context):
    text = (
        "👋 Welcome, It's 🦋🌷\n\n"
        "I am your Premium Subscription Bot. 😍😍\n"
        "I can help you get instant access to our exclusive premium channels.\n\n"
        "👀 Click the button to browse our plans!"
    )
    try:
        with open("welcome.jpg", "rb") as photo:
            return await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=main_menu()
            )
    except:
        return await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=main_menu()
        )

# ============ START ============
async def start(update, context):
    chat_id = update.effective_chat.id
    await send_welcome(chat_id, context)

# ============ BUTTON HANDLER ============
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    # ----- DEMO -----
    if query.data == "demo":
        await query.message.reply_text(
            f"🎬 **DEMO LINK**\n\n"
            f"🔗 {DEMO_LINK}\n\n"
            f"⏳ **Time Limit:** 15 minutes\n"
            f"⚠️ For preview only",
            parse_mode="Markdown"
        )
    
    # ----- PRICE LIST -----
    elif query.data == "price":
        await query.message.edit_text(
            "💰 **PRICE LIST**\n\nSelect your plan:",
            reply_markup=price_buttons(),
            parse_mode="Markdown"
        )
    
    # ----- PAYMENT OPTIONS -----
    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                await query.message.reply_photo(
                    photo=photo,
                    caption=(
                        f"💳 **PAYMENT METHOD**\n\n"
                        f"📲 Scan QR Code to pay ₹{plan}\n"
                        f"⏳ **QR valid for 10 minutes**\n\n"
                        f"✅ After payment, send Transaction ID here:"
                    ),
                    reply_markup=back_button(),
                    parse_mode="Markdown"
                )
        except:
            await query.message.edit_text(
                f"💳 **Pay ₹{plan}**\n\nSend Transaction ID after payment:",
                reply_markup=back_button(),
                parse_mode="Markdown"
            )
    
    # ----- CONTACT -----
    elif query.data == "contact":
        await query.message.reply_text(
            "📞 **CONTACT US**\n\n"
            "👤 Support: @its_cuteiii",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    
    # ----- BACK -----
    elif query.data == "back":
        await query.message.delete()
        await send_welcome(chat_id, context)

# ============ TRANSACTION HANDLER ============
async def handle_transaction(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Please select a plan first!",
            reply_markup=main_menu()
        )
        return
    
    plan = context.user_data['selected_plan']
    
    try:
        await update.message.delete()
    except:
        pass
    
    await update.message.reply_text(
        f"✅ **PAYMENT CONFIRMED!** 🎉\n\n"
        f"💰 Plan: ₹{plan}\n"
        f"🧾 Transaction ID: `{text}`\n\n"
        f"🔗 **JOIN GROUP:**\n{GROUP_LINK}\n\n"
        f"⚠️ Link is valid for 30 seconds!",
        parse_mode="Markdown"
    )
    
    if 'selected_plan' in context.user_data:
        del context.user_data['selected_plan']

# ============ ERROR HANDLER ============
async def error_handler(update, update2, context):
    logging.error(f"Error: {context.error}")

# ============ MAIN ============
def main():
    threading.Thread(target=run_web, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transaction))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
