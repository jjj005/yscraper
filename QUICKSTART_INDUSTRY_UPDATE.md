# Quick Start: Industry Tags Update

## TL;DR

```bash
# 1. Test everything works
python test_industry_extraction.py

# 2. Try with 5 companies first
python update_industries.py --limit 5

# 3. Run the full update
python update_industries.py
```

## What This Does

Updates the `industry` column in your PostgreSQL database by scraping industry tags from Y Combinator company pages.

**Before:**
```
Company: Parse
Industry: [] (empty)
```

**After:**
```
Company: Parse
Industry: ['developer-tools', 'api', 'big-data']
```

## Prerequisites

✅ You must have:
1. PostgreSQL database set up (see `DATABASE_SETUP.md`)
2. `.env` file with database credentials
3. Companies already in your database
4. Chrome browser installed

## Step-by-Step

### Step 1: Verify Setup

Run the test script to make sure everything is configured:

```bash
python test_industry_extraction.py
```

This checks:
- ✅ HTML parsing logic works
- ✅ Database connection works
- ✅ Selenium/Chrome setup works

If all tests pass, you're ready to proceed!

### Step 2: Test Run

Start with a small test (5 companies):

```bash
python update_industries.py --limit 5
```

Watch the output carefully. You should see:
```
[1/5] Processing: CompanyName
  Fetching: https://www.ycombinator.com/companies/...
    Found tag: developer-tools
    Found tag: api
  Total tags found: 2
  ✓ Updated with 2 tags: developer-tools, api
```

### Step 3: Full Update

If the test run looks good, run for all companies:

```bash
python update_industries.py
```

This will:
- Process all companies in your database
- Skip companies that already have industry tags
- Update the `industry` column
- Show progress updates every 10 companies

### Step 4: Verify Results

Check the database:

```sql
-- See updated companies
SELECT name, batch, industry 
FROM companies 
WHERE industry IS NOT NULL AND array_length(industry, 1) > 0
LIMIT 10;

-- Count how many have tags now
SELECT 
  COUNT(*) FILTER (WHERE industry IS NOT NULL AND array_length(industry, 1) > 0) as with_tags,
  COUNT(*) FILTER (WHERE industry IS NULL OR array_length(industry, 1) IS NULL) as without_tags,
  COUNT(*) as total
FROM companies;
```

## Common Use Cases

### Update Only Recent Batch

```bash
python update_industries.py --batch "Fall 2025"
```

### Re-scrape Everything (Force Update)

```bash
python update_industries.py --no-skip-existing
```

### Process in Chunks

```bash
# Process 100 at a time
python update_industries.py --limit 100

# Run multiple times - it will skip already-processed companies
```

## Troubleshooting

### "Failed to connect to database"
→ Check your `.env` file
→ Run: `python test_db_connection.py`

### "Failed to setup WebDriver"
→ Update Chrome browser
→ Run: `pip install --upgrade selenium webdriver-manager`

### "No industry tags found"
→ YC might have changed their HTML
→ Visit the company page manually and check if tags are there
→ Check the logs to see which company failed

### Script is interrupted
→ No problem! Just run it again
→ It will skip companies that already have tags

## Performance

- **Speed**: ~2-3 seconds per company
- **100 companies**: ~5 minutes
- **1000 companies**: ~50 minutes

The script runs in headless mode (background), so you can continue working while it runs.

## Files Created

This update added these files:

```
yscraper/
├── update_industries.py              # Main script
├── test_industry_extraction.py       # Test/verification script
├── INDUSTRY_UPDATER_README.md        # Detailed documentation
└── QUICKSTART_INDUSTRY_UPDATE.md     # This file
```

## Example Output

```
======================================================================
STARTING INDUSTRY UPDATE PROCESS
======================================================================
INFO:__main__:Found 150 companies to process

[1/150] Processing: Parse
  URL: https://www.ycombinator.com/companies/parse-bot
    Found tag: developer-tools
    Found tag: api
    Found tag: big-data
  ✓ Updated with 3 tags: developer-tools, api, big-data

[2/150] Processing: AnotherCompany
  ⏭️  Skipping (already has 2 tags)

----------------------------------------------------------------------
PROGRESS UPDATE
----------------------------------------------------------------------
  Total: 150
  Updated: 145
  Skipped: 4
  Errors: 1
----------------------------------------------------------------------

======================================================================
FINAL SUMMARY
======================================================================
  Total companies: 150
  Successfully updated: 145
  Skipped (already had tags): 4
  Errors: 1
======================================================================

Success rate: 99.3%
```

## What Gets Extracted

✅ **Included:**
- developer-tools
- api
- big-data
- healthcare
- fintech
- b2b
- saas
- etc.

❌ **Excluded:**
- Fall 2025, Winter 2024 (batch info)
- Active, Inactive (status)
- YC badges

## Tips

1. **Start small** - Always test with `--limit 5` first
2. **Monitor closely** - Watch the first 10-20 companies to make sure tags look correct
3. **Interrupt safely** - Press Ctrl+C if something looks wrong, progress is saved
4. **Re-run anytime** - Safe to run multiple times, skips already-processed companies

## Need More Help?

- **Detailed docs**: See `INDUSTRY_UPDATER_README.md`
- **Database setup**: See `DATABASE_SETUP.md`
- **Test script**: Run `test_industry_extraction.py`

## Integration with Your Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Run main scraper                                     │
│    python yc_scraper_working.py                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Save to PostgreSQL                                   │
│    python save_to_postgres.py                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Update industry tags  ← YOU ARE HERE                 │
│    python update_industries.py                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Use the data!                                        │
│    - Query database                                     │
│    - Build dashboards                                   │
│    - Export to CSV/Excel                                │
└─────────────────────────────────────────────────────────┘
```

---

Ready? Let's update those industry tags! 🚀

```bash
python test_industry_extraction.py
python update_industries.py --limit 5
python update_industries.py
```

