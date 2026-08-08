import os
import logging
import threading
import asyncio
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = "8624130041:AAEG-IuDfZ-hYnk3-SaSImGbWVpTzFuY09U"
PORT = 10000
SUPABASE_URL = "https://fenfugidjisacajvqaxoa.supabase.co"
SUPABASE_KEY = "sb_publishable_5eO5_0miaJnq4Ia296cSqw_CXJOE-8-"
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

# ============ SUPABASE ============
def check_transaction(tx_id):
    url = f"{SUPABASE_URL}/rest/v1/paid_users?transaction_id=eq.{tx_id}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        return r.status_code == 200 and len(r.json()) > 0
    except:
        return False

def save_payment(user_id, tx_id, plan):
    url = f"{SUPABASE_URL}/rest/v1/paid_users"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    data = {"user_id": str(user_id), "transaction_id": str(tx_id), "plan": str(plan), "payment_status": "completed"}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        return r.status_code == 201
    except:
        return False

# ============ DELETE ============
async def delete_msg(context, chat_id, msg_id, delay):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass

# ============ SEND WELCOME ============
async def send_welcome(chat_id, context):
    text = "👋 Welcome, It's 🦋🌷\n\nI am your Premium Subscription Bot. 😍😍\nI can help you get instant access to our exclusive premium channels.\n\n👀 Click the button to browse our plans!"
    try:
        with open("welcome.jpg", "rb") as photo:
            return await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=main_menu())
    except:
        return await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=main_menu())

# ============ START ============
async def start(update, context):
    chat_id = update.effective_chat.id
    
    if 'last_welcome' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['last_welcome'])
        except:
            pass
    
    msg = await send_welcome(chat_id, context)
    context.user_data['last_welcome'] = msg.message_id
    await delete_msg(context, chat_id, update.message.message_id, 5)

# ============ BUTTONS ============
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == "demo":
        msg = await query.message.reply_text("🎬 DEMO LINK:\nhttps://t.me/+gywxm8qaCkIzYzI1")
        await delete_msg(context, chat_id, msg.message_id, 30)

    elif query.data == "price":
        await query.message.edit_text("💰 PRICE LIST\n\nSelect your plan:", reply_markup=price_buttons())

    elif query.data.startswith("pay_"):
        plan = query.data.replace("pay_", "")
        context.user_data['selected_plan'] = plan
        
        try:
            with open("qr.jpg", "rb") as photo:
                await query.message.delete()
                msg = await query.message.reply_photo(
                    photo=photo,
                    caption=f"💳 Pay ₹{plan}\n\n⏳ QR valid for 10 minutes\n\n✅ Send Transaction ID after payment:",
                    reply_markup=back_button()
                )
                context.user_data['qr_msg_id'] = msg.message_id
                
                # ✅ QR DELETE AFTER 10 MINUTES + TIMEOUT MESSAGE
                async def qr_timeout():
                    await asyncio.sleep(600)  # 10 minutes
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
                        timeout_msg = await context.bot.send_message(
                            chat_id=chat_id,
                            text="⏳ PAYMENT TIMEOUT!\n\n❌ QR expired after 10 minutes.\n🔄 Please select a plan again.",
                            reply_markup=main_menu()
                        )
                        await delete_msg(context, chat_id, timeout_msg.message_id, 30)
                    except:
                        pass
                
                asyncio.create_task(qr_timeout())
                
        except:
            msg = await query.message.edit_text(f"💳 Pay ₹{plan}\n\nSend Transaction ID:", reply_markup=back_button())
            await delete_msg(context, chat_id, msg.message_id, 600)

    elif query.data == "contact":
        msg = await query.message.reply_text("📞 Contact: @its_cuteiii")
        await delete_msg(context, chat_id, msg.message_id, 30)

    elif query.data == "back":
        await query.message.delete()
        msg = await send_welcome(chat_id, context)
        context.user_data['last_welcome'] = msg.message_id

# ============ TRANSACTION ============
async def handle_transaction(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if 'selected_plan' not in context.user_data:
        msg = await update.message.reply_text("❌ Select a plan first!", reply_markup=main_menu())
        await delete_msg(context, chat_id, msg.message_id, 10)
        await delete_msg(context, chat_id, update.message.message_id, 5)
        return

    # Delete QR if exists
    if 'qr_msg_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['qr_msg_id'])
        except:
            pass
        del context.user_data['qr_msg_id']

    if check_transaction(text):
        msg = await update.message.reply_text("❌ This Transaction ID is already used!")
        await delete_msg(context, chat_id, msg.message_id, 10)
        await delete_msg(context, chat_id, update.message.message_id, 5)
        return

    plan = context.user_data['selected_plan']
    success = save_payment(user_id, text, plan)

    if success:
        await update.message.delete()
        
        # Delete old welcome
        if 'last_welcome' in context.user_data:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['last_welcome'])
            except:
                pass
        
        # Send link
        msg = await update.message.reply_text(
            f"✅ PAYMENT CONFIRMED! 🎉\n\n"
            f"Plan: ₹{plan}\n"
            f"Transaction: {text}\n\n"
            f"🔗 JOIN GROUP:\n{GROUP_LINK}\n\n"
            f"⚠️ Auto-delete in 30 seconds."
        )
        await delete_msg(context, chat_id, msg.message_id, 30)
        
        # Sab delete ke baad Welcome
        await asyncio.sleep(35)
        new_welcome = await send_welcome(chat_id, context)
        context.user_data['last_welcome'] = new_welcome.message_id
        
        del context.user_data['selected_plan']
    else:
        msg = await update.message.reply_text("❌ Payment failed! Contact @its_cuteiii")
        await delete_msg(context, chat_id, msg.message_id, 15)
        await delete_msg(context, chat_id, update.message.message_id, 5)

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
