import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import calendar

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store channel IDs for each server
channel_ids = {}

def get_next_asset_change_date():
    today = datetime.utcnow()
    month = today.month
    year = today.year

    # Find the first Tuesday of the current month
    first_tuesday = None
    for day in range(1, 8):
        if calendar.weekday(year, month, day) == calendar.TUESDAY:
            first_tuesday = day
            break

    if today.day > first_tuesday:
        # If today is past the first Tuesday, calculate for the next month
        month = month + 1 if month < 12 else 1
        year = year if month != 1 else year + 1

        for day in range(1, 8):
            if calendar.weekday(year, month, day) == calendar.TUESDAY:
                first_tuesday = day
                break

    next_asset_change_date = datetime(year, month, first_tuesday) + timedelta(days=1)  # Move to Wednesday so it will use the updated assets without any trouble
    return next_asset_change_date.strftime("%d/%m/%Y")

def get_unreal_engine_assets():
    url = 'https://www.unrealengine.com/marketplace/en-US/assets?tag=4910&locale=en-GB'

    options = Options()
    options.headless = True
    service = ChromeService(executable_path=r"Path/to/your/chrome/driver")

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'asset-container')))
    except Exception as e:
        print(f"Error waiting for page to load: {e}")
        driver.quit()
        return []

    page_source = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_source, 'html.parser')
    asset_containers = soup.find_all('div', class_='asset-container')
    print(f"Found {len(asset_containers)} assets on the page.")

    asset_info_list = []
    for index, element in enumerate(asset_containers):
        try:
            print(f"Processing asset {index + 1}/{len(asset_containers)}")

            asset_name_element = element.find('h3')
            asset_name = asset_name_element.text.strip() if asset_name_element else 'No name available'
            print(f"Asset name: {asset_name}")

            original_price_element = element.find('div', class_='price-container')
            asset_original_price = original_price_element.text.strip().replace('100%OFF', '').replace('Free', '').strip() if original_price_element else 'Original price not available'
            print(f"Original price: {asset_original_price}")

            discounted_price_element = element.find('span', class_='asset-price')
            asset_discounted_price = discounted_price_element.text.strip().replace('Price: ', '').replace(asset_original_price, '').replace('Free', '').strip() if discounted_price_element else 'Free'
            
            # If the asset_discounted_price is empty, it means the asset is free
            if not asset_discounted_price:
                asset_discounted_price = '**Free**'

            discount_note_element = element.find('span', class_='asset-discount-note')
            asset_discount_note = discount_note_element.text.strip().replace('100%OFF', '100% OFF') if discount_note_element else None

            # Formatting the price and discount text
            price_text = f"Original Price: **{asset_original_price}**"
            discount_text = f"Discount: **{asset_discount_note}**"

            print(f"Asset price: {price_text}")
            print(f"Asset discount: {discount_text}")

            image_element = element.find('img')
            asset_image_url = image_element['src'] if image_element else 'No image available'
            print(f"Asset image URL: {asset_image_url}")

            # Finding the asset link dynamically
            asset_link_element = element.find('a')
            asset_link = f"https://www.unrealengine.com{asset_link_element['href']}" if asset_link_element else 'No link available'
            print(f"Asset link: {asset_link}")

            next_asset_change_date = get_next_asset_change_date()
            embed = discord.Embed(
                title=asset_name,
                description=f'{price_text}\n{discount_text}',
                color=discord.Color.green()
            ) # Putting them in order inside the embedded message
            embed.set_image(url=asset_image_url)
            embed.add_field(name='Current Price', value=f'{asset_discounted_price}', inline=False)  
            embed.add_field(name='Free until', value=f'`{next_asset_change_date}`', inline=True)
            embed.add_field(name='Open in Browser', value=f'[Link]({asset_link})', inline=True)
            embed.set_footer(text='Powered by Chadtopia')

            asset_info_list.append(embed)
        except Exception as e:
            print(f"Error processing asset element: {e}")

    if not asset_info_list:
        print("No assets were found during scraping.")
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

