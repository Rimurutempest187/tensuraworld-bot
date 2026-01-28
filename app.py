#!/usr/bin/env python3
import logging
import json
import random
import os
import threading
from typing import Any, Dict
from flask import Flask
from threading import Thread
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

# ---------- Flask Keep-Alive ----------
flask_app = Flask(__name__)
data_lock = threading.Lock()

@flask_app.route("/")
def home():
    return "Bot is alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

def keep_alive():
    thread = Thread(target=run_web_server)
    thread.daemon = True
    thread.start()

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Files ----------
CHAR_FILE = "characters.json"
USER_FILE = "users.json"

# ---------- Helper Functions ----------
def load_data(file: str) -> Any:
    with data_lock:
        if not os.path.exists(file):
            default = [] if file == CHAR_FILE else {}
            with open(file, "w", encoding="utf-8") as f:
                json.dump(default, f)
            return default
        with open(file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] if file == CHAR_FILE else {}

def save_data(file: str, data: Any) -> None:
    with data_lock:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(users: Dict, user_id: str) -> Dict:
    if user_id not in users:
        users[user_id] = {
            "cards": [],
            "coins": 100,
            "last_bonus": ""
        }
    return users[user_id]

# ---------- Command Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome to the Character Collection Bot!\n\n"
        "🎮 Commands:\n"
        "/roll - Roll a new character (Free)\n"
        "/bal - Check your coin balance\n"
        "/bonus - Claim your daily 50 coins\n"
        "/store - View character list\n"
        "/buy <id> - Buy a specific character"
    )

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    characters = load_data(CHAR_FILE)
    
    if not characters:
        await update.message.reply_text("❌ No characters found in database.")
        return

    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)

    char = random.choice(characters)
    char_id = str(char.get("id"))
    
    owned_ids = [str(c.get("id")) for c in user_data.get("cards", [])]
    
    if char_id not in owned_ids:
        user_data["cards"].append(char)
        save_data(USER_FILE, users)
        msg = f"🎉 [NEW] You obtained {char.get('name')}! ({char.get('rarity')})"
    else:
        msg = f"🔄 You rolled {char.get('name')} again (Already owned)."

    image_url = char.get("image_url")
    if image_url:
        try:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=msg)
        except Exception as e:
            logger.error(f"Image Error: {e}")
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data.get("last_bonus") == today:
        await update.message.reply_text("🎁 You've already claimed your bonus today. Come back tomorrow!")
        return

    user_data["coins"] += 50
    user_data["last_bonus"] = today
    save_data(USER_FILE, users)
    await update.message.reply_text(f"🎉 +50 coins added! Current balance: {user_data['coins']} 💰")

async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)
    await update.message.reply_text(f"💰 Balance: {user_data['coins']} coins.\n🎴 Cards Owned: {len(user_data['cards'])}")

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    characters = load_data(CHAR_FILE)
    if not characters:
        await update.message.reply_text("🛒 Store is currently empty.")
        return

    lines = ["🛒 **Character Store** (Use /buy <id>)"]
    for c in characters:
        price = c.get("price", 100)
        lines.append(f"🆔 `{c['id']}` | {c['name']} - 💰 {price}")
    
    text = "\n".join(lines)
    if len(text) > 4000:
        await update.message.reply_text(text[:4000])
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /buy <character_id>")
        return

    user_id = str(update.effective_user.id)
    char_id_to_buy = str(context.args[0])
    
    users = load_data(USER_FILE)
    characters = load_data(CHAR_FILE)
    user_data = get_user_data(users, user_id)

    char = next((c for c in characters if str(c.get("id")) == char_id_to_buy), None)

    if not char:
        await update.message.reply_text("❌ Invalid Character ID.")
        return

    price = char.get("price", 100)
    if user_data["coins"] < price:
        await update.message.reply_text(f"❌ Inadequate coins! Need {price} coins.")
        return

    owned_ids = [str(c.get("id")) for c in user_data.get("cards", [])]
    if char_id_to_buy in owned_ids:
        await update.message.reply_text("✅ You already own this character.")
        return

    user_data["coins"] -= price
    user_data["cards"].append(char)
    save_data(USER_FILE, users)

    await update.message.reply_text(f"🛒 Purchased {char['name']} for {price} coins!")

# ---------- Main ----------
def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN missing in environment variables!")
        return

    keep_alive()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("buy", buy))

    logger.info("🤖 Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
