
import discord
from discord.ext import commands
import os
import json
import re
from datetime import datetime

# =========================================================
# OVDJE LIJEPIS SVOJE ID-eve
# =========================================================
SOURCE_CHANNEL_ID = 1487121538451771512
LOG_CHANNEL_ID = 1487121637454381243
PING_ROLE_ID = 1476259451353694313

# Fajl gdje se cuva zadnji ID
COUNTER_FILE = "/data/counter.json"

# =========================================================
# DISCORD INTENTS
# =========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================================================
# POMOCNE FUNKCIJE
# =========================================================
def ensure_counter_file():
    folder = os.path.dirname(COUNTER_FILE)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_id": 0}, f)

def get_next_id():
    ensure_counter_file()

    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["last_id"] += 1
    new_id = data["last_id"]

    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

    return new_id

def parse_message(content: str):
    """
    Prima poruke kao:
    luk 5
    luk x5
    luk x 5
    limun 2
    """
    content = content.strip().lower()

    match = re.match(r"^([^\d]+?)\s*(?:x\s*)?(\d+)$", content, re.IGNORECASE)
    if not match:
        return None, None

    vrsta = match.group(1).strip()
    komada = int(match.group(2))
    return vrsta, komada

def get_image_attachment(message: discord.Message):
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            return attachment

        filename = attachment.filename.lower()
        if filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            return attachment

    return None

# =========================================================
# EVENTI
# =========================================================
@bot.event
async def on_ready():
    print(f"Bot je online kao {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != SOURCE_CHANNEL_ID:
        return

    image_attachment = get_image_attachment(message)
    if not image_attachment:
        return

    vrsta, komada = parse_message(message.content)
    if not vrsta or not komada:
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        print("LOG_CHANNEL_ID nije dobar.")
        return

    sadnja_id = get_next_id()
    user_mention = message.author.mention
    role_mention = f"<@&{PING_ROLE_ID}>"
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    embed = discord.Embed(
        title="🌱 Sadnja zabilježena!",
        description=f"{user_mention} je posadio/la.",
        color=discord.Color.green()
    )

    embed.add_field(name="🌿 Vrsta", value=vrsta.title(), inline=True)
    embed.add_field(name="🔢 Komada", value=str(komada), inline=True)
    embed.add_field(name="🆔 ID", value=f"#{sadnja_id}", inline=True)
    embed.add_field(name="🕒 Vrijeme", value=now_str, inline=False)
    embed.add_field(name="👤 Osoba", value=user_mention, inline=False)

    embed.set_image(url=image_attachment.url)
    embed.set_footer(text="Automatska evidencija sadnje")

    await log_channel.send(
        content=f"{role_mention} {user_mention}",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(users=True, roles=True)
    )

    try:
        await message.add_reaction("✅")
    except Exception as e:
        print("Ne mogu dodati reakciju:", e)

    await bot.process_commands(message)

# =========================================================
# POKRETANJE
# =============================================
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
