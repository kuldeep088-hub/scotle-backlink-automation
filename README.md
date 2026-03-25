# Business Lead Generator

Scrapes business listings from **JustDial**, cleans the data, and automatically uploads it to **Google Sheets**.

---

## Project Structure

```
business_lead_generator/
├── main.py           # Entry point - run this
├── scraper.py        # JustDial scraping logic (Playwright + requests fallback)
├── sheets.py         # Google Sheets integration
├── utils.py          # Cleaning, deduplication, filtering
├── config.py         # All settings in one place
├── requirements.txt  # Python dependencies
├── credentials.json  # YOUR Google service account key (you create this)
└── output/
    ├── business_leads_backup.csv
    └── scraper.log
```

---

## Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

Then install the Chromium browser for Playwright:

```bash
playwright install chromium
```

---

## Step 2 — Setup Google Sheets API

### 2.1 Create a Google Cloud Project

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Click **"New Project"** → name it anything (e.g., `lead-generator`)
3. Click **"Create"**

### 2.2 Enable Required APIs

1. In your project, go to **APIs & Services > Library**
2. Search for **"Google Sheets API"** → Enable it
3. Search for **"Google Drive API"** → Enable it

### 2.3 Create a Service Account

1. Go to **APIs & Services > Credentials**
2. Click **"Create Credentials"** → **"Service Account"**
3. Name it anything (e.g., `lead-bot`) → Click **Create**
4. Skip the optional role/access steps → Click **Done**

### 2.4 Download credentials.json

1. Click on your new service account in the list
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"** → **JSON**
4. A file will download — **rename it to `credentials.json`**
5. **Move it into the `business_lead_generator/` folder**

### 2.5 Share Your Google Sheet (Important!)

1. Open [Google Sheets](https://sheets.google.com) and create a sheet named **"Business Leads"**
   *(or let the script create it automatically)*
2. Click **Share**
3. Copy the **service account email** from your credentials.json file
   (looks like: `lead-bot@your-project.iam.gserviceaccount.com`)
4. Paste it in the Share dialog → set permission to **"Editor"** → Click **Send**

---

## Step 3 — Run the Script

### Interactive Mode (recommended for beginners)
```bash
python main.py
```
The script will ask you for city, category, and preferences.

### Direct Mode (for automation)
```bash
python main.py --city Jaipur --category Restaurants
python main.py --city Mumbai --category Salons --quality-filter
python main.py --city Delhi  --category Gyms   --schedule
```

### All CLI Options
| Flag | Description |
|------|-------------|
| `--city` | City to search (e.g., Jaipur) |
| `--category` | Business type (e.g., Restaurants) |
| `--quality-filter` | Only keep leads with rating > 4 AND phone |
| `--schedule` | Run daily at 09:00 (change in config.py) |

---

## Output

| Location | Description |
|----------|-------------|
| Google Sheets | Live spreadsheet with all leads |
| `output/business_leads_backup.csv` | Local CSV backup (always saved) |
| `output/scraper.log` | Full log of every run |

### Google Sheet Columns
| Name | Phone | Address | Rating | Website | City | Category | Source | Date Scraped |

---

## Configuration

Edit `config.py` to change settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_DELAY` | 2 | Seconds to wait between requests |
| `MAX_DELAY` | 5 | Max wait between requests |
| `MAX_RETRIES` | 3 | Times to retry a failed request |
| `MAX_SCROLLS` | 10 | How many times to scroll (more = more results) |
| `MIN_RATING` | 4.0 | Quality filter minimum rating |
| `DAILY_RUN_TIME` | "09:00" | Time for daily scheduled run |
| `HEADLESS` | True | Hide browser window during scraping |

---

## Troubleshooting

**"No records found"**
- JustDial may be blocking requests. Try again in a few minutes.
- Make sure Playwright is installed: `playwright install chromium`

**"credentials.json not found"**
- Follow Step 2 above to set up the Google Sheets API

**"Permission denied on Google Sheet"**
- Make sure you shared the sheet with your service account email (Step 2.5)

**Playwright browser not found**
- Run: `playwright install chromium`

---

## Adding More Websites Later

1. Open `scraper.py`
2. Create a new class extending `BaseScraper`
3. Implement the `scrape(city, category)` method
4. Register it in `ScraperFactory.SCRAPERS`

```python
class SulekhaScraper(BaseScraper):
    def scrape(self, city, category):
        # your logic here
        return records

# In ScraperFactory:
SCRAPERS = {
    'justdial': JustdialScraper,
    'sulekha': SulekhaScraper,   # <-- add here
}
```
