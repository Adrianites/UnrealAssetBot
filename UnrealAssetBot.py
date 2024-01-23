import discord
from discord.ext import commands
from interactions import SlashCommand, SlashContext
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')  # Removing the default help command
slash = SlashCommand(bot, sync_commands=True)  # Instantiate SlashCommand correctly

# Dictionary to store channel IDs for each server
channel_ids = {}

# Function to get Unreal Engine assets with names, images, prices, and links
def get_unreal_engine_assets():
    url = 'https://www.unrealengine.com/marketplace/en-US/assets?tag=4910'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    asset_info_elements = soup.find_all('div', class_='asset-container catalog asset-full')

    asset_info_list = []
    for element in asset_info_elements:
        asset_name = element.find('h3').text.strip()

        # Get the asset original price
        original_price_element = element.find('span', class_='asset-price asset-discount-price-wrapper')
        asset_original_price = original_price_element.text.strip() if original_price_element else 'Original price not available'

        # Get the asset discounted price
        discounted_price_element = element.find('span', class_='asset-discount-note')
        asset_discounted_price = discounted_price_element.text.strip() if discounted_price_element else None

        # Combine both prices for display
        asset_price = f'Price: {asset_original_price}'
        if asset_discounted_price:
            asset_price += f'\nDiscount: {asset_discounted_price}'

        # Get the asset image URL
        image_element = element.find('img', class_='image-box')
        asset_image_url = image_element['src'] if image_element else 'No image available'

        # Get the asset link
        asset_link_element = element.find('a', class_='asset')
        asset_link = f"https://www.unrealengine.com{asset_link_element['href']}" if asset_link_element else 'No link available'

        # Combine all of the information into one message
        embed = discord.Embed(
            title=asset_name,
            description=f'Price: {asset_price}\n[Link to Asset]({asset_link})',
            color=discord.Color.green()
        )
        embed.set_image(url=asset_image_url)
        asset_info_list.append((asset_name, asset_image_url, asset_price, asset_link, embed))

    return asset_info_list


# Function to load channel ID from file
def load_channel_id(guild_id): 
    try:
        with open('channel_ids.json', 'r') as file:
            data = json.load(file)
            return data.get(str(guild_id))
    except FileNotFoundError:
        return None

# Function to save channel ID to file
def save_channel_id(guild_id, channel_id):
    data = {}
    try:
        with open('channel_ids.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass
    
    data[str(guild_id)] = channel_id
    
    with open('channel_ids.json', 'w') as file:
        json.dump(data, file)

# Check admin permissions decorator
def is_admin():
    def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            # Send a message to the user if they don't have admin privileges
            embed = discord.Embed(
                title="Permission Denied",
                description="You do not have the required Administrator privileges to use this command.",
                color=discord.Color.red()
            )
            ctx.send(embed=embed)
            return False
    return commands.check(predicate)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Connected to the following servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

# Event: Bot joins a new server
@bot.event
async def on_guild_join(guild):
    print(f'Joined a new server: {guild.name} (ID: {guild.id})')
    await guild.owner.send(f'Thank you for adding me to your server, {guild.name}! To set up automatic updates, use the `/set_channel` command in the channel where you want the updates. If you want to remove the automatic updates then use the `/remove_channel` command in the channel. If you want to test if the automatic update is working then use the `/test_update` command. Side note: Only people with *Administrator Privileges* can use the commands.')


# Command: Test Update
@slash.slash(name='test_update', description='Trigger a test update to see the latest Unreal Engine assets.')
@is_admin()  # Use the custom decorator
async def test_update(ctx: SlashContext):
    await update_assets(ctx)

async def update_assets(ctx: commands.Context):
    print("Update Triggered!")

    asset_info_list = get_unreal_engine_assets()

    # Get the current date in the specified format
    current_date = datetime.utcnow().strftime('%B %d, %Y')

    # Check if the channel is set for the current guild
    channel_id = load_channel_id(ctx.guild.id)
    if channel_id is None:
        await ctx.send('Channel not set. Please use `/set_channel` to set the channel for automatic updates.')
        return

    channel = await bot.get_channel(channel_id)
    if channel:
        # Send a single message with the combined information
        combined_message = f'As of {current_date}, the free assets are:\n\n'
        for asset_name, asset_image_url, asset_price, asset_link, embed in asset_info_list:
            combined_message += f'{asset_name}\n{asset_price}\n[Link to Asset]({asset_link})\n\n'

        await channel.send(combined_message)
        print('Message sent successfully!')
        await ctx.send('Test update sent successfully!')
    else:
        await ctx.send('Channel not found. Please set the channel using `/set_channel` command.')

# Command: Set Channel
@bot.command(name='set_channel', help='Set the channel for automatic updates.')
@is_admin()  # Use the custom decorator
async def set_channel(ctx):
    current_channel_id = load_channel_id(ctx.guild.id)
    if current_channel_id is None:
        save_channel_id(ctx.guild.id, ctx.channel.id)
        await ctx.send(f'Channel set to #{ctx.channel.name} for automatic updates.')
    else:
        await ctx.send('Channel is already set. To change it, use `/remove_channel` first.')

# Command: Remove Channel
@bot.command(name='remove_channel', help='Remove the set channel for automatic updates.')
@is_admin()  # Use the custom decorator
async def remove_channel(ctx):
    current_channel_id = load_channel_id(ctx.guild.id)
    if current_channel_id is not None:
        save_channel_id(ctx.guild.id, None)
        await ctx.send('Channel removed. Automatic updates will not work until you set a new channel.')
    else:
        await ctx.send('Channel is not set. To set it, use `/set_channel` first.')

# Run the bot
bot.run('bot_token')
# Do not share your bot token with anyone else.
