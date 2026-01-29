#!/usr/bin/env python3
import logging, json, random, os, threading
from typing import Any, Dict
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

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
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Files ----------
CHAR_FILE = "tempest.json"
USER_FILE = "users.json"

# ---------- Helper Functions ----------
def load_data(file: str) -> Any:
    with data_lock:
        if not os.path.exists(file):
            default = [] if file == CHAR_FILE else {}
            with open(file, "w", encoding="utf-8") as f: json.dump(default, f)
            return default
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return [] if file == CHAR_FILE else {}

def save_data(file: str, data: Any) -> None:
    with data_lock:
        with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(users: Dict, user_id: str) -> Dict:
    if user_id not in users:
        users[user_id] = {"cards": [], "coins": 100, "last_bonus": "", "last_smash": "", "avatar_url": ""}
    return users[user_id]

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n"
        "/smash 🎴 Get random character\n"
        "/store 🛒 View shop\n"
        "/buy <id> 💰 Purchase\n"
        "/myinfo 👤 Profile\n"
        "/collection 🎴 Your cards\n"
        "/bonus 🎁 Daily coins\n"
        "/bal 💰 Balance\n"
        "/setavatar <url> 📸 Avatar\n"
        "/leaderboard 🏆 Top players"
    )

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_data(USER_FILE); user_data = get_user_data(users, user_id)
    caption = (f"👤 Player Info\n🆔 {user_id}\n📛 {update.effective_user.full_name}\n"
               f"💰 Coins: {user_data['coins']}\n🎴 Collection: {len(user_data['cards'])}")
    if user_data["avatar_url"]:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=user_data["avatar_url"], caption=caption)
    else: await update.message.reply_text(caption)

async def setavatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("📸 Usage: /setavatar <image_url>")
    user_id = str(update.effective_user.id); users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id); user_data["avatar_url"] = context.args[0]
    save_data(USER_FILE, users); await update.message.reply_text("✅ Avatar updated!")

async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id); users = load_data(USER_FILE)
    cards = get_user_data(users, user_id)["cards"]
    if not cards: return await update.message.reply_text("❌ No characters yet.")
    await update.message.reply_text("\n".join([f"🆔 {c['id']} | {c['name']} ({c['rarity']})" for c in cards]))

async def smash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id); users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id); now = datetime.now()
    if user_data["last_smash"]:
        last_time = datetime.strptime(user_data["last_smash"], "%Y-%m-%d %H:%M:%S")
        if now - last_time < timedelta(minutes=1):
            return await update.message.reply_text("⏳ Wait before smashing again!")
    user_data["last_smash"] = now.strftime("%Y-%m-%d %H:%M:%S"); save_data(USER_FILE, users)
    char = random.choice(load_data(CHAR_FILE)); msg = f"🎉 You got {char['name']} ({char['rarity']})"
    if str(char["id"]) not in [str(c["id"]) for c in user_data["cards"]]:
        user_data["cards"].append(char); save_data(USER_FILE, users)
    if char["image_url"]: await context.bot.send_photo(chat_id=update.effective_chat.id, photo=char["image_url"], caption=msg)
    else: await update.message.reply_text(msg)

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chars = load_data(CHAR_FILE)
    await update.message.reply_text("\n".join([f"🆔 {c['id']} | {c['name']} ({c['rarity']}) - 💰 {c['price']}" for c in chars]))

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /buy <id>")
    char_id = context.args[0]; chars = load_data(CHAR_FILE); users = load_data(USER_FILE)
    user_id = str(update.effective_user.id); user_data = get_user_data(users, user_id)
    char = next((c for c in chars if str(c["id"]) == char_id), None)
    if not char: return await update.message.reply_text("❌ Not found.")
    if any(str(c["id"]) == char_id for c in user_data["cards"]): return await update.message.reply_text("🔄 Already owned.")
    if user_data["coins"] < char["price"]: return await update.message.reply_text("💸 Not enough coins.")
    user_data["coins"] -= char["price"]; user_data["cards"].append(char); save_data(USER_FILE, users)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=char["image_url"], caption=f"🎉 Bought {char['name']}!")

async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id); users = load_data(USER_FILE)
    await update.message.reply_text(f"💰 Balance: {get_user_data(users, user_id)['coins']} coins")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id); users = load_data(USER_FILE)
    user_data = get_user_data(users, user_id); today = datetime.now().strftime("%Y-%m-%d")
    if user_data["last_bonus"] == today: return await update.message.reply_text("❌ Already claimed today.")
    user_data["last_bonus"] = today; user_data["coins"] += 50; save_data(USER_FILE, users)
    await update.message.reply_text("🎁 Daily bonus +50 coins!")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USER_FILE)
    ranking = sorted(users.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    lines = ["🏆 Leaderboard:"]
    for i, (uid, data) in enumerate(ranking, 1):
        lines.append(f"{i}. {data.get('coins',0)} coins - ID {uid}")
    await update.message.reply_text("\n".join(lines))

# ---------- Main ----------
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN missing in environment variables!")
        return

    # Keep-alive server
    keep_alive()

    # Build Telegram bot app
    app = ApplicationBuilder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("smash", smash))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("setavatar", setavatar))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    logger.info("🤖 Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

