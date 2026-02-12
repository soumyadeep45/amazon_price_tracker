import requests
from bs4 import BeautifulSoup
import smtplib
import os
import json
import random
import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# --- FUNCTIONS ---

def get_price(url):
    """Scrapes price with advanced headers to bypass basic bot detection."""
    
    # List of "Browser Fingerprints"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    # "Stealth" Headers - These make the bot look like a real user browsing
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "lxml")

        # DEBUG: Print the page title to see if we are blocked
        page_title = soup.title.text.strip() if soup.title else "No Title"
        # print(f"   📄 Page Title: {page_title[:30]}...") 

        if "Robot Check" in page_title or "Captcha" in page_title:
            print("   ⚠️ Amazon blocked this request (CAPTCHA Detected).")
            return None

        # METHOD 1: Standard 'a-price-whole' (Visible Price)
        price_element = soup.find("span", class_="a-price-whole")
        
        # METHOD 2: 'a-offscreen' (Hidden Price, often more reliable)
        if not price_element:
            price_element = soup.find("span", class_="a-offscreen")

        # METHOD 3: Old style IDs (Backwards compatibility)
        if not price_element:
            price_element = soup.find(id="priceblock_ourprice")
            
        if not price_element:
            price_element = soup.find(id="priceblock_dealprice")

        # PROCESS THE PRICE
        if price_element:
            price_text = price_element.get_text().strip()
            # Remove currency symbols and commas (e.g. "₹1,299.00" -> "1299.00")
            clean_price = price_text.replace("₹", "").replace(",", "").replace("€", "").replace("$", "")
            
            # Handle cases where price might handle text
            try:
                final_price = float(clean_price)
                return final_price
            except ValueError:
                # print(f"   ⚠️ Could not convert '{clean_price}' to number.")
                return None
        else:
            # print("   ⚠️ Selector failed. Page layout might be different.")
            return None
            
    except Exception as e:
        print(f"   ❌ Network/Scrape Error: {e}")
        return None

def send_email(product_name, price, url):
    """Sends a professional HTML email alert."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️ Email credentials missing. Skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"📉 Price Drop: {product_name} is ₹{price}!"

    # Professional HTML Template
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #d32f2f;">📉 Price Drop Alert!</h2>
        <p>The price for <strong>{product_name}</strong> has dropped to <strong>₹{price}</strong>.</p>
        <p>This is below your target price.</p>
        <br>
        <a href="{url}" style="background-color: #ff9900; color: black; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
          View on Amazon
        </a>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ Email Alert Sent for {product_name}!")
    except Exception as e:
        print(f"❌ Email Failed: {e}")

def save_history(name, price):
    """Saves price data to CSV."""
    filename = "price_history.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Time", "Product", "Price"])
        
        now = datetime.now()
        writer.writerow([now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), name, price])

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print("--- 🛒 Amazon Tracker Started ---")
    
    # Robust Path Finding
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'products.json')

    try:
        with open(json_path, 'r') as file:
            products = json.load(file)
            print(f"📋 Loaded {len(products)} products.")
    except FileNotFoundError:
        print("❌ Error: products.json not found! Please create it.")
        products = []

    for item in products:
        name = item['name']
        url = item['url']
        target = item['target_price']
        
        print(f"\n🔍 Checking: {name}...")
        current_price = get_price(url)
        
        if current_price:
            print(f"   💰 Current: ₹{current_price} | Target: ₹{target}")
            save_history(name, current_price)
            
            if current_price <= target:
                print("   📉 TARGET MET! Sending alert...")
                send_email(name, current_price, url)
            else:
                print("   Wait: Price is still above target.")
        else:
            print("   ⚠️ Could not retrieve price (Blocked or changed layout).")

    print("\n--- 🏁 Finished ---")