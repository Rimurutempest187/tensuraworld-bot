import json
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import json
import os

# Load user data
def load_users():
    if not os.path.exists("users.json"):
        # auto-create empty users.json if not exist
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    else:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)

# Save user data
def save_users(users):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
# Load character data by faction
def load_faction_data(faction):
    try:
        with open(f"{faction}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Load user data
def load_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save user data
def save_users(users):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# /start command
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {"coins": 1000, "characters": []}
        save_users(users)
        update.message.reply_text("🎉 Welcome to Tensura World! You've received 1000 coins to begin.")
    else:
        update.message.reply_text("👋 You're already registered. Use /store to start collecting!")

# /characters <faction>
def characters(update: Update, context: CallbackContext):
    faction = context.args[0] if context.args else "tempest"
    data = load_faction_data(faction)
    if not data:
        update.message.reply_text("❌ Faction not found.")
        return
    message = f"📜 Characters in {faction.capitalize()}:\n"
    for c in data:
        message += f"{c['id']} - {c['name']} ({c['rarity']})\n"
    update.message.reply_text(message)

# /store <faction>
def store(update: Update, context: CallbackContext):
    faction = context.args[0] if context.args else "tempest"
    data = load_faction_data(faction)
    if not data:
        update.message.reply_text("❌ Faction not found.")
        return
    message = f"🛒 Store - {faction.capitalize()}:\n"
    for c in data:
        message += f"{c['id']} - {c['name']} ({c['rarity']}) - {c['price']} coins\n"
    update.message.reply_text(message)

# /buy <id>
def buy(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    char_id = int(context.args[0]) if context.args else None
    all_factions = ["tempest", "demonlords", "humans", "holychurch", "eastern_empire", "dragons"]
    character = None

    for faction in all_factions:
        data = load_faction_data(faction)
        for c in data:
            if c["id"] == char_id:
                character = c
                break
        if character:
            break

    if not character:
        update.message.reply_text("❌ Character not found.")
        return

    if character["id"] in users[user_id]["characters"]:
        update.message.reply_text("⚠️ You already own this character.")
        return

    if users[user_id]["coins"] < character["price"]:
        update.message.reply_text("💸 Not enough coins.")
        return

    users[user_id]["coins"] -= character["price"]
    users[user_id]["characters"].append(character["id"])
    save_users(users)
    update.message.reply_text(f"✅ You bought {character['name']} for {character['price']} coins!")

# /bonus
def bonus(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    bonus_amount = random.randint(100, 300)
    users[user_id]["coins"] += bonus_amount
    save_users(users)
    update.message.reply_text(f"🎁 Daily Bonus: You received {bonus_amount} coins!")

# /leaderboard
def leaderboard(update: Update, context: CallbackContext):
    users = load_users()
    ranking = sorted(users.items(), key=lambda x: len(x[1]["characters"]), reverse=True)
    message = "🏆 Leaderboard - Top Collectors:\n"
    for i, (uid, data) in enumerate(ranking[:10], start=1):
        message += f"{i}. User {uid} - {len(data['characters'])} characters\n"
    update.message.reply_text(message)

# Main bot setup
def main():
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("characters", characters))
    dp.add_handler(CommandHandler("store", store))
    dp.add_handler(CommandHandler("buy", buy))
    dp.add_handler(CommandHandler("bonus", bonus))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

