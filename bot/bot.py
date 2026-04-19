import discord
import aiohttp
import os

TOKEN = os.getenv("DISCORD_TOKEN")
WATCH_CHANNEL_IDS = {1485655601328554126}
ALARM_URL = "http://127.0.0.1:8000/alarm"
API_KEY = "change-me"

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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                ALARM_URL,
                headers={"X-API-Key": API_KEY},
            ) as resp:
                print(resp.status, await resp.text())

client.run(TOKEN)