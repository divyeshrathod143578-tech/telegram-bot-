import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("TOKEN")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back")]])

def price_buttons():
    rows = [
        ("₹60 - 399 Videos","pay_60"),
        ("₹89 - 499 Videos","pay_89"),
        ("₹99 - 799 Videos","pay_99"),
        ("₹130 - 1199 Videos","pay_130"),
        ("₹149 - 2500 Group","pay_149"),
        ("₹199 - 7999 Group","pay_199"),
        ("₹249 - 14999 Group","pay_249"),
        ("₹349 - Long Videos","pay_349"),
        ("₹480 - Unlimited","pay_480"),
    ]
    kb=[[InlineKeyboardButton(t,callback_data=c)] for t,c in rows]
    kb.append([InlineKeyboardButton("🔙 BACK",callback_data="back")])
    return InlineKeyboardMarkup(kb)

def price_back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK TO PRICES",callback_data="price")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}!\n\nChoose an option below:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if q.data=="price":
        await q.message.edit_text("💰 PRICE LIST\n\nSelect your plan:",reply_markup=price_buttons())
    elif q.data.startswith("pay_"):
        await q.message.edit_text("💳 Payment details.\n\nUpload qr.jpg later if needed.",reply_markup=price_back())
    elif q.data=="back":
        elif q.data=="demo":
    await q.message.edit_text(
        "🎬 DEMO LINKS\n\n"
        "Group 1: https://t.me/+1u-iqI31ORI2ZTQ1"
        "Group 2: https://t.me/yourgroup2",
        reply_markup=back_menu()
    )
        await q.message.edit_text("🎬 Demo",reply_markup=back_menu())
    elif q.data=="contact":
        await q.message.edit_text("📞 Contact: @its_cuteiii",reply_markup=back_menu())

def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__=="__main__":
    main()
