from config import Server_Link
from utils import delete_channel_id

def setup_events(bot):
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}')
        print('Connected to the following servers:')
        for guild in bot.guilds:
            print(f'- {guild.name} (ID: {guild.id})')
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)

    @bot.event
    async def on_guild_join(guild):
        await bot.tree.sync(guild=guild)
        print(f'Joined a new server: {guild.name} (ID: {guild.id})')
        await guild.owner.send(f'Thanks for adding me to your server, `{guild.name}`! To see all commands, use the `/list_of_commands` command. Side note: Only people with *Administrator Privileges* can use the commands.')

    @bot.event
    async def on_guild_remove(guild):
        print(f'Removed from server: {guild.name} (ID: {guild.id})')
        delete_channel_id(guild.id)
        await guild.owner.send(f'I have been removed from your server `{guild.name}`. If you have any feedback or need assistance, feel free to contact my creator in my support server, {Server_Link}.')