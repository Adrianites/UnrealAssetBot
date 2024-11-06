import asyncio
from discord.ext import commands
from config import Bot_Token, intents, Application_ID
from commands import setup_commands
from events import setup_events

bot = commands.Bot(command_prefix='/', intents=intents, application_id=Application_ID)

async def main():
    setup_events(bot)
    await setup_commands(bot)
    await bot.start(Bot_Token)

if __name__ == "__main__":
    asyncio.run(main())