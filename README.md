# Unreal Assets Bot

# THIS DISCORD BOT HAS BEEN ARCHIVED AND NOT WORKING EVER SINCE EPIC GAMES CHANGED THEIR STORE TO FAB

---

 This is a discord bot that was created to track the "Free for the Month" assets on the Epic Marketplace.

For this bot you will need a chromedriver for it to access the website.

---

# Here is a detailed way to get all of the things you will need.

## Step 1: Determine Your Chrome Version

   1. Open Google Chrome.
      
   2. Click on the three vertical dots in the upper-right corner of the browser window.
      
   3. Navigate to Help > About Google Chrome.
      
   4. A new tab will open, displaying the version number of Chrome you're using (e.g., 91.0.4472.101). Note this version number down.
   
   
## Step 2: Download ChromeDriver
   
   1. Visit the ChromeDriver download page. [ChromeDriver Download Page](https://developer.chrome.com/docs/chromedriver/downloads)
      
   2. On this page, you’ll see a list of ChromeDriver versions. Select the version that corresponds to your Chrome version.
      
   3. Click on the correct version link. This will take you to a new page with download options for different operating systems.
      
   4. Download the appropriate file for your operating system (e.g., chromedriver_win32.zip for Windows, chromedriver_mac64.zip for Mac, etc.).
      
   5. Extract the downloaded file to a location on your computer and remember this location for later.
   
   
## Step 3: Set Up ChromeDriver Path
   
   1. Once you’ve extracted the file, you’ll have an executable file named chromedriver.
      
   2. Note the full path to this file. For example, if you extracted it to `C:\Users\Joe\Documents\`, the full path would be `C:\Users\Joe\Documents\chromedriver.exe`.
   
   
## Step 4: Update Your Bot Code
   
   1. Open the bot's code in your favourite editor. (e.g., Visual Studio Code)
      
   2. Locate the line in your code where the ChromeDriver path is specified:
      
       > `service = ChromeService(executable_path=r"Path/to/your/chrome/driver`
       
       > (Check the code for all the changes that need to be made; they are written down at the bottom of the code with comments)
   
   3. Replace `Path/to/your/chrome/driver` with the full path to the chromedriver executable.


---

## Sidenote
   
   Whenever you update Google Chrome, make sure to update ChromeDriver to the corresponding version to avoid compatibility issues.
    
   __This bot is still in a work in progress build.__

---

This project is licensed under the MIT License.
