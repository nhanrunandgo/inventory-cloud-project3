from woocommerce import API
import urllib3
import json
import os
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

wcapi = API(
    url=os.getenv("WP_WEBSITE_URL"),  # Consider using domain name
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    wp_api=True,
    version="wc/v3",
    timeout=30,
    verify_ssl=False
)

def woocommerce_handler(category, data):
    response = wcapi.put(category, data).json()
    return response
    
    