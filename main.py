import requests
from bs4 import BeautifulSoup
import smtplib
import time
import random
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os  # <--- NEW: You must add this library!

# --- CONFIGURATION SECTION ---
# --- CONFIGURATION SECTION ---
PRODUCT_URL = "https://www.amazon.in/dp/B01CCGW4OE"
TARGET_PRICE = 500.0

# SECURE: We are telling Python "Go look for these secrets in the system settings"
# We are NOT writing the password here anymore.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# Headers to make the bot look like a Human Browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

def get_product_price():
    """Scrapes the product price handling multiple potential HTML structures."""
    print(f"[{datetime.datetime.now()}] Checking price...")
    
    try:
        # 1. Random delay to avoid bot detection
        time.sleep(random.uniform(2, 5))
        
        # 2. Fetch the page
        page = requests.get(PRODUCT_URL, headers=HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")

        # 3. List of possible CSS selectors for Amazon Price
        selectors = [
            {"class_": "a-price-whole"},                     # Standard India
            {"id": "corePriceDisplay_desktop_feature_div"},   # Desktop
            {"class_": "a-offscreen"},                        # Hidden price
            {"id": "priceblock_ourprice"},                   # Old style
            {"id": "priceblock_dealprice"}                   # Deal style
        ]

        # 4. Try to find the price using each selector
        for selector in selectors:
            price_tag = soup.find(name="span", **selector)
            if price_tag:
                raw_price = price_tag.get_text().strip()
                # Clean the text: Remove '₹', ',', and empty spaces
                clean_price = raw_price.replace("₹", "").replace(",", "").replace("$", "")
                
                # Extract the first valid number (handle "400.00" or "400")
                try:
                    final_price = float(clean_price.split("\n")[0])
                    print(f" -> Found Price: ₹{final_price}")
                    return final_price
                except ValueError:
                    continue # If text isn't a number, try next selector

        # 5. Debugging: If no price found, save HTML to check for Captcha
        print(" -> Error: Price not found. Saving debug HTML...")
        with open("debug_error.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        return None

    except Exception as e:
        print(f" -> Critical Error: {e}")
        return None

def send_email_alert(price):
    """Sends an email notification using SMTP (UTF-8 safe)."""
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "🚨 Price Drop Alert!"  # The emoji will work now!

    body = f"The price has dropped to ₹{price}!\n\nBuy it here: {PRODUCT_URL}"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            # We send the 'msg' object instead of a simple string
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(" -> Email Alert Sent Successfully!")
    except Exception as e:
        print(f" -> Failed to send email: {e}")

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    print("--- Amazon Price Tracker Started ---")
    print(f"Tracking URL: {PRODUCT_URL}")
    print(f"Target Price: ₹{TARGET_PRICE}")
    
    # Run once immediately
    current_price = get_product_price()
    
    if current_price:
        if current_price <= TARGET_PRICE:
            print(" -> Price is LOW! Sending alert...")
            send_email_alert(current_price)
        else:
            print(f" -> Price is still high (₹{current_price}). No email sent.")
    else:
        print(" -> Failed to retrieve price.")
