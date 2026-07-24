import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = ""

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎬 DEMO", callback_data="demo")],
        [InlineKeyboardButton("💰 PRICE LIST", callback_data="price")],
        [InlineKeyboardButton("📞 CONTACT", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu():
    keyboard = [
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def price_buttons():
    keyboard = [
        [InlineKeyboardButton("₹60 - 399 Videos", callback_data="pay_60")],
        [InlineKeyboardButton("₹89 - 499 Videos", callback_data="pay_89")],
        [InlineKeyboardButton("₹99 - 799 Videos", callback_data="pay_99")],
        [InlineKeyboardButton("₹130 - 1199 Videos", callback_data="pay_130")],
        [InlineKeyboardButton("₹149 - 2500 Group", callback_data="pay_149")],
        [InlineKeyboardButton("₹199 - 7999 Group", callback_data="pay_199")],
        [InlineKeyboardButton("₹249 - 14999 Group", callback_data="pay_249")],
        [InlineKeyboardButton("₹349 - Long Videos", callback_data="pay_349")],
        [InlineKeyboardButton("₹480 - Unlimited", callback_data="pay_480")],
        [InlineKeyboardButton("🔙 BACK", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def price_back():
    keyboard = [
        [InlineKeyboardButton("🔙 BACK TO PRICES", callback_data="price")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\nChoose an option below:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "price":
        await query.message.edit_text(
            "💰 PRICE LIST\n\nSelect your plan:",
            reply_markup=price_buttons()
        )

    elif query.data.startswith("pay_"):
        plans = {
            "pay_60": "₹60 - 399 Videos",
            "pay_89": "₹89 - 499 Videos",
            "pay_99": "₹99 - 799 Videos",
            "pay_130": "₹130 - 1199 Videos",
            "pay_149": "₹149 - 2500 Group",
            "pay_199": "₹199 - 7999 Group",
            "pay_249": "₹249 - 14999 Group",
            "pay_349": "₹349 - Long Videos",
            "pay_480": "₹480 - Unlimited"
        }

        selected_plan = plans.get(query.data, "Selected Plan")

        try:
            with open("qr.jpg", "rb") as qr:
                await query.message.reply_photo(
                    photo=qr,
                    caption=f"💳 Payment for: {selected_plan}",
                    reply_markup=price_back()
                )
        except FileNotFoundError:
            await query.message.edit_text(
                f"💳 {selected_plan}\n\nContact @yourusername for payment.",
                reply_markup=price_back()
            )

    elif query.data == "back":
        await query.message.edit_text(
            "👋 Welcome back!\n\nChoose an option:",
            reply_markup=main_menu()
        )

    elif query.data == "demo":
        await query.message.edit_text(
            "🎬 Demo\n\nThis is a demo.",
            reply_markup=back_menu()
        )

    elif query.data == "contact":
        await query.message.edit_text(
            "📞 Contact\n\nTelegram: @its_cuteiii",
            reply_markup=back_menu()
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
