# Y Combinator Companies Scraper

A Python-based web scraper for extracting company information from Y Combinator's directory, specifically designed to handle infinite scroll pagination.

## Features

- **Infinite Scroll Handling**: Automatically scrolls to load all companies
- **Robust Data Extraction**: Extracts company name, batch, description, location, tags, and more
- **PostgreSQL Database**: Save data to AWS RDS PostgreSQL for easy querying
- **Industry Tags Updater**: Extract and update industry tags from individual company pages
- **Multiple Output Formats**: Saves data as both JSON and CSV
- **Error Handling**: Includes retry logic and comprehensive error handling
- **Headless Mode**: Can run with or without browser UI
- **Logging**: Detailed logging for debugging and monitoring

## Installation

1. Install Python 3.8 or higher
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the simple scraper:
```bash
python yc_scraper.py
```

### Advanced Usage

Run the advanced scraper with more options:
```bash
# Run with UI (default)
python yc_scraper_advanced.py

# Run in headless mode (no browser window)
python yc_scraper_advanced.py --headless

# Limit the number of scrolls
python yc_scraper_advanced.py --max-scrolls 10

# Use a custom URL
python yc_scraper_advanced.py --url "https://www.ycombinator.com/companies?batch=Summer%202024"
```

## Output Files

The scraper generates two types of files:

1. **JSON file**: `yc_companies_YYYYMMDD_HHMMSS.json`
   - Contains all company data with metadata
   - Includes scrape date and total count

2. **CSV file**: `yc_companies_YYYYMMDD_HHMMSS.csv`
   - Tabular format for easy analysis
   - Can be opened in Excel or Google Sheets

## Data Fields

- `name`: Company name
- `batch`: Y Combinator batch (e.g., "Summer 2024")
- `description`: Company description/tagline
- `location`: Company location
- `tags`: Industry tags/categories
- `team_size`: Number of employees (if available)
- `url`: Direct link to company profile on YC

## Database Integration

### Save to PostgreSQL

1. Set up PostgreSQL database (see `DATABASE_SETUP.md`)
2. Create `.env` file with your credentials
3. Run:
```bash
python save_to_postgres.py
```

### Update Industry Tags

After saving to PostgreSQL, you can extract and update industry tags:

```bash
# Test first
python test_industry_extraction.py

# Run update
python update_industries.py

# Or update specific batch
python update_industries.py --batch "Fall 2025"

# Test with limited companies
python update_industries.py --limit 10
```

See `QUICKSTART_INDUSTRY_UPDATE.md` for detailed instructions.

## Alternative Solutions

### Using Playwright (Alternative)

If you encounter issues with Selenium, you can use the Playwright-based scraper:

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Run the Playwright scraper
python yc_scraper_playwright.py
```

## Troubleshooting

1. **Chrome Driver Issues**: The script uses `webdriver-manager` to automatically download the correct Chrome driver. If you have issues, ensure Chrome browser is installed.

2. **Timeout Errors**: If the page loads slowly, you can modify the wait times in the script.

3. **Missing Data**: Some companies may have incomplete information. The scraper will extract whatever is available.

4. **Rate Limiting**: If you scrape too frequently, you might get rate limited. Add delays between runs.

## Legal Notice

Please ensure you comply with Y Combinator's Terms of Service and robots.txt when using this scraper. This tool is for educational purposes.



