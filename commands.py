import discord
from discord import app_commands
from utils import is_admin, get_unreal_engine_assets, load_channel_id, save_channel_id, delete_channel_id
from datetime import datetime, timedelta, timezone
from config import FFMPEG_Path, DropBox_Access_Token
import dropbox
import asyncio
import os
import re
from youtube_downloader import download_youtube_video

class FormatSelect(discord.ui.Select):
    def __init__(self, url):
        self.url = url
        options = [
            discord.SelectOption(label='MP4', description='Download as MP4', value='mp4'),
            discord.SelectOption(label='MP3', description='Download as MP3', value='mp3')
        ]
        super().__init__(placeholder='Choose the format...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        format = self.values[0]
        await interaction.response.send_message('Downloading video...', ephemeral=True)

        try:
            title = "downloaded_video"
            ext = 'mp3' if format == 'mp3' else 'mp4'
            file_path = f'downloads/{title}.{ext}'

            # Call the Rust function to download the video
            download_youtube_video(self.url, format, file_path)

            # Upload the file to Dropbox
            dbx = dropbox.Dropbox(DropBox_Access_Token)
            with open(file_path, "rb") as f:
                dbx.files_upload(f.read(), f'/{title}.{ext}', mute=True)
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(f'/{title}.{ext}')
            dropbox_link = shared_link_metadata.url.replace("?dl=0", "?dl=1")

            await interaction.followup.send(f'Video downloaded successfully: {title}.{ext}', ephemeral=True)
            await interaction.followup.send(f'Download link: {dropbox_link}', ephemeral=True)

            # Delete the file after uploading
            os.remove(file_path)

            # Wait for 10 minutes before deleting the file from Dropbox
            await asyncio.sleep(600)
            dbx.files_delete_v2(f'/{title}.{ext}')
        except Exception as e:
            await interaction.followup.send(f'Error downloading video: {e}', ephemeral=True)

class FormatSelectView(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        self.add_item(FormatSelect(url))

async def setup_commands(bot):
    @bot.tree.command(name='test_update', description='Trigger a test update to see the latest Unreal Engine assets.')
    @app_commands.check(is_admin)
    async def test_update(interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
            return

        channel_id = load_channel_id(interaction.guild.id)
        if channel_id is None:
            await interaction.response.send_message('Channel not set. Please use `/set_channel` to set the channel for automatic updates.', ephemeral=True)
            return

        await interaction.response.send_message('Fetching latest assets...', ephemeral=True)

        asset_info_list = get_unreal_engine_assets()
        if not asset_info_list:
            await interaction.followup.send('No assets found or an error occurred while fetching assets.', ephemeral=True)
            return

        guild = bot.get_guild(interaction.guild.id)
        channel = bot.get_channel(channel_id)
        if channel is None:
            await interaction.followup.send('The channel for automatic updates could not be found. Please set it again using `/set_channel`.', ephemeral=True)
            return

        for asset_info in asset_info_list:
            await channel.send(embed=asset_info)

        await interaction.followup.send('Test update completed. The latest assets have been posted in the designated channel.', ephemeral=True)

    @bot.tree.command(name='set_channel', description='Set the channel for automatic updates.')
    @app_commands.check(is_admin)
    async def set_channel(interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
            return

        save_channel_id(interaction.guild.id, interaction.channel.id)
        await interaction.response.send_message(f'Automatic updates have been set for {interaction.channel.name}.', ephemeral=True)

    @bot.tree.command(name='remove_channel', description='Remove the channel for automatic updates.')
    @app_commands.check(is_admin)
    async def remove_channel(interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
            return

        delete_channel_id(interaction.guild.id)
        await interaction.response.send_message('Automatic updates have been removed for this channel.', ephemeral=True)

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
        **/download_youtube** - Download a YouTube video.
        **/list_of_commands** - List all commands of the bot.

        Side note: Only people with `Administrator Privileges` can use the commands.
        """
        await interaction.response.send_message(help_text, ephemeral=True)

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
                        await asyncio.sleep(1)

                await interaction.followup.send(f"Deleted {deleted_count} recent messages of {user.name} from the last {time_value} {time_unit_str}.")
            except discord.NotFound:
                await interaction.followup.send("User not found. Please check the user ID and try again.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("I do not have permission to delete messages in this channel.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)

    @bot.tree.command(name='download_youtube', description='Download a YouTube video.')
    async def download_youtube(interaction: discord.Interaction, url: str):
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Commands cannot be used in DMs. Please use this command in a server.", ephemeral=True)
            return

        await interaction.response.send_message('Please select the format:', view=FormatSelectView(url), ephemeral=True)