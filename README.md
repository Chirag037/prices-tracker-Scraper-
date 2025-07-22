# prices-tracker-Scraper-
This Python-based automation tool monitors the price of any Amazon product in real-time and automatically notifies you via email when the price drops below your desired threshold. It helps users track deals effortlessly without manually checking the site. 
# 🛒 Amazon Prices Tracker Scraper

This Python-based automation tool monitors the price of any Amazon product in real-time and automatically notifies you via email when the price drops below your desired threshold. It helps users effortlessly track deals without having to manually check product pages.

---

## 🚀 Features

- ✅ Scrapes product title and current price from Amazon
- 📉 Compares current price with your target threshold
- 📧 Sends an email alert when the price drops
- 💡 Easy configuration with `config.py`
- 🧰 Clean and modular code structure

---

## 🛠️ Tech Stack

- **Python 3**
- `requests`
- `BeautifulSoup` (bs4)
- `lxml`
- `smtplib` (for sending email)

---

## 📦 Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Chirag037/prices-tracker-Scraper-.git
   cd prices-tracker-Scraper-
Install dependencies:

pip install -r requirements.txt
Configure your settings:

Open config.py and set:

PRODUCT_URL

TARGET_PRICE








🧩 Customization Ideas
🔁 Schedule it to run daily using schedule or a cron job

📊 Store prices in a CSV or database for trend analysis

📲 Add Telegram or Discord notifications

🌐 Turn it into a Flask-based web dashboard

📄 License
This project is licensed under the MIT License.

