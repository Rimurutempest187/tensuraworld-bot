import os, json, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ==========================
# 🔒 Security & Data Handling
# ==========================
DATA_FILE = "users.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Replit Secrets

def load_users():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# ==========================
# 🎲 Utility Functions
# ==========================
RARITY_EMOJIS = {"Common":"⚪","Rare":"🔵","Epic":"🟣","Legendary":"🟡"}

def summon_item():
    roll = random.randint(1,100)
    if roll <= 60:
        return {"name": random.choice(["Potion","Scroll"]), "rarity":"Common"}
    elif roll <= 85:
        return {"name": random.choice(["Sword","Armor","Gem"]), "rarity":"Rare"}
    elif roll <= 95:
        return {"name": random.choice(["Magic Staff","Dragon Scale"]), "rarity":"Epic"}
    else:
        return {"name": random.choice(["Excalibur","Phoenix Feather"]), "rarity":"Legendary"}

# ==========================
# 🏁 Core Commands
# ==========================
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {"coins":1000,"characters":[],"items":[],"guild":None,"rating":1000}
        save_users(users)
        update.message.reply_text("🎉 Welcome to RPG Bot! You received 1000 coins to begin.")
    else:
        update.message.reply_text("👋 You're already registered. Use /quest /battle /shop /inventory /leaderboard etc.")

# ==========================
# 📜 Quest System
# ==========================
def quest(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    reward = random.choice([150,300,500])
    item = summon_item()
    users[user_id]["coins"] += reward
    users[user_id]["items"].append(item)
    save_users(users)
    update.message.reply_text(
        f"📜 Quest Complete!\nReward: {reward} coins + {RARITY_EMOJIS[item['rarity']]} {item['rarity']} {item['name']}"
    )

# ==========================
# ⚔️ Battle System
# ==========================
def battle(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    enemy_power = random.randint(5,20)
    player_power = len(users[user_id]["characters"]) + users[user_id]["rating"]//100
    if player_power >= enemy_power:
        reward = random.randint(100,500)
        users[user_id]["coins"] += reward
        save_users(users)
        update.message.reply_text(f"⚔️ Victory! You earned {reward} coins.")
    else:
        update.message.reply_text("⚔️ Defeat... Better luck next time!")

# ==========================
# 🛒 Shop System
# ==========================
def shop(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🛍 Browse Items", callback_data="shop_browse")],
        [InlineKeyboardButton("💸 Buy Potion (200)", callback_data="shop_buy_potion")]
    ]
    update.message.reply_text("🛒 Shop Menu", reply_markup=InlineKeyboardMarkup(keyboard))

def shop_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    if query.data == "shop_browse":
        query.edit_message_text("🛍 Items:\n- Potion (200)\n- Sword (500)\n- Armor (800)")
    elif query.data == "shop_buy_potion":
        if users[user_id]["coins"] >= 200:
            users[user_id]["coins"] -= 200
            users[user_id]["items"].append({"name":"Potion","rarity":"Common"})
            save_users(users)
            query.edit_message_text("💸 You bought a Potion!")
        else:
            query.edit_message_text("⚠️ Not enough coins.")

# ==========================
# 📦 Inventory System
# ==========================
def inventory(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    items = users[user_id].get("items",[])
    if not items:
        update.message.reply_text("📦 Inventory empty.")
        return
    grouped = {"Common":[],"Rare":[],"Epic":[],"Legendary":[]}
    for i in items:
        grouped[i["rarity"]].append(i["name"])
    msg = "📦 <b>Your Inventory</b>\n\n"
    for rarity, lst in grouped.items():
        if lst:
            msg += f"{RARITY_EMOJIS[rarity]} <b>{rarity}</b>\n" + "\n".join([f"- {x}" for x in lst]) + "\n\n"
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏆 Leaderboard
# ==========================
def leaderboard(update: Update, context: CallbackContext):
    users = load_users()
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("coins",0), reverse=True)
    top10 = sorted_users[:10]
    msg = "🏆 <b>Global Leaderboard</b>\n" + "\n".join(
        [f"{i+1}. User {uid} - {data['coins']} coins" for i,(uid,data) in enumerate(top10)]
    )
    update.message.reply_text(msg, parse_mode="HTML")

# ==========================
# ⚔️ Guild Wars
# ==========================
def guildwars(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    guild = users[user_id].get("guild","No Guild")
    keyboard = [
        [InlineKeyboardButton("➕ Join War", callback_data="gw_join")],
        [InlineKeyboardButton("⚔️ Fight", callback_data="gw_fight")],
        [InlineKeyboardButton("🎁 Rewards", callback_data="gw_rewards")]
    ]
    update.message.reply_text(f"⚔️ Guild Wars\nGuild: {guild}", reply_markup=InlineKeyboardMarkup(keyboard))

def guildwars_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()
    if query.data == "gw_join":
        users[user_id]["guild_war"] = True
        save_users(users)
        query.edit_message_text("✅ Joined Guild War!")
    elif query.data == "gw_fight":
        if users[user_id].get("guild_war"):
            reward = 1200
            users[user_id]["coins"] += reward
            save_users(users)
            query.edit_message_text(f"⚔️ Victory! Earned {reward} coins.")
        else:
            query.edit_message_text("⚠️ Join war first.")
    elif query.data == "gw_rewards":
        query.edit_message_text("🎁 Rewards claimed!")

# ==========================
# 🚀 Main
# ==========================
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set in environment variables.")
        return

    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("quest", quest))
    dp.add_handler(CommandHandler("battle", battle))
    dp.add_handler(CommandHandler("shop", shop))
    dp.add_handler(CallbackQueryHandler(shop_buttons, pattern="^shop_"))
    dp.add_handler(CommandHandler("inventory", inventory))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("guildwars", guildwars))
    dp.add_handler(CallbackQueryHandler(guildwars_buttons, pattern="^gw_"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
