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

# ============ FLASK ============
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

# ============ DELETE FUNCTIONS ============
async def delete_message_after_delay(context, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def delete_qr_and_notify(context, chat_id, qr_msg_id):
    await asyncio.sleep(600)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=qr_msg_id)
        timeout_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ PAYMENT TIMEOUT!\n\n❌ QR expired after 10 minutes.\n🔄 Please select a plan again.",
            reply_markup=main_menu()
        )
        await asyncio.sleep(30)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=timeout_msg.message_id)
        except:
            pass
    except:
        pass

# ============ SEND WELCOME ============
async def send_welcome(chat_id, context, text="👋 Welcome, It's 🦋🌷\n\nI am your Premium Subscription Bot. 😍😍\nI can help you get instant access to our exclusive premium channels.\n\n👀 Click the button to browse our plans!"):
    try:
        with open("welcome.jpg", "rb") as photo:
            return await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=main_menu(),
                parse_mode=None
            )
    except:
        return await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=main_menu(),
            parse_mode=None
        )

# ============ START ============
async def start(update, context):
    chat_id = update.effective_chat.id
    
    if 'qr_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
        except:
            pass
        del context.user_data['qr_msg_id']
    
    if 'link_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['link_msg_id'])
        except:
            pass
        del context.user_data['link_msg_id']
    
    await send_welcome(chat_id, context)

# ============ BUTTON HANDLER ============
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    if query.data == "price":
        if 'qr_msg_id' in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
            except:
                pass
            del context.user_data['qr_msg_id']
        
        await query.message.edit_text(
            "💰 **PRICE LIST**\n\nSelect your plan:",
            reply_markup=price_buttons(),
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        
        if 'qr_msg_id' in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
            except:
                pass
            del context.user_data['qr_msg_id']
        
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                qr_msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"💳 **Pay ₹{plan}**\n\n⏳ QR expires in 10 minutes\n\n✅ Send Transaction ID after payment:",
                    reply_markup=back_button(),
                    parse_mode="Markdown"
                )
                context.user_data['qr_msg_id'] = qr_msg.message_id
                asyncio.create_task(delete_qr_and_notify(context, chat_id, qr_msg.message_id))
        except:
            await query.message.edit_text(
                f"💳 **Pay ₹{plan}**\n\nSend Transaction ID:",
                reply_markup=back_button(),
                parse_mode="Markdown"
            )
    
    elif query.data == "contact":
        await query.message.edit_text(
            "📞 **CONTACT**\n\n@its_cuteiii",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    
    elif query.data == "back":
        if 'qr_msg_id' in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
            except:
                pass
            del context.user_data['qr_msg_id']
        
        await query.message.delete()
        await send_welcome(chat_id, context, "👋 Welcome, It's 🦋🌷\n\nI am your Premium Subscription Bot. 😍😍\nI can help you get instant access to our exclusive premium channels.\n\n👀 Click the button to browse our plans!")

# ============ TRANSACTION HANDLER ============
async def handle_transaction(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    if 'selected_plan' not in context.user_data:
        await update.message.reply_text(
            "❌ Select a plan first!",
            reply_markup=main_menu()
        )
        return
    
    plan = context.user_data['selected_plan']
    
    if 'qr_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
        except:
            pass
        del context.user_data['qr_msg_id']
    
    try:
        await update.message.delete()
    except:
        pass
    
    link_msg = await update.message.reply_text(
        f"✅ **PAYMENT CONFIRMED!** 🎉\n\n"
        f"🔗 **JOIN GROUP:**\n{GROUP_LINK}\n\n"
        f"⚠️ Link expires in 30 seconds!",
        parse_mode="Markdown"
    )
    
    context.user_data['link_msg_id'] = link_msg.message_id
    asyncio.create_task(delete_message_after_delay(context, chat_id, link_msg.message_id, 30))
    
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
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
