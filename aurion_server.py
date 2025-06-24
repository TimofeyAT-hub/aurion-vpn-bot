
import os
import logging
import json
import random
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DEVELOPER_IDS = [int(x) for x in os.getenv("DEVELOPER_IDS", "").split(",") if x]
FREE_GROUP_ID = int(os.getenv("FREE_GROUP_ID", "-1002589194767"))
GAME_CHAT_ID = int(os.getenv("GAME_CHAT_ID", "-1002447009319"))
DATA_FILE = "users_data.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KASPI = os.getenv("KASPI")
SBER = os.getenv("SBER")

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def has_access(user_id, chat_id):
    if user_id in DEVELOPER_IDS:
        return True
    data = load_data()
    if str(user_id) in data:
        start = datetime.fromisoformat(data[str(user_id)]["start"])
        status = data[str(user_id)]["status"]
        if status == "active" or chat_id == FREE_GROUP_ID:
            return True
        elif datetime.now() - start <= timedelta(days=7):
            return True
    return chat_id == FREE_GROUP_ID

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.lower()
    if user_id in DEVELOPER_IDS or chat_id in [FREE_GROUP_ID, GAME_CHAT_ID]:
        access_granted = True
    else:
        access_granted = has_access(user_id, chat_id)
    if not access_granted:
        await update.message.reply_text("⏳ Ваш пробный период истёк. Пожалуйста, оплатите доступ через /pay.")
        return
    greetings = ["привет", "здравствуй", "йо", "ку", "hello", "hi", "hey"]
    if any(greet in text for greet in greetings):
        await update.message.reply_text("Приветствую тебя в мире Ауруса 🌌 Чем могу помочь?")
    else:
        await update.message.reply_text("👋 Бот получил ваше сообщение.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in DEVELOPER_IDS:
        await update.message.reply_text("👨‍💻 Панель разработчика активирована.")
    else:
        await update.message.reply_text("📚 Добро пожаловать в серверную версию Аурион 2.000")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {"start": datetime.now().isoformat(), "status": "demo"}
        save_data(data)
    payment_keyboard = [
        [InlineKeyboardButton("💰 Kaspi", callback_data="show_kaspi")],
        [InlineKeyboardButton("🏦 СБП", callback_data="show_sbp")],
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid:{user_id}")]
    ]
    await update.message.reply_text("💸 Выберите способ оплаты:", reply_markup=InlineKeyboardMarkup(payment_keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_kaspi":
        await query.message.reply_text(f"🇰🇿 Kaspi: {KASPI}")
    elif query.data == "show_sbp":
        await query.message.reply_text(f"🇷🇺 СБП (Сбер): {SBER}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL + TOKEN
    )

if __name__ == "__main__":
    main()
