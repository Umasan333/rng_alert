import os
import discord
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")

# 監視したいチャンネルIDを入れる
WATCH_CHANNEL_IDS = {1485655601328554126}

# RenderのURLに書き換える
ALARM_URL = "https://rng-alert.onrender.com"

# Render側のAPI_KEYと同じ値にする
API_KEY = "3fa8f64f6b82a6772549c4bba19a4ee1"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id not in WATCH_CHANNEL_IDS:
        return

    if message.mention_everyone:
        print("@everyone detected")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ALARM_URL,
                    headers={"X-API-Key": API_KEY},
                ) as resp:
                    print(resp.status, await resp.text())
        except Exception as e:
            print("send error:", e)

if not TOKEN:
    print("DISCORD_TOKEN が設定されていません")
else:
    client.run(TOKEN)