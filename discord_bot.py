import discord
from dotenv import load_dotenv
import os

from deck import Deck

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
BOT_CHANNEL = os.getenv('DISCORD_BOT_CHANNEL')


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        for self.guild in client.guilds:
            if self.guild.name == GUILD:
                break

        for self.bot_channel in self.guild.text_channels:
            if self.bot_channel.name == BOT_CHANNEL:
                break

        print("Ready")
        await self.bot_channel.send("Hello :)")

    async def on_disconnect(self):
        await self.bot_channel.send("-_- zzz")

    async def on_message(self, message):
        try:
            if message.author == client.user:
                return

            if "deck" in message.content.lower() and ("valid" in message.content.lower() or "check" in message.content.lower()):
                if not message.attachments:
                    await message.channel.send("Looks like you forgot to attach a deck. No worries, just ask me again. :)")
                else:
                    deck_string = await message.attachments[0].read()
                    deck_string = deck_string.decode()
                    deck = Deck(deck_string)
                    deck_validity_message = deck.get_deck_validity_message()
                    await message.channel.send(deck_validity_message)

            if "thank" in message.content.lower() and "friend" in message.content.lower():
                await message.channel.send(":)")

        except Exception as e:
            await message.channel.send("Uh oh, looks like there was an oopsie doopsie in your codey wodey :|")
            print(e)

intents=discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)
