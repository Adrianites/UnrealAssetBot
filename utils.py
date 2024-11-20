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
import time
import subprocess

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
    options = Options()
    options.headless = True
    service = ChromeService(executable_path=Driver_Path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.fab.com')

    try:
        # Wait for the main page to load and find the link with the specified class
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'fabkit-Blades-title')))
        blade_link_elements = driver.find_elements(By.CSS_SELECTOR, 'a.fabkit-Blades-title.fabkit-Blades--interactive')
        
        blade_link = None
        for element in blade_link_elements:
            if "Limited-Time Free" in element.text:
                blade_link = element.get_attribute('href')
                break
        
        if not blade_link:
            raise Exception("Could not find the Limited-Time Free link.")
        
        print(f"Found free assets link: {blade_link}")

        # Ensure the URL is correctly formatted
        if not blade_link.startswith("http"):
            blade_link = f"https://www.fab.com{blade_link}"

        # Navigate to the blade link
        driver.get(blade_link)

        # Check for human verification page
        if "cf_challenge_container" in driver.page_source:
            print("Human verification page detected. Attempting to solve.")
            try:
                # Add a longer delay to ensure the page has fully loaded
                time.sleep(10)
                
                # Wait for the challenge form to be present
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'challenge-form')))
                
                # Loop to wait for the span element to appear
                span_element = None
                for _ in range(20):  # Try for up to 20 seconds
                    try:
                        span_element = driver.execute_script('''
                            let shadowRoot1 = document.querySelector("label.cb-lb");
                            if (!shadowRoot1) {
                                console.log("shadowRoot1 not found");
                                return null;
                            }
                            console.log("shadowRoot1 found");
                            shadowRoot1 = shadowRoot1.shadowRoot;
                            if (!shadowRoot1) {
                                console.log("shadowRoot1.shadowRoot not found");
                                return null;
                            }
                            console.log("shadowRoot1.shadowRoot found");
                            let shadowRoot2 = shadowRoot1.querySelector("#shadow-root");
                            if (!shadowRoot2) {
                                console.log("shadowRoot2 not found");
                                return null;
                            }
                            console.log("shadowRoot2 found");
                            shadowRoot2 = shadowRoot2.shadowRoot;
                            if (!shadowRoot2) {
                                console.log("shadowRoot2.shadowRoot not found");
                                return null;
                            }
                            console.log("shadowRoot2.shadowRoot found");
                            let shadowRoot3 = shadowRoot2.querySelector("#document");
                            if (!shadowRoot3) {
                                console.log("shadowRoot3 not found");
                                return null;
                            }
                            console.log("shadowRoot3 found");
                            shadowRoot3 = shadowRoot3.shadowRoot;
                            if (!shadowRoot3) {
                                console.log("shadowRoot3.shadowRoot not found");
                                return null;
                            }
                            console.log("shadowRoot3.shadowRoot found");
                            let shadowRoot4 = shadowRoot3.querySelector("#shadow-root");
                            if (!shadowRoot4) {
                                console.log("shadowRoot4 not found");
                                return null;
                            }
                            console.log("shadowRoot4 found");
                            shadowRoot4 = shadowRoot4.shadowRoot;
                            if (!shadowRoot4) {
                                console.log("shadowRoot4.shadowRoot not found");
                                return null;
                            }
                            console.log("shadowRoot4.shadowRoot found");
                            return shadowRoot4.querySelector("span.cb-i");
                        ''')
                        if span_element:
                            break
                    except Exception as e:
                        print(f"Error accessing shadow DOM: {e}")
                    time.sleep(1)
                
                if span_element:
                    checkbox = driver.execute_script('''
                        let shadowRoot1 = document.querySelector("label.cb-lb").shadowRoot;
                        let shadowRoot2 = shadowRoot1.querySelector("#shadow-root").shadowRoot;
                        let shadowRoot3 = shadowRoot2.querySelector("#document").shadowRoot;
                        let shadowRoot4 = shadowRoot3.querySelector("#shadow-root").shadowRoot;
                        return shadowRoot4.querySelector("input[type='checkbox']");
                    ''')
                    if checkbox:
                        driver.execute_script("arguments[0].click();", checkbox)
                        print("Checked the verification checkbox.")
                    else:
                        raise Exception("Checkbox not found in shadow DOM.")
                else:
                    raise Exception("Span element not found in shadow DOM.")
                
                # Wait for the verification to complete
                time.sleep(10)
                
                # Wait for the assets page to load
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'fabkit-ResultGrid-root')))
            except Exception as e:
                print(f"Error solving human verification: {e}")
                driver.quit()
                return []

        # Wait for the assets page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'fabkit-ResultGrid-root')))
    except Exception as e:
        print(f"Error navigating to assets page: {e}")
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