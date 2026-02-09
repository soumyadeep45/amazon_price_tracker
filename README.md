# 🛒 Amazon Price Tracker Bot

An automated, cloud-native price monitoring tool that tracks Amazon products and sends real-time email alerts using Python and GitHub Actions.

## 🌟 Key Features
* **Automated Monitoring:** Runs on a schedule (every 6 hours) using GitHub Actions—no local computer required.
* **Security First:** Implements **GitHub Secrets** and environment variables to protect sensitive credentials (email/passwords).
* **Dynamic Scraper:** Uses `BeautifulSoup4` and custom User-Agent headers to bypass basic anti-scraping measures.
* **Privacy Focused:** Repository history has been sanitized to ensure no personal data is stored in the Git history.

## 🛠️ Tech Stack
* **Language:** Python 3.9
* **Libraries:** `BeautifulSoup4` (Scraping), `Requests` (HTTP), `LXML` (Parsing)
* **Automation:** GitHub Actions (CI/CD)
* **Protocol:** SMTP with SSL for secure email transmission

## 📂 Project Structure
```text
amazon_price_tracker/
├── .github/
│   └── workflows/
│       └── scraper.yml    # Automation & environment config
├── main.py               # Main application logic
└── requirements.txt      # List of Python dependencies
