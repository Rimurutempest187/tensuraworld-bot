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
# ❤️ Fun Social Commands
# ==========================

def smash(update: Update, context: CallbackContext):
    char = random_character()
    keyboard = [
        [InlineKeyboardButton("🔥 Smash", callback_data=f"smash_yes_{char['id']}")],
        [InlineKeyboardButton("❌ Pass", callback_data=f"smash_no_{char['id']}")]
    ]
    update.message.reply_text(
        f"Random pick: {char['name']} ({char['rarity']})\nWould you smash?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def marry(update: Update, context: CallbackContext):
    char = random_character()
    keyboard = [
        [InlineKeyboardButton("💍 Marry", callback_data=f"marry_yes_{char['id']}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"marry_no_{char['id']}")]
    ]
    update.message.reply_text(
        f"Random pick: {char['name']} ({char['rarity']})\nWould you marry?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def propose(update: Update, context: CallbackContext):
    char = random_character()
    keyboard = [
        [InlineKeyboardButton("💌 Propose", callback_data=f"propose_yes_{char['id']}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"propose_no_{char['id']}")]
    ]
    update.message.reply_text(
        f"You are proposing to {char['name']} ({char['rarity']}) 💖",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# ❤️ Fun Social Callback Handler
# ==========================
def fun_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    action, choice, char_id = query.data.split("_")
    char_id = int(char_id)

    # demo character pool
    pool = [
        {"id":1,"name":"Rimuru","rarity":"Legendary"},
        {"id":2,"name":"Shuna","rarity":"Epic"},
        {"id":3,"name":"Benimaru","rarity":"Epic"},
        {"id":4,"name":"Gobta","rarity":"Rare"},
        {"id":5,"name":"Ranga","rarity":"Rare"}
    ]
    char = next((c for c in pool if c["id"] == char_id), None)

    if not char:
        query.edit_message_text("❌ Character not found.")
        return

    if action == "smash":
        if choice == "yes":
            query.edit_message_text(f"🔥 You smashed {char['name']} ({char['rarity']})!")
        else:
            query.edit_message_text(f"❌ You passed on {char['name']}.")
    elif action == "marry":
        if choice == "yes":
            users[user_id]["married"].append(char["name"])
            save_users(users)
            query.edit_message_text(f"💍 You married {char['name']}! Congratulations 🎉")
        else:
            query.edit_message_text(f"❌ You rejected {char['name']}.")
    elif action == "propose":
        if choice == "yes":
            accepted = random.choice([True, False])
            if accepted:
                query.edit_message_text(f"💌 {char['name']} accepted your proposal 💖")
            else:
                query.edit_message_text(f"💔 {char['name']} rejected your proposal...")
        else:
            query.edit_message_text("❌ Proposal cancelled.")

# ==========================
# 👤 Profile System
# ==========================
def profile(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    data = users[user_id]
    coins = data.get("coins", 0)
    items = len(data.get("items", []))
    chars = len(data.get("characters", []))
    guild = data.get("guild", "No Guild")
    rating = data.get("rating", 1000)
    married = data.get("married", [])

    msg = f"""
👤 <b>Player Profile</b>

💰 Coins: {coins}
📦 Items: {items}
🎴 Characters: {chars}
🏰 Guild: {guild}
⭐ Rating: {rating}
💍 Married: {", ".join(married) if married else "None"}
    """

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🎯 Missions System
# ==========================
def missions(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example missions
    mission_list = [
        {"id":1, "task":"Complete 1 Quest", "reward":200},
        {"id":2, "task":"Win 1 Battle", "reward":300},
        {"id":3, "task":"Buy an Item from Shop", "reward":150}
    ]

    # Save missions to user if not already
    if "missions" not in users[user_id]:
        users[user_id]["missions"] = {m["id"]:False for m in mission_list}
        save_users(users)

    msg = "🎯 <b>Daily Missions</b>\n\n"
    keyboard = []
    for m in mission_list:
        status = "✅ Completed" if users[user_id]["missions"].get(m["id"]) else "❌ Not Done"
        msg += f"{m['id']}. {m['task']} → {status}\nReward: {m['reward']} coins\n\n"
        if not users[user_id]["missions"].get(m["id"]):
            keyboard.append([InlineKeyboardButton(f"Claim {m['reward']} coins", callback_data=f"mission_claim_{m['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    update.message.reply_text(msg.strip(), parse_mode="HTML", reply_markup=reply_markup)

# ==========================
# 🎯 Missions Callback Handler
# ==========================
def missions_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    if user_id not in users:
        query.edit_message_text("❌ Please use /start first.")
        return

    if query.data.startswith("mission_claim_"):
        mission_id = int(query.data.split("_")[2])
        # Example mission rewards
        rewards = {1:200, 2:300, 3:150}
        if not users[user_id]["missions"].get(mission_id):
            users[user_id]["coins"] += rewards[mission_id]
            users[user_id]["missions"][mission_id] = True
            save_users(users)
            query.edit_message_text(f"🎁 Mission {mission_id} completed!\nYou received {rewards[mission_id]} coins.")
        else:
            query.edit_message_text("⚠️ Mission already completed.")

# ==========================
# 🎰 Gacha System
# ==========================
def gacha(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Cost per summon
    summon_cost = 500
    if users[user_id]["coins"] < summon_cost:
        update.message.reply_text("⚠️ Not enough coins for gacha summon (500 needed).")
        return

    # Deduct coins
    users[user_id]["coins"] -= summon_cost

    # Summon random item/character
    roll = random.randint(1,100)
    if roll <= 60:
        rarity = "Common"
        reward = random.choice(["Potion","Scroll","Gobta"])
    elif roll <= 85:
        rarity = "Rare"
        reward = random.choice(["Sword","Armor","Ranga"])
    elif roll <= 95:
        rarity = "Epic"
        reward = random.choice(["Magic Staff","Dragon Scale","Shuna","Benimaru"])
    else:
        rarity = "Legendary"
        reward = random.choice(["Excalibur","Phoenix Feather","Rimuru"])

    # Save reward
    users[user_id]["items"].append({"name":reward,"rarity":rarity})
    save_users(users)

    # UI message
    msg = f"""
🎰 <b>Gacha Summon</b>
You spent 500 coins...

✨ Result: {RARITY_EMOJIS[rarity]} <b>{rarity}</b> {reward}
    """

    keyboard = [
        [InlineKeyboardButton("🎰 Summon Again (500)", callback_data="gacha_again")],
        [InlineKeyboardButton("📦 View Inventory", callback_data="gacha_inventory")]
    ]
    update.message.reply_text(msg.strip(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# 🎰 Gacha Callback Handler
# ==========================
def gacha_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    if query.data == "gacha_again":
        # Call gacha again
        gacha(query, context)
    elif query.data == "gacha_inventory":
        # Show inventory
        items = users[user_id].get("items",[])
        if not items:
            query.edit_message_text("📦 Inventory empty.")
            return
        grouped = {"Common":[],"Rare":[],"Epic":[],"Legendary":[]}
        for i in items:
            grouped[i["rarity"]].append(i["name"])
        msg = "📦 <b>Your Inventory</b>\n\n"
        for rarity, lst in grouped.items():
            if lst:
                msg += f"{RARITY_EMOJIS[rarity]} <b>{rarity}</b>\n" + "\n".join([f"- {x}" for x in lst]) + "\n\n"
        query.edit_message_text(msg.strip(), parse_mode="HTML")


# ==========================
# 🏅 Achievements System
# ==========================
def achievements(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    data = users[user_id]

    # Track stats
    quests = data.get("quests_done", 0)
    battles = data.get("battles_won", 0)
    gacha_pulls = len(data.get("items", []))
    marriages = len(data.get("married", []))

    # Achievement conditions
    achievement_list = [
        {"name":"Novice Adventurer","condition":quests>=1,"desc":"Complete your first quest"},
        {"name":"Battle Rookie","condition":battles>=1,"desc":"Win your first battle"},
        {"name":"Collector","condition":gacha_pulls>=5,"desc":"Summon 5 items via gacha"},
        {"name":"Lover","condition":marriages>=1,"desc":"Marry a character"}
    ]

    msg = "🏅 <b>Your Achievements</b>\n\n"
    for ach in achievement_list:
        status = "✅ Unlocked" if ach["condition"] else "❌ Locked"
        msg += f"{ach['name']} → {status}\n{ach['desc']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 🔧 Upgrade System
# ==========================
def upgrade(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    items = users[user_id].get("items", [])
    if not items:
        update.message.reply_text("📦 No items to upgrade.")
        return

    # Show first item for demo
    item = random.choice(items)
    keyboard = [
        [InlineKeyboardButton("🔧 Upgrade", callback_data=f"upgrade_{item['name']}")]
    ]
    update.message.reply_text(
        f"Choose item to upgrade:\n{RARITY_EMOJIS[item['rarity']]} {item['rarity']} {item['name']}\nCost: 300 coins",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def upgrade_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    if user_id not in users:
        query.edit_message_text("❌ Please use /start first.")
        return

    item_name = query.data.split("_")[1]
    items = users[user_id].get("items", [])
    item = next((i for i in items if i["name"] == item_name), None)

    if not item:
        query.edit_message_text("❌ Item not found.")
        return

    if users[user_id]["coins"] < 300:
        query.edit_message_text("⚠️ Not enough coins to upgrade.")
        return

    # Deduct coins
    users[user_id]["coins"] -= 300

    # Success chance
    success = random.choice([True, False, True])  # 66% success
    if success:
        # Upgrade rarity
        rarity_order = ["Common","Rare","Epic","Legendary"]
        current_index = rarity_order.index(item["rarity"])
        if current_index < len(rarity_order)-1:
            item["rarity"] = rarity_order[current_index+1]
            save_users(users)
            query.edit_message_text(f"✅ Upgrade successful!\nNew rarity: {RARITY_EMOJIS[item['rarity']]} {item['rarity']} {item['name']}")
        else:
            query.edit_message_text("⚠️ Item is already Legendary, cannot upgrade further.")
    else:
        query.edit_message_text("❌ Upgrade failed... Better luck next time!")


# ==========================
# 📅 Daily Login Bonus System
# ==========================
import datetime

def daily(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    today = datetime.date.today().isoformat()
    last_claim = users[user_id].get("last_daily", None)
    streak = users[user_id].get("daily_streak", 0)

    if last_claim == today:
        update.message.reply_text("⚠️ You already claimed your daily bonus today.")
        return

    # Update streak
    if last_claim == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
        streak += 1
    else:
        streak = 1

    users[user_id]["daily_streak"] = streak
    users[user_id]["last_daily"] = today

    # Reward scaling with streak
    reward = 100 * streak
    users[user_id]["coins"] += reward
    save_users(users)

    msg = f"""
📅 <b>Daily Login Bonus</b>
Streak: {streak} days
Reward: 💰 {reward} coins
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📜 Quest Log System
# ==========================
def quest(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    reward = random.choice([150,300,500])
    item = summon_item()

    users[user_id]["coins"] += reward
    users[user_id]["items"].append(item)

    # Track quest history
    if "quest_log" not in users[user_id]:
        users[user_id]["quest_log"] = []
    users[user_id]["quest_log"].append({
        "date": datetime.date.today().isoformat(),
        "reward_coins": reward,
        "item": item
    })

    # Count quests done
    users[user_id]["quests_done"] = users[user_id].get("quests_done", 0) + 1

    save_users(users)

    update.message.reply_text(
        f"📜 Quest Complete!\nReward: {reward} coins + {RARITY_EMOJIS[item['rarity']]} {item['rarity']} {item['name']}"
    )

def questlog(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users or "quest_log" not in users[user_id] or not users[user_id]["quest_log"]:
        update.message.reply_text("📜 No quests completed yet.")
        return

    log = users[user_id]["quest_log"][-5:]  # show last 5 quests
    msg = "📜 <b>Your Quest Log</b>\n\n"
    for q in log:
        msg += f"🗓 {q['date']} → 💰 {q['reward_coins']} coins + {RARITY_EMOJIS[q['item']['rarity']]} {q['item']['rarity']} {q['item']['name']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏰 Guild Profile System
# ==========================
def guildprofile(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    data = users[user_id]
    guild = data.get("guild", "No Guild")
    guild_wars = data.get("guild_wars", 0)
    guild_wins = data.get("guild_wins", 0)
    guild_rewards = data.get("guild_rewards", 0)

    msg = f"""
🏰 <b>Guild Profile</b>

Guild: {guild}
⚔️ Wars Joined: {guild_wars}
🏆 Wars Won: {guild_wins}
🎁 Rewards Earned: {guild_rewards} coins
    """

]
update.message.reply_text("🏠 <b>Main Menu</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
# ==========================
# 📊 Player Stats System
# ==========================
def stats(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    data = users[user_id]

    coins = data.get("coins", 0)
    items = len(data.get("items", []))
    chars = len(data.get("characters", []))
    guild = data.get("guild", "No Guild")
    rating = data.get("rating", 1000)

    quests = data.get("quests_done", 0)
    battles = data.get("battles_won", 0)
    gacha_pulls = len(data.get("items", []))
    upgrades = data.get("upgrades_done", 0)
    streak = data.get("daily_streak", 0)
    marriages = len(data.get("married", []))
    guild_wars = data.get("guild_wars", 0)
    guild_wins = data.get("guild_wins", 0)

    msg = f"""
📊 <b>Player Stats</b>

👤 User: {update.effective_user.first_name}
💰 Coins: {coins}
🎴 Characters: {chars}
📦 Items: {items}
🏰 Guild: {guild}
⭐ Rating: {rating}

📜 Quests Completed: {quests}
⚔️ Battles Won: {battles}
🎰 Gacha Pulls: {gacha_pulls}
🔧 Upgrades Done: {upgrades}
📅 Daily Streak: {streak} days
💍 Marriages: {marriages}
⚔️ Guild Wars Joined: {guild_wars}
🏆 Guild Wars Won: {guild_wins}
    """
- Always align emojis + text for clean look.
- Separate sections with line breaks for readability.

### 4. **Consistent Layout**
- Every command output should follow a **header → stats → actions** pattern:
- Header: bold + emoji  
- Stats: list with emojis  
- Actions: inline buttons  

Example for `/gacha`:
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏠 Main Menu System
# ==========================
def mainmenu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("⚔️ Battle", callback_data="menu_battle"),
         InlineKeyboardButton("📜 Quest", callback_data="menu_quest")],
        [InlineKeyboardButton("🛒 Shop", callback_data="menu_shop"),
         InlineKeyboardButton("🎰 Gacha", callback_data="menu_gacha")],
        [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
         InlineKeyboardButton("📊 Stats", callback_data="menu_stats")],
        [InlineKeyboardButton("🏅 Achievements", callback_data="menu_achievements"),
         InlineKeyboardButton("📅 Daily", callback_data="menu_daily")],
        [InlineKeyboardButton("📜 Quest Log", callback_data="menu_questlog"),
         InlineKeyboardButton("🏰 Guild Profile", callback_data="menu_guildprofile")],
        [InlineKeyboardButton("❤️ Smash/Marry/Propose", callback_data="menu_social")]
    ]

    update.message.reply_text(
        "🏠 <b>Main Menu</b>\nChoose your adventure:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# 🏠 Main Menu Callback Handler
# ==========================
def mainmenu_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data

    if choice == "menu_battle":
        battle(query, context)
    elif choice == "menu_quest":
        quest(query, context)
    elif choice == "menu_shop":
        shop(query, context)
    elif choice == "menu_gacha":
        gacha(query, context)
    elif choice == "menu_profile":
        profile(query, context)
    elif choice == "menu_stats":
        stats(query, context)
    elif choice == "menu_achievements":
        achievements(query, context)
    elif choice == "menu_daily":
        daily(query, context)
    elif choice == "menu_questlog":
        questlog(query, context)
    elif choice == "menu_guildprofile":
        guildprofile(query, context)
    elif choice == "menu_social":
        query.edit_message_text("❤️ Use /smash, /marry, /propose for fun social commands!")

# ==========================
# ❓ Help System
# ==========================
def help_command(update: Update, context: CallbackContext):
    msg = """
❓ <b>Help Menu</b>

🏁 <b>Core RPG</b>
- /start → Register & get 1000 coins
- /quest → Complete quest for coins + item
- /battle → Fight enemy for coins
- /shop → Open shop menu
- /inventory → Show your items
- /leaderboard → Global top 10 players
- /guildwars → Join/fight/reward in guild wars
- /characters <faction> → View faction characters
- /store <faction> → Buy faction characters

❤️ <b>Social Fun</b>
- /smash → Smash or pass random character
- /marry → Marry random character
- /propose → Propose to random character

👤 <b>Player Systems</b>
- /profile → Show player profile
- /missions → Daily missions with rewards
- /gacha → Random summon system
- /achievements → Unlock milestones
- /upgrade → Enhance items/characters
- /daily → Claim daily login bonus
- /questlog → View quest history
- /guildprofile → Show guild info
- /stats → Overall player stats
- /mainmenu → Central hub menu

❓ <b>Help</b>
- /help → Show this guide
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# ⚙️ Settings System
# ==========================
def settings(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Default settings if not exist
    if "settings" not in users[user_id]:
        users[user_id]["settings"] = {
            "sound": True,
            "notifications": True,
            "theme": "Light"
        }
        save_users(users)

    s = users[user_id]["settings"]
    keyboard = [
        [InlineKeyboardButton(f"🔊 Sound: {'On' if s['sound'] else 'Off'}", callback_data="set_sound")],
        [InlineKeyboardButton(f"🔔 Notifications: {'On' if s['notifications'] else 'Off'}", callback_data="set_notifications")],
        [InlineKeyboardButton(f"🎨 Theme: {s['theme']}", callback_data="set_theme")]
    ]

    msg = "⚙️ <b>Settings</b>\n\nCustomize your experience:"
    update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# ⚙️ Settings Callback Handler
# ==========================
def settings_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()
    s = users[user_id]["settings"]

    if query.data == "set_sound":
        s["sound"] = not s["sound"]
        query.edit_message_text(f"🔊 Sound toggled → {'On' if s['sound'] else 'Off'}")
    elif query.data == "set_notifications":
        s["notifications"] = not s["notifications"]
        query.edit_message_text(f"🔔 Notifications toggled → {'On' if s['notifications'] else 'Off'}")
    elif query.data == "set_theme":
        s["theme"] = "Dark" if s["theme"] == "Light" else "Light"
        query.edit_message_text(f"🎨 Theme changed → {s['theme']}")

    users[user_id]["settings"] = s
    save_users(users)

# ==========================
# ℹ️ About System
# ==========================
def about(update: Update, context: CallbackContext):
    msg = """
ℹ️ <b>About This Bot</b>

🤖 Bot Name: RPG Adventure Bot
📌 Version: v1.0.0
👨‍💻 Developer: Rimuru
🏗 Built With: Python + python-telegram-bot
☁️ Hosted On: Cloud (Replit/Fly.io/Railway/Render)

🎮 Features:
- RPG Core Systems (quests, battles, shop, inventory, guild wars)
- Social Fun (smash, marry, propose)
- Player Progression (profile, missions, gacha, achievements, upgrade, daily, questlog, stats)
- UI/UX Polish (inline menus, emoji badges, rich formatting)

💡 Goal:
Deliver a fun, interactive, and polished RPG experience inside Telegram.
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 🙏 Credits System
# ==========================
def credits(update: Update, context: CallbackContext):
    msg = """
🙏 <b>Credits</b>

👨‍💻 <b>Developer</b>
- Rimuru

🛠 <b>Contributors</b>
- Community testers
- Anime/Game lore curators
- UI/UX feedback providers

🎮 <b>Special Thanks</b>
- python-telegram-bot library maintainers
- Cloud hosting platforms (Replit, Fly.io, Railway, Render)
- Open-source community for inspiration

💡 <b>Supporters</b>
- Friends & testers who helped polish the bot
- Early players who gave feedback

✨ <i>This bot was built with passion for RPG mechanics, anime/game lore, and interactive Telegram experiences.</i>
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📰 News / Announcements System
# ==========================
def news(update: Update, context: CallbackContext):
    # Example static news list (can be dynamic later)
    news_list = [
        {"date":"2026-01-25","title":"🎉 New Gacha Characters","desc":"Added 10 new Epic & Legendary characters to summon pool."},
        {"date":"2026-01-26","title":"⚔️ Guild Wars Update","desc":"Guild wars now reward bonus coins for consecutive wins."},
        {"date":"2026-01-27","title":"📅 Daily Bonus Buff","desc":"Daily streak rewards increased by 20% for all players."}
    ]

    msg = "📰 <b>Game News & Updates</b>\n\n"
    for n in news_list:
        msg += f"🗓 {n['date']}\n{n['title']}\n{n['desc']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 🎉 Events System
# ==========================
def events(update: Update, context: CallbackContext):
    # Example static events list (can be dynamic later)
    events_list = [
        {"name":"🔥 Dragon Hunt","date":"2026-02-01 to 2026-02-07","desc":"Defeat dragons in quests to earn rare scales.","reward":"Epic Dragon Scale"},
        {"name":"💖 Valentine Special","date":"2026-02-14","desc":"Marry/propose characters during Valentine to earn bonus coins.","reward":"500 coins"},
        {"name":"⚔️ Guild War Season","date":"2026-03-01 to 2026-03-15","desc":"Top guilds win legendary rewards.","reward":"Legendary Weapon"}
    ]

    msg = "🎉 <b>Limited-Time Events</b>\n\n"
    for e in events_list:
        msg += f"{e['name']}\n🗓 {e['date']}\n{e['desc']}\n🎁 Reward: {e['reward']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 📝 Patch Notes System
# ==========================
def patchnotes(update: Update, context: CallbackContext):
    # Example static patch notes list (can be dynamic later)
    patch_list = [
        {"version":"v1.0.1","date":"2026-01-20","changes":[
            "⚔️ Battle rewards balanced (less coins, more XP)",
            "📜 Quest log now shows last 5 quests",
            "🎰 Gacha rates adjusted (Epic +5%, Legendary +2%)"
        ]},
        {"version":"v1.0.2","date":"2026-01-25","changes":[
            "🏅 Achievements system added",
            "🔧 Upgrade system success chance increased to 66%",
            "📅 Daily streak rewards scale better"
        ]},
        {"version":"v1.0.3","date":"2026-01-29","changes":[
            "🏰 Guild profile system added",
            "📊 Stats command added",
            "⚙️ Settings menu polished with inline buttons"
        ]}
    ]

    msg = "📝 <b>Patch Notes</b>\n\n"
    for p in patch_list:
        msg += f"📌 Version: {p['version']} ({p['date']})\n"
        for c in p["changes"]:
            msg += f"- {c}\n"
        msg += "\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🛡 Admin System
# ==========================
ADMIN_IDS = ["123456789"]  # Replace with your Telegram ID(s)

def admin(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ You are not authorized to use admin commands.")
        return

    keyboard = [
        [InlineKeyboardButton("📰 Manage News", callback_data="admin_news")],
        [InlineKeyboardButton("🎉 Manage Events", callback_data="admin_events")],
        [InlineKeyboardButton("📝 Manage Patch Notes", callback_data="admin_patchnotes")]
    ]

    msg = "🛡 <b>Admin Panel</b>\nChoose what to manage:"
    update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# 🛡 Admin Callback Handler
# ==========================
def admin_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in ADMIN_IDS:
        query.edit_message_text("❌ You are not authorized to use admin commands.")
        return

    if query.data == "admin_news":
        query.edit_message_text("📰 Admin: Add/Edit/Delete News here.")
    elif query.data == "admin_events":
        query.edit_message_text("🎉 Admin: Add/Edit/Delete Events here.")
    elif query.data == "admin_patchnotes":
        query.edit_message_text("📝 Admin: Add/Edit/Delete Patch Notes here.")

# ==========================
# 🛡 Moderation System
# ==========================
MODERATOR_IDS = ["123456789"]  # Replace with your Telegram ID(s)

def moderation(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in MODERATOR_IDS:
        update.message.reply_text("❌ You are not authorized to use moderation commands.")
        return

    keyboard = [
        [InlineKeyboardButton("🚫 Ban Player", callback_data="mod_ban")],
        [InlineKeyboardButton("✅ Unban Player", callback_data="mod_unban")],
        [InlineKeyboardButton("💰 Reset Coins", callback_data="mod_reset_coins")],
        [InlineKeyboardButton("📦 Reset Items", callback_data="mod_reset_items")],
        [InlineKeyboardButton("👀 Monitor Activity", callback_data="mod_monitor")]
    ]

    msg = "🛡 <b>Moderation Panel</b>\nChoose an action:"
    update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# 🛡 Moderation Callback Handler
# ==========================
def moderation_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in MODERATOR_IDS:
        query.edit_message_text("❌ You are not authorized to use moderation commands.")
        return

    if query.data == "mod_ban":
        query.edit_message_text("🚫 Moderation: Ban a player (enter user ID).")
    elif query.data == "mod_unban":
        query.edit_message_text("✅ Moderation: Unban a player (enter user ID).")
    elif query.data == "mod_reset_coins":
        query.edit_message_text("💰 Moderation: Reset coins for a player.")
    elif query.data == "mod_reset_items":
        query.edit_message_text("📦 Moderation: Reset items for a player.")
    elif query.data == "mod_monitor":
        query.edit_message_text("👀 Moderation: Monitor player activity logs.")

# ==========================
# 📢 Report System
# ==========================
def report(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    if not context.args:
        update.message.reply_text("📢 Usage: /report <your message>")
        return

    report_text = " ".join(context.args)

    # Save report to user data
    if "reports" not in users[user_id]:
        users[user_id]["reports"] = []
    users[user_id]["reports"].append({
        "date": datetime.date.today().isoformat(),
        "text": report_text
    })
    save_users(users)

    # Notify user
    update.message.reply_text("✅ Your report has been submitted. Thank you!")

    # Notify admins/mods
    for admin_id in MODERATOR_IDS:
        context.bot.send_message(
            chat_id=admin_id,
            text=f"📢 <b>New Report</b>\n👤 User: {update.effective_user.first_name}\n🗓 Date: {datetime.date.today().isoformat()}\n\n{report_text}",
            parse_mode="HTML"
        )

# ==========================
# ⭐ Feedback System
# ==========================
def feedback(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    if not context.args:
        update.message.reply_text("⭐ Usage: /feedback <your rating 1-5> <your message>")
        return

    try:
        rating = int(context.args[0])
        if rating < 1 or rating > 5:
            update.message.reply_text("⚠️ Rating must be between 1 and 5.")
            return
    except ValueError:
        update.message.reply_text("⚠️ First argument must be a number (1-5).")
        return

    feedback_text = " ".join(context.args[1:]) if len(context.args) > 1 else "No message"

    # Save feedback to user data
    if "feedback" not in users[user_id]:
        users[user_id]["feedback"] = []
    users[user_id]["feedback"].append({
        "date": datetime.date.today().isoformat(),
        "rating": rating,
        "text": feedback_text
    })
    save_users(users)

    # Notify user
    update.message.reply_text("✅ Thank you for your feedback!")

    # Notify admins/mods
    for admin_id in MODERATOR_IDS:
        context.bot.send_message(
            chat_id=admin_id,
            text=f"⭐ <b>New Feedback</b>\n👤 User: {update.effective_user.first_name}\n🗓 Date: {datetime.date.today().isoformat()}\nRating: {rating}/5\n\n{feedback_text}",
            parse_mode="HTML"
        )

# ==========================
# 💖 Donate System
# ==========================
def donate(update: Update, context: CallbackContext):
    msg = """
💖 <b>Support the Bot</b>

This RPG bot is built with passion and love for the community.
If you'd like to support development, you can donate and unlock perks!

💎 <b>Donation Perks</b>
- 🎁 Special supporter badge on your profile
- 💰 Monthly coin bonus
- 🎴 Exclusive gacha characters
- 🏅 Early access to new features

📌 <b>How to Donate</b>
- Contact the developer (Rimuru) directly
- Or visit: <i>support link here</i>

🙏 Thank you for keeping the adventure alive!
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🎁 Perks System
# ==========================
def perks(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example supporter perks
    perks_list = [
        "🏅 Supporter Badge on profile",
        "💰 Monthly coin bonus (1000 coins)",
        "🎴 Exclusive gacha characters",
        "⚡ Early access to new features",
        "🎉 Special event rewards"
    ]

    msg = "🎁 <b>Supporter Perks</b>\n\n"
    for p in perks_list:
        msg += f"- {p}\n"

    # Check if user is donor
    if users[user_id].get("donor", False):
        msg += "\n✅ You are an active supporter! Your perks are enabled."
    else:
        msg += "\n❌ You are not a supporter yet. Use /donate to join."

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏅 Profile Badge System
# ==========================
def profilebadge(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example badges
    badges = {
        "donor": "💖 Supporter",
        "moderator": "🛡 Moderator",
        "admin": "👑 Admin",
        "veteran": "⚔️ Veteran Player"
    }

    # Assign badge if donor
    user_badges = []
    if users[user_id].get("donor", False):
        user_badges.append(badges["donor"])
    if user_id in MODERATOR_IDS:
        user_badges.append(badges["moderator"])
    if user_id in ADMIN_IDS:
        user_badges.append(badges["admin"])
    if users[user_id].get("quests_done", 0) >= 100:
        user_badges.append(badges["veteran"])

    if not user_badges:
        msg = "🏅 <b>Profile Badges</b>\n❌ You have no badges yet."
    else:
        msg = "🏅 <b>Profile Badges</b>\n" + "\n".join(user_badges)

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🎖 Titles System
# ==========================
def titles(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example unlock conditions
    unlocked_titles = []
    if users[user_id].get("quests_done", 0) >= 50:
        unlocked_titles.append("📜 Quest Master")
    if users[user_id].get("battles_won", 0) >= 100:
        unlocked_titles.append("⚔️ Arena Champion")
    if users[user_id].get("donor", False):
        unlocked_titles.append("💖 Patron of Adventure")
    if users[user_id].get("daily_streak", 0) >= 30:
        unlocked_titles.append("📅 Streak Legend")
    if users[user_id].get("achievements", []):
        unlocked_titles.append("🏅 Achievement Hunter")

    msg = "🎖 <b>Player Titles</b>\n\n"
    if unlocked_titles:
        msg += "Unlocked Titles:\n" + "\n".join(unlocked_titles)
    else:
        msg += "❌ No titles unlocked yet. Keep playing to earn more!"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📚 Collections System
# ==========================
def collections(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    chars = users[user_id].get("characters", [])
    items = users[user_id].get("items", [])

    # Group characters by rarity
    rarity_groups = {"Common": [], "Rare": [], "Epic": [], "Legendary": []}
    for c in chars:
        rarity = c.get("rarity", "Common")
        rarity_groups.setdefault(rarity, []).append(c["name"])

    msg = "📚 <b>Your Collections</b>\n\n"

    msg += "🎴 <b>Characters</b>\n"
    for rarity, names in rarity_groups.items():
        if names:
            msg += f"{rarity}: " + ", ".join(names) + "\n"
    if not chars:
        msg += "❌ No characters collected yet.\n"

    msg += "\n📦 <b>Items</b>\n"
    if items:
        msg += ", ".join([i["name"] for i in items])
    else:
        msg += "❌ No items collected yet."

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🎲 Rarity System
# ==========================
def rarity(update: Update, context: CallbackContext):
    msg = """
🎲 <b>Rarity Rates</b>

🎴 <b>Characters</b>
- Common: 60%
- Rare: 25%
- Epic: 12%
- Legendary: 3%

📦 <b>Items</b>
- Common: 70%
- Rare: 20%
- Epic: 8%
- Legendary: 2%

💡 Tip:
Higher rarity = stronger stats + unique abilities.
Keep summoning to complete your collections!
    """
    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 🏹 Factions System
# ==========================
def factions(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example factions
    factions_list = [
        {"name":"⚔️ Knights of Valor","lore":"Brave warriors sworn to protect the realm.","bonus":"+10% defense when grouped"},
        {"name":"🔥 Dragon Clan","lore":"Masters of fire and dragon taming.","bonus":"+15% attack with dragon allies"},
        {"name":"🌙 Shadow Guild","lore":"Silent assassins moving under the moonlight.","bonus":"+20% critical hit chance at night"},
        {"name":"🌿 Nature Spirits","lore":"Protectors of forests and wildlife.","bonus":"+10% healing from nature spells"}
    ]

    msg = "🏹 <b>Factions</b>\n\n"
    for f in factions_list:
        msg += f"{f['name']}\n📖 {f['lore']}\n✨ Bonus: {f['bonus']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📖 Lore System
# ==========================
def lore(update: Update, context: CallbackContext):
    # Example lore entries
    lore_entries = [
        {"title":"🌍 Origins of the Realm","story":"Long ago, the world was forged by four elemental gods—Fire, Water, Earth, and Air. Their balance created life, but their rivalry birthed chaos."},
        {"title":"⚔️ The Great War","story":"Centuries ago, factions clashed in a war that shattered kingdoms. Heroes rose, legends were born, and scars remain across the land."},
        {"title":"🐉 Myth of Dragons","story":"Dragons are said to be descendants of the Fire God. Their scales hold immense power, and only the bravest can tame them."},
        {"title":"🌙 Shadow Guild","story":"A secretive order that thrives in darkness. They weave myths into fear, and their assassins are whispered about in every tavern."}
    ]

    msg = "📖 <b>World Lore</b>\n\n"
    for l in lore_entries:
        msg += f"{l['title']}\n{l['story']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📖 Story System
# ==========================
def story(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example story episode
    msg = """
📖 <b>Episode I: The Awakening</b>

You wake up in a ruined temple. The air is thick with dust, and faint light shines through broken pillars. 
A mysterious voice whispers: "Hero... your journey begins now."

What will you do?
    """

    keyboard = [
        [InlineKeyboardButton("⚔️ Explore the temple", callback_data="story_explore")],
        [InlineKeyboardButton("🌿 Step outside", callback_data="story_outside")],
        [InlineKeyboardButton("🛡 Stay and meditate", callback_data="story_meditate")]
    ]

    update.message.reply_text(msg.strip(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# 📖 Story Callback Handler
# ==========================
def story_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data

    if choice == "story_explore":
        query.edit_message_text("⚔️ You explore deeper into the temple and discover ancient runes glowing faintly...")
    elif choice == "story_outside":
        query.edit_message_text("🌿 You step outside into the forest. The sound of birds fills the air, but danger lurks nearby...")
    elif choice == "story_meditate":
        query.edit_message_text("🛡 You meditate, and visions of past heroes flow into your mind, granting wisdom...")

# ==========================
# 📚 Chapter System
# ==========================
def chapter(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Default chapter state
    if "chapter" not in users[user_id]:
        users[user_id]["chapter"] = 1
        save_users(users)

    current_chapter = users[user_id]["chapter"]

    # Example chapters
    chapters = {
        1: "📖 <b>Chapter I: The Awakening</b>\nYou awaken in a ruined temple...",
        2: "📖 <b>Chapter II: The Forest Path</b>\nYou step into the forest, danger lurks...",
        3: "📖 <b>Chapter III: The Dragon's Roar</b>\nA mighty dragon blocks your path..."
    }

    msg = chapters.get(current_chapter, "📖 No more chapters available yet.")
    keyboard = [
        [InlineKeyboardButton("➡️ Next Chapter", callback_data="chapter_next")],
        [InlineKeyboardButton("🔄 Restart Story", callback_data="chapter_restart")]
    ]

    update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# 📚 Chapter Callback Handler
# ==========================
def chapter_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    users = load_users()

    if "chapter" not in users[user_id]:
        users[user_id]["chapter"] = 1

    if query.data == "chapter_next":
        users[user_id]["chapter"] += 1
        query.edit_message_text(f"➡️ Progressed to Chapter {users[user_id]['chapter']}")
    elif query.data == "chapter_restart":
        users[user_id]["chapter"] = 1
        query.edit_message_text("🔄 Story restarted at Chapter I")

    save_users(users)

# ==========================
# 📓 Journal System
# ==========================
def journal(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()

    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return

    # Example journal entries
    journal_entries = users[user_id].get("journal", [])

    msg = "📓 <b>Your Adventure Journal</b>\n\n"
    if journal_entries:
        for entry in journal_entries[-5:]:  # Show last 5 entries
            msg += f"🗓 {entry['date']} — {entry['event']}\n"
    else:
        msg += "❌ No journal entries yet. Start your journey with /story or /chapter!"

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 📓 Add Journal Entry Helper
# ==========================
def add_journal_entry(user_id, event):
    users = load_users()
    if "journal" not in users[user_id]:
        users[user_id]["journal"] = []
    users[user_id]["journal"].append({
        "date": datetime.date.today().isoformat(),
        "event": event
    })
    save_users(users)

# ==========================
# 📚 Codex System
# ==========================
def codex(update: Update, context: CallbackContext):
    # Example codex entries
    codex_entries = [
        {"term":"⚔️ Knights of Valor","desc":"Brave warriors sworn to protect the realm. Known for their honor and defense."},
        {"term":"🔥 Dragon Clan","desc":"Masters of fire and dragon taming. Fierce in battle, feared across kingdoms."},
        {"term":"🌙 Shadow Guild","desc":"Silent assassins moving under the moonlight. Specialists in stealth and critical strikes."},
        {"term":"🌍 Elemental Gods","desc":"Four primordial beings—Fire, Water, Earth, Air—whose balance created life and chaos."},
        {"term":"🎴 Gacha","desc":"Summoning system where characters/items are obtained based on rarity rates."},
        {"term":"📦 Legendary Items","desc":"Artifacts of immense power, often tied to myths and quests."}
    ]

    msg = "📚 <b>Codex</b>\n\n"
    for e in codex_entries:
        msg += f"{e['term']}\n{e['desc']}\n\n"

    update.message.reply_text(msg.strip(), parse_mode="HTML")


# ==========================
# 📚 Library System
# ==========================
def library(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return
    
    msg = "📚 <b>Library Archive</b>\n\n"
    
    # Lore
    lore_entries = users[user_id].get("lore_unlocked", [])
    if lore_entries:
        msg += "📖 <b>Lore</b>\n" + "\n".join([f"- {l}" for l in lore_entries]) + "\n\n"
    else:
        msg += "📖 Lore: ❌ None unlocked yet.\n\n"
    
    # Story Chapters
    chapter_progress = users[user_id].get("chapter", 1)
    msg += f"📓 <b>Story Progress</b>\nCurrent Chapter: {chapter_progress}\n\n"
    
    # Journal
    journal_entries = users[user_id].get("journal", [])
    if journal_entries:
        msg += "🗒 <b>Journal Entries</b>\n"
        for entry in journal_entries[-3:]:
            msg += f"- {entry['date']}: {entry['event']}\n"
        msg += "\n"
    else:
        msg += "🗒 Journal: ❌ Empty\n\n"
    
    # Codex
    codex_entries = users[user_id].get("codex_unlocked", [])
    if codex_entries:
        msg += "📚 <b>Codex</b>\n" + "\n".join([f"- {c}" for c in codex_entries]) + "\n\n"
    else:
        msg += "📚 Codex: ❌ None unlocked yet.\n\n"
    
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏛 Museum System
# ==========================
def museum(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return
    
    # Example museum entries
    museum_entries = users[user_id].get("museum", [
        {"name":"⚔️ Sword of Eternity","desc":"A blade said to cut through time itself.","rarity":"Legendary"},
        {"name":"🐉 Dragon Scale","desc":"A relic from the ancient Dragon Clan.","rarity":"Epic"},
        {"name":"🌍 Crystal of Elements","desc":"Contains fragments of the four elemental gods.","rarity":"Legendary"},
        {"name":"📜 Scroll of Shadows","desc":"Forbidden knowledge from the Shadow Guild.","rarity":"Rare"}
    ])
    
    msg = "🏛 <b>Museum Showcase</b>\n\n"
    for entry in museum_entries:
        msg += f"{entry['name']} ({entry['rarity']})\n{entry['desc']}\n\n"
    
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🖼 Gallery System
# ==========================
def gallery(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    users = load_users()
    
    if user_id not in users:
        update.message.reply_text("❌ Please use /start first.")
        return
    
    chars = users[user_id].get("characters", [])
    items = users[user_id].get("items", [])
    
    msg = "🖼 <b>Your Gallery</b>\n\n"
    
    # Characters showcase
    if chars:
        msg += "🎴 <b>Characters</b>\n"
        for c in chars[:10]:  # Show first 10 for preview
            emoji = "⭐" if c.get("rarity") == "Legendary" else "✨" if c.get("rarity") == "Epic" else "🔹"
            msg += f"{emoji} {c['name']} ({c.get('rarity','Common')})\n"
        msg += "\n"
    else:
        msg += "🎴 Characters: ❌ None collected yet.\n\n"
    
    # Items showcase
    if items:
        msg += "📦 <b>Items</b>\n"
        for i in items[:10]:
            emoji = "💎" if i.get("rarity") == "Legendary" else "🔮" if i.get("rarity") == "Epic" else "🔹"
            msg += f"{emoji} {i['name']} ({i.get('rarity','Common')})\n"
    else:
        msg += "📦 Items: ❌ None collected yet."
    
    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🏆 Hall of Fame System
# ==========================
def halloffame(update: Update, context: CallbackContext):
    users = load_users()

    # Example leaderboard logic
    top_players = sorted(users.items(), key=lambda x: x[1].get("achievements_count", 0), reverse=True)[:5]

    msg = "🏆 <b>Hall of Fame</b>\n\n"
    rank = 1
    for uid, data in top_players:
        name = data.get("name", f"Player {uid}")
        achievements = data.get("achievements_count", 0)
        rare_items = len([i for i in data.get("items", []) if i.get("rarity") == "Legendary"])
        msg += f"{rank}. 👤 {name}\n   🏅 Achievements: {achievements}\n   💎 Legendary Items: {rare_items}\n\n"
        rank += 1

    if not top_players:
        msg += "❌ No players in Hall of Fame yet."

    update.message.reply_text(msg.strip(), parse_mode="HTML")
# ==========================
# 📊 Ranking System
# ==========================
def ranking(update: Update, context: CallbackContext):
    users = load_users()
    args = context.args

    # Default category
    category = args[0].lower() if args else "coins"

    # Supported categories
    categories = {
        "coins": "💰 Coins",
        "quests": "📜 Quests Completed",
        "battles": "⚔️ Battles Won",
        "achievements": "🏅 Achievements"
    }

    if category not in categories:
        update.message.reply_text("❌ Invalid category. Use /ranking [coins|quests|battles|achievements]")
        return

    # Sort leaderboard
    top_players = sorted(
        users.items(),
        key=lambda x: x[1].get(category, 0),
        reverse=True
    )[:5]

    msg = f"📊 <b>Ranking — {categories[category]}</b>\n\n"
    rank = 1
    for uid, data in top_players:
        name = data.get("name", f"Player {uid}")
        score = data.get(category, 0)
        msg += f"{rank}. 👤 {name} — {score}\n"
        rank += 1

    if not top_players:
        msg += "❌ No players ranked yet."

    update.message.reply_text(msg.strip(), parse_mode="HTML")

# ==========================
# 🗂 Central Menu System
# ==========================
def menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
         InlineKeyboardButton("🏅 Progression", callback_data="menu_progression")],
        [InlineKeyboardButton("📚 Lore & Story", callback_data="menu_lore"),
         InlineKeyboardButton("🎴 Collections", callback_data="menu_collections")],
        [InlineKeyboardButton("🏆 Rankings", callback_data="menu_rankings"),
         InlineKeyboardButton("🏛 Museum & Gallery", callback_data="menu_gallery")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")]
    ]

    msg = "🗂 <b>Main Menu</b>\n\nChoose a category to explore:"
    update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
### 5. **Reusable UI Components**
- Create helper functions for menus:
  ```python
  def main_menu():
      return InlineKeyboardMarkup([
          [InlineKeyboardButton("⚔️ Battle", callback_data="menu_battle"),
           InlineKeyboardButton("📜 Quest", callback_data="menu_quest")],
          [InlineKeyboardButton("🛒 Shop", callback_data="menu_shop"),
           InlineKeyboardButton("🎰 Gacha", callback_data="menu_gacha")],
          [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"),
           InlineKeyboardButton("📊 Stats", callback_data="menu_stats")]
      ])
# ==========================
# 🗂 Menu Callback Handler
# ==========================
def menu_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = query.data

    if choice == "menu_profile":
        query.edit_message_text("👤 Profile Commands:\n/start, /profile, /profilebadge, /titles")
    elif choice == "menu_progression":
        query.edit_message_text("🏅 Progression Commands:\n/quests, /battles, /achievements, /journal")
    elif choice == "menu_lore":
        query.edit_message_text("📚 Lore & Story Commands:\n/lore, /story, /chapter, /codex, /library")
    elif choice == "menu_collections":
        query.edit_message_text("🎴 Collection Commands:\n/collections, /rarity, /factions")
    elif choice == "menu_rankings":
        query.edit_message_text("🏆 Ranking Commands:\n/halloffame, /ranking, /leaderboard")
    elif choice == "menu_gallery":
        query.edit_message_text("🏛 Showcase Commands:\n/museum, /gallery")
    elif choice == "menu_settings":
        query.edit_message_text("⚙️ Settings Commands:\n/feedback, /donate, /perks")

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
    dp.add_handler(CommandHandler("inventory", inventory))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("guildwars", guildwars))
    dp.add_handler(CallbackQueryHandler(guildwars_buttons, pattern="^gw_"))
    dp.add_handler(CommandHandler("smash", smash))
    dp.add_handler(CommandHandler("marry", marry))
    dp.add_handler(CommandHandler("propose", propose))
    dp.add_handler(CallbackQueryHandler(fun_buttons, pattern="^(smash|marry|propose)_"))
    dp.add_handler(CommandHandler("missions", missions))
    dp.add_handler(CallbackQueryHandler(missions_buttons, pattern="^mission_"))
    dp.add_handler(CommandHandler("upgrade", upgrade))
    dp.add_handler(CallbackQueryHandler(upgrade_buttons, pattern="^upgrade_"))
    dp.add_handler(CommandHandler("mainmenu", mainmenu))
    dp.add_handler(CallbackQueryHandler(mainmenu_buttons, pattern="^menu_"))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(CallbackQueryHandler(settings_buttons, pattern="^set_"))
    dp.add_handler(CommandHandler("about", about))
    dp.add_handler(CommandHandler("credits", credits))
    dp.add_handler(CommandHandler("news", news))
    dp.add_handler(CommandHandler("events", events))
    dp.add_handler(CommandHandler("patchnotes", patchnotes))
    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CallbackQueryHandler(admin_buttons, pattern="^admin_"))
    dp.add_handler(CommandHandler("moderation", moderation))
    dp.add_handler(CallbackQueryHandler(moderation_buttons, pattern="^mod_"))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("feedback", feedback))
    dp.add_handler(CommandHandler("donate", donate))
    dp.add_handler(CommandHandler("perks", perks))
    dp.add_handler(CommandHandler("profilebadge", profilebadge))
    dp.add_handler(CommandHandler("titles", titles))
    dp.add_handler(CommandHandler("rarity", rarity))
    dp.add_handler(CommandHandler("factions", factions))
    dp.add_handler(CallbackQueryHandler(story_buttons, pattern="^story_"))
    dp.add_handler(CommandHandler("chapter", chapter))
    dp.add_handler(CallbackQueryHandler(chapter_buttons, pattern="^chapter_"))
    dp.add_handler(CommandHandler("journal", journal))
    dp.add_handler(CommandHandler("codex", codex))
    dp.add_handler(CommandHandler("library", library))
    dp.add_handler(CommandHandler("halloffame", halloffame))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CallbackQueryHandler(menu_buttons, pattern="^menu_"))

    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


