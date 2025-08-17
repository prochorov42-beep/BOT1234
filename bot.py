import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Bot
from telegram.error import TelegramError
import threading
import time

# Telegram
TOKEN = os.environ.get("8416426315:AAHaQ6YUNK2Qhd2HL8vXUfZWANWfr3LhYEg")
CHAT_ID = os.environ.get("745466246")
bot = Bot(token=TOKEN)

# OLX URLs
ELECTRO_URL = "https://www.olx.pl/rowery/rowery-elektryczne/wroclaw/"
NORMAL_URL = "https://www.olx.pl/rowery/rowery-szosowe-i-gorskie/wroclaw/"

# Цены
ELECTRO_MIN, ELECTRO_MAX = 0, 1300
NORMAL_MIN, NORMAL_MAX = 0, 250

# Flask
app = Flask(__name__)

# Хранение уже отправленных объявлений
sent_links = set()

def fetch_olx(url, min_price, max_price):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    ads = []

    for item in soup.select("div.css-1sw7q4x"):  # OLX элемент
        try:
            title_tag = item.select_one("h6")
            link_tag = item.find("a", href=True)
            price_tag = item.select_one("p")

            if not (title_tag and link_tag and price_tag):
                continue

            title = title_tag.get_text(strip=True)
            link = link_tag['href']
            price_text = price_tag.get_text(strip=True).replace("zł", "").replace(" ", "")
            price = int(price_text) if price_text.isdigit() else 0

            if min_price <= price <= max_price and link not in sent_links:
                ads.append((title, link, price))
        except Exception:
            continue

    return ads

def check_ads():
    while True:
        for url, min_p, max_p in [
            (ELECTRO_URL, ELECTRO_MIN, ELECTRO_MAX),
            (NORMAL_URL, NORMAL_MIN, NORMAL_MAX)
        ]:
            new_ads = fetch_olx(url, min_p, max_p)
            for title, link, price in new_ads:
                try:
                    bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"{title}\nCena: {price} zł\n{link}"
                    )
                    sent_links.add(link)
                except TelegramError:
                    continue
        time.sleep(300)  # Проверка каждые 5 минут

@app.route("/")
def index():
    return "Бот работает!"

if __name__ == "__main__":
    threading.Thread(target=check_ads, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