# Function to delete channel ID from file
def delete_channel_id(guild_id):
    try:
        with open('channel_ids.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return

    if str(guild_id) in data:
        del data[str(guild_id)]

        with open('channel_ids.json', 'w') as file:
            json.dump(data, file)

# Check admin permissions decorator
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# Event: Bot is ready
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
    await guild.owner.send(f'I have been removed from your server `{guild.name}`. If you have any feedback or need assistance, feel free to contact my creator in my support server, [SERVER-NAME-HERE](<SERVER-LINK-HERE>) .')

# Command: Test Update
@bot.tree.command(name='test_update', description='Trigger a test update to see the latest Unreal Engine assets.')
@app_commands.check(is_admin)  # Use the custom decorator
async def test_update(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
        return

    # Check if the channel is set for the current guild
    channel_id = load_channel_id(interaction.guild.id)
    if channel_id is None:
        await interaction.response.send_message('Channel not set. Please use `/set_channel` to set the channel for automatic updates.', ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)  # Defer the response
    await interaction.followup.send("Update Triggered!", ephemeral=True)

    asset_info_list = get_unreal_engine_assets()
    if not asset_info_list:
        await interaction.followup.send('No assets found or an error occurred during scraping.', ephemeral=True)
        return

    channel_id = load_channel_id(interaction.guild.id)
    channel = bot.get_channel(channel_id)
    if channel is None:
        await interaction.followup.send('The channel for automatic updates could not be found. Please set it again using `/set_channel`.', ephemeral=True)
        return

    for asset_info in asset_info_list:
        await channel.send(embed=asset_info)

    await interaction.followup.send('Test update completed. The latest assets have been posted in the designated channel.', ephemeral=True)

# Command: Set Channel
@bot.tree.command(name='set_channel', description='Set the channel for automatic updates.')
@app_commands.check(is_admin)  # Check for admin decorator
async def set_channel(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
        return

    save_channel_id(interaction.guild.id, interaction.channel.id)
    await interaction.response.send_message(f'Automatic updates have been set for {interaction.channel.name}.', ephemeral=True)

# Command: Remove Channel
@bot.tree.command(name='remove_channel', description='Remove the channel for automatic updates.')
@app_commands.check(is_admin)  # Check for admin decorator
async def remove_channel(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
        return

    delete_channel_id(interaction.guild.id)
    await interaction.response.send_message('Automatic updates have been removed for this channel.', ephemeral=True)

# Command: List of Commands
@bot.tree.command(name='list_of_commands', description='List all commands of the bot.')
async def list_of_commands(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
        return

    help_text = """
    **Unreal Assets Bot Commands:**
    **/set_channel** - Set the channel for automatic updates on the latest **Free** Assets.
    **/remove_channel** - Remove the channel for automatic updates on the latest **Free** Assets.
    **/test_update** - Trigger a test update to see the latest Unreal Engine assets.
    **/delete** - Deletes recent messages of a user. - Use `M, H, or D` for Minutes, Hours, or Days (eg. *3h* for 3 hours)
    **/list_of_commands** - List all commands of the bot.

    Side note: Only people with `Administrator Privileges` can use the commands.
    """
    await interaction.response.send_message(help_text, ephemeral=True)

# Command: Delete messages
@bot.tree.command(name="delete", description="Deletes recent messages of a user")
async def delete(interaction: discord.Interaction, user_id: str, time: str):
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
        return

    if interaction.user.guild_permissions.administrator:
        try:
            user = await bot.fetch_user(user_id)
            await interaction.response.send_message(f"Deleting recent messages of {user.name}...", ephemeral=True)
            deleted_count = 0

            # Validate and parse the time string
            if not (time[-1] in ['m', 'h', 'd'] and time[:-1].isdigit()):
                await interaction.followup.send("Invalid time format. Use `m` for minutes, `h` for hours, or `d` for days.", ephemeral=True)
                return

            time_unit = time[-1]
            time_value = int(time[:-1])

            if time_value > 365:
                await interaction.followup.send("Time value cannot be greater than 365.", ephemeral=True)
                return

            if time_unit == 'm':
                time_limit = datetime.now(timezone.utc) - timedelta(minutes=time_value)
                time_unit_str = "Minute(s)"
            elif time_unit == 'h':
                time_limit = datetime.now(timezone.utc) - timedelta(hours=time_value)
                time_unit_str = "Hour(s)"
            elif time_unit == 'd':
                time_limit = datetime.now(timezone.utc) - timedelta(days=time_value)
                time_unit_str = "Day(s)"
            else:
                await interaction.followup.send("Invalid time format. Use `m` for minutes, `h` for hours, or `d` for days.", ephemeral=True)
                return

            async for message in interaction.channel.history(limit=100):
                if message.author.id == user.id and message.created_at > time_limit:
                    await message.delete()
                    deleted_count += 1
                    await asyncio.sleep(1)  # Add a 1-second delay so discord wont be upset

            await interaction.followup.send(f"Deleted {deleted_count} recent messages of {user.name} from the last {time_value} {time_unit_str}.")
        except discord.NotFound:
            await interaction.response.send_message("User not found. Please check the user ID and try again.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to delete messages in this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)


# Run the bot
bot.run("Bot_Token")
# Do not share your bot token with anyone else.


# Changes to be made
    # Line 52  - Change "Path/to/your/chrome/driver" to your own path (eg. C:\Users\Joe\Documents\Chromedriver.exe)
    # Line 194 - Change "[SERVER-NAME-HERE](<SERVER-LINK-HERE>)"" for your own Server (eg. [Joes Discord Server](<https://discord.gg/JoesServerLink>) 
    # Line 326 - Change "Bot_Token" to your own bots token (Its a long line of random characters you receive in the Discord Developer Portal) 