import os

# base configs
BOT_NAMES = ['детка', 'baby', 'умник', 'clever boy']
VK_GROUP_ID = os.getenv('VK_GROUP_ID')
VK_TOKEN = os.getenv('VK_TOKEN')

# weather configs
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_CITY = os.getenv('WEATHER_CITY')

if not VK_GROUP_ID or not VK_TOKEN:
    raise ImportError(
        "Couldn't get valid VK settings. Please check the environment variables"
    )
