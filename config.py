import os
from dotenv import load_dotenv
import discord

# Load environment variables from .env file
load_dotenv()

Bot_Token = os.getenv("BOT_TOKEN")
Driver_Path = os.getenv("DRIVER_PATH")
Server_Link = os.getenv("SERVER_LINK")
Application_ID = os.getenv("APPLICATION_ID")
FFMPEG_Path = os.getenv("FFMPEG_PATH")
DropBox_Access_Token = os.getenv("DROPBOX_ACCESS_TOKEN")

intents = discord.Intents.all()