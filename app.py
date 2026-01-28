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
from datetime import datetime, timedelta

# ---------- Command Handlers ----------

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)

    name = update.effective_user.full_name
    coins = user_data.get("coins", 0)
    collection_count = len(user_data.get("cards", []))

    await update.message.reply_text(
        f"👤 Player Info\n"
        f"🆔 ID: {user_id}\n"
        f"📛 Name: {name}\n"
        f"💰 Coins: {coins}\n"
        f"🎴 Collection: {collection_count} characters"
    )

async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)

    cards = user_data.get("cards", [])
    if not cards:
        await update.message.reply_text("❌ You don't own any characters yet.")
        return

    lines = ["🎴 Your Collection:"]
    for c in cards:
        lines.append(f"🆔 {c['id']} | {c['name']} ({c['rarity']})")

    text = "\n".join(lines)
    if len(text) > 4000:
        await update.message.reply_text(text[:4000])
    else:
        await update.message.reply_text(text)

# ---------- Smash with Cooldown ----------
async def smash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id)

    # Cooldown check
    last_smash = user_data.get("last_smash")
    now = datetime.now()

    if last_smash:
        last_time = datetime.strptime(last_smash, "%Y-%m-%d %H:%M:%S")
        if now - last_time < timedelta(minutes=1):
            remaining = 60 - int((now - last_time).seconds)
            await update.message.reply_text(
                f"⏳ Please wait {remaining} seconds before smashing again!"
            )
            return

    # Save new smash time
    user_data["last_smash"] = now.strftime("%Y-%m-%d %H:%M:%S")
    save_data(USER_FILE, users)

    # Smash logic (same as roll)
    characters = load_data(CHAR_FILE)
    if not characters:
        await update.message.reply_text("❌ No characters found in database.")
        return

    char = random.choice(characters)
    char_id = str(char.get("id"))
    owned_ids = [str(c.get("id")) for c in user_data.get("cards", [])]

    if char_id not in owned_ids:
        user_data["cards"].append(char)
        save_data(USER_FILE, users)
        msg = f"🎉 [NEW] You smashed and obtained {char.get('name')}! ({char.get('rarity')})"
    else:
        msg = f"🔄 You smashed {char.get('name')} again (Already owned)."

    image_url = char.get("image_url")
    if image_url:
        try:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=msg)
        except Exception as e:
            logger.error(f"Image Error: {e}")
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text(msg)


# ---------- Main ----------
def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN missing in environment variables!")
        return

    keep_alive()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("smash", smash))   # changed from roll
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("collection", collection))

    logger.info("🤖 Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

