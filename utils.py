import json
import discord
from datetime import datetime, timedelta, timezone
import calendar
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from config import Driver_Path

def is_admin(interaction: discord.Interaction):
    if interaction.guild is None:
        return False
    return interaction.user.guild_permissions.administrator

def load_channel_id(guild_id):
    try:
        with open('channel_ids.json', 'r') as file:
            data = json.load(file)
            return data.get(str(guild_id))
    except FileNotFoundError:
        return None

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

def get_next_asset_change_date():
    today = datetime.utcnow()
    next_month = today.month + 1 if today.month < 12 else 1
    year = today.year if next_month != 1 else today.year + 1

    first_tuesday = None
    for day in range(1, 8):
        if calendar.weekday(year, next_month, day) == calendar.TUESDAY:
            first_tuesday = day
            break

    next_asset_change_date = datetime(year, next_month, first_tuesday) + timedelta(days=1)
    return next_asset_change_date.strftime("%d/%m/%Y")

def get_unreal_engine_assets():
    url = 'https://www.fab.com/blade/0691ff19-b259-44e0-ad3b-093a53010f46?context=homepage'

    options = Options()
    options.headless = True
    service = ChromeService(executable_path=Driver_Path)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'fabkit-ResultGrid-root')))
    except Exception as e:
        print(f"Error waiting for page to load: {e}")
        driver.quit()
        return []

    page_source = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_source, 'html.parser')
    asset_containers = soup.find_all('div', class_='fabkit-Stack-root fabkit-scale--gapX-layout-3 fabkit-scale--gapY-layout-3 fabkit-Stack--column hTu1xoWw')
    print(f"Found {len(asset_containers)} assets on the page.")

    asset_info_list = []
    for index, element in enumerate(asset_containers):
        try:
            print(f"Processing asset {index + 1}/{len(asset_containers)}")

            asset_name_element = element.find('div', class_='fabkit-Typography-ellipsisWrapper')
            asset_name = asset_name_element.text.strip() if asset_name_element else 'No name available'
            print(f"Asset name: {asset_name}")

            star_rating_element = element.find('div', class_='fabkit-Stack-root fabkit-Stack--align_center fabkit-scale--gapX-spacing-1 fabkit-scale--gapY-spacing-1')
            star_rating = star_rating_element.text.strip() if star_rating_element else 'No rating available'
            print(f"Star rating: {star_rating}")

            subtitle_element = element.find('div', class_='yEF5rBPt')
            if subtitle_element:
                subtitle_element = subtitle_element.find_next_sibling('div')
                subtitle = subtitle_element.text.strip() if subtitle_element else 'No subtitle available'
            else:
                subtitle = 'No subtitle available'
            print(f"Subtitle: {subtitle}")

            # Extract the star rating number and subtitle separately
            if star_rating.replace('.', '', 1).isdigit():
                star_rating_value = star_rating
            else:
                star_rating_value = 'No rating available'

            price_element = element.find('div', class_='fabkit-Typography-root fabkit-typography--intent-primary fabkit-Text--lg fabkit-Text--regular')
            asset_price = price_element.text.strip() if price_element else 'Free'
            print(f"Asset price: {asset_price}")

            image_element = element.find('img')
            asset_image_url = image_element['src'] if image_element else 'No image available'
            print(f"Asset image URL: {asset_image_url}")

            asset_link_element = element.find('a', class_='fabkit-Thumbnail-overlay h2KfmOpM')
            asset_link = f"https://www.fab.com{asset_link_element['href']}" if asset_link_element else 'No link available'
            print(f"Asset link: {asset_link}")

            next_asset_change_date = get_next_asset_change_date()
            embed = discord.Embed(
                title=asset_name,
                description=f'**{subtitle}**\n\nCurrent Price:\n**{asset_price}**\n\nStar Rating:\n**{star_rating_value}**',
                color=discord.Color.green()
            )
            embed.set_image(url=asset_image_url)
            embed.add_field(name='Free until', value=f'`{next_asset_change_date}`', inline=True)
            embed.add_field(name='Open in Browser', value=f'[Link]({asset_link})', inline=True)
            embed.set_footer(text='Powered by Chadtopia')

            asset_info_list.append(embed)
        except Exception as e:
            print(f"Error processing asset element: {e}")

    if not asset_info_list:
        print("No assets were found during scraping.")
    return asset_info_list