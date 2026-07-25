import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("TOKEN")

# Flask for Render
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ])


def price_buttons():
    rows = [
        ("₹60 - 399 Videos", "pay_60"),
        ("₹89 - 499 Videos", "pay_89"),
        ("₹99 - 799 Videos", "pay_99"),
        ("₹130 - 1199 Videos", "pay_130"),
        ("₹149 - 2500 Group", "pay_149"),
        ("₹199 - 7999 Group", "pay_199"),
        ("₹249 - 14999 Group", "pay_249"),
        ("₹349 - Long Videos", "pay_349"),
        ("₹480 - Unlimited", "pay_480"),
    ]

    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in rows]
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back")])

    return InlineKeyboardMarkup(keyboard)


def price_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK TO PRICES", callback_data="price")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}!\n\nChoose an option below:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "price":
        await q.message.edit_text(
            "💰 PRICE LIST\n\nSelect your plan:",
            reply_markup=price_buttons()
        )

    elif q.data.startswith("pay_"):
        with open("qr.jpg", "rb") as photo:
            await q.message.reply_photo(
                photo=photo,
                caption=(
                    "💳 PAYMENT METHOD\n\n"
                    "📲 Scan the QR Code to make payment.\n\n"
                    "✅ After payment send screenshot to:\n"
                    "@its_cuteiii"
                ),
                reply_markup=price_back()
            )

    elif q.data == "demo":
        await q.message.edit_text(
            "🎬 DEMO LINK\n\n"
            "https://t.me/+1u-iqI31ORI2ZTQ1\n\n"
            "👆🏻 Check DEMO 👆🏻\n\n"
            "⏳ You have just 15 minutes...\n"
            "🔒 After that, this link will be blocked ❌",
            reply_markup=back_menu()
        )

    elif q.data == "contact":
        await q.message.edit_text(
            "📞 CONTACT\n\n"
            "Username: @its_cuteiii\n\n"
            "https://t.me/its_cuteiii",
            reply_markup=back_menu()
        )
    elif q.data == "back":
        await q.message.edit_text(
            "Choose an option:",
            reply_markup=main_menu()
        )


def main():
    threading.Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
