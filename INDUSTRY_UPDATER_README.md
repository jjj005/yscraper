# Industry Tags Updater

## Overview

This script updates the `industry` column in the PostgreSQL database by extracting industry tags from individual Y Combinator company pages.

## What It Does

1. Connects to your PostgreSQL database
2. Fetches companies from the `companies` table
3. Visits each company's YC page (e.g., `ycombinator.com/companies/parse-bot`)
4. Extracts industry tags from the HTML
5. Filters out unnecessary tags (batch info, Active status, etc.)
6. Updates the `industry` column in the database

## Industry Tag Extraction

The script extracts tags from links like:
```html
<a href="/companies/industry/developer-tools">
  <div class="yc-tw-Pill">developer-tools</div>
</a>
```

### Tags Included ✅
- `developer-tools`
- `api`
- `big-data`
- `healthcare`
- `fintech`
- etc.

### Tags Excluded ❌
- Batch tags: `Fall 2025`, `Winter 2025`, `Summer 2024`, etc.
- Status tags: `Active`, `Inactive`, `Public`, `Acquired`
- YC-specific badges

## Prerequisites

1. **Environment Setup**
   - Make sure you have a `.env` file with PostgreSQL credentials
   - See `DATABASE_SETUP.md` for database setup instructions

2. **Required Packages**
   All packages should already be installed if you've set up the main scraper:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
# Update all companies (skips those with existing tags)
python update_industries.py
```

### Advanced Options

```bash
# Update only a specific batch
python update_industries.py --batch "Fall 2025"

# Test with first 10 companies
python update_industries.py --limit 10

# Update all companies, even those with existing tags
python update_industries.py --no-skip-existing

# Combine options
python update_industries.py --batch "Fall 2025" --limit 20 --no-skip-existing
```

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--batch` | Filter by specific batch | `--batch "Fall 2025"` |
| `--limit` | Limit number of companies to process | `--limit 50` |
| `--no-skip-existing` | Re-process companies that already have tags | `--no-skip-existing` |

## Examples

### Example 1: Test Run
Start with a small test to make sure everything works:
```bash
python update_industries.py --limit 5
```

### Example 2: Update Specific Batch
Update only companies from a recent batch:
```bash
python update_industries.py --batch "Fall 2025"
```

### Example 3: Full Update
Update all companies that don't have industry tags:
```bash
python update_industries.py
```

### Example 4: Force Re-scrape
Re-scrape all companies, even those with existing tags:
```bash
python update_industries.py --no-skip-existing
```

## Output Example

```
======================================================================
STARTING INDUSTRY UPDATE PROCESS
======================================================================
INFO:__main__:Found 150 companies to process

Processing 150 companies...
Skip existing: True

[1/150] Processing: Parse
  URL: https://www.ycombinator.com/companies/parse-bot
  Fetching: https://www.ycombinator.com/companies/parse-bot
    Found tag: developer-tools
    Found tag: api
    Found tag: big-data
  Total tags found: 3
  ✓ Updated with 3 tags: developer-tools, api, big-data

[2/150] Processing: AnotherCompany
  URL: https://www.ycombinator.com/companies/another-company
  ⏭️  Skipping (already has 2 tags)

[3/150] Processing: ThirdCompany
  URL: https://www.ycombinator.com/companies/third-company
  Fetching: https://www.ycombinator.com/companies/third-company
    Found tag: healthcare
    Found tag: ai
  Total tags found: 2
  ✓ Updated with 2 tags: healthcare, ai

----------------------------------------------------------------------
PROGRESS UPDATE
----------------------------------------------------------------------
  Total: 150
  Updated: 2
  Skipped: 1
  Errors: 0
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

## How It Works

### 1. Tag Extraction Strategy

The script uses two patterns to find industry tags:

**Pattern 1: Industry Links**
```python
# Looks for: <a href="/companies/industry/TAGNAME">
industry_links = soup.find_all('a', href=re.compile(r'^/companies/industry/'))
```

**Pattern 2: Pill Elements** (Fallback)
```python
# Looks for: <div class="yc-tw-Pill"> inside industry links
pill_divs = soup.find_all('div', class_=re.compile(r'yc-tw-Pill'))
```

### 2. Tag Filtering

The script automatically filters out:
- **Batch indicators**: Contains YC logo SVG or matches "Season YYYY" pattern
- **Status indicators**: Contains colored dot (green/red/gray circles)
- **Explicit exclusions**: "Active", "Inactive", "Public", "Acquired"

### 3. Database Update

```sql
UPDATE companies 
SET industry = ARRAY['developer-tools', 'api', 'big-data'], 
    updated_at = CURRENT_TIMESTAMP
WHERE id = 123;
```

## Performance

- **Speed**: ~2-3 seconds per company (including page load and processing)
- **Headless mode**: Runs in background, no visible browser window
- **Respectful delays**: 1-second delay between requests
- **Progress updates**: Shows progress every 10 companies

### Estimated Time

| Companies | Estimated Time |
|-----------|----------------|
| 10 | ~30 seconds |
| 50 | ~2.5 minutes |
| 100 | ~5 minutes |
| 500 | ~25 minutes |
| 1000 | ~50 minutes |

## Troubleshooting

### Issue: "Failed to connect to database"
**Solution:**
- Check your `.env` file has correct credentials
- Verify PostgreSQL instance is running
- Test connection: `python test_db_connection.py`

### Issue: "Failed to setup WebDriver"
**Solution:**
- Make sure Chrome browser is installed
- Update Chrome to latest version
- Try: `pip install --upgrade selenium webdriver-manager`

### Issue: "No industry tags found" for most companies
**Solution:**
- Check if YC changed their HTML structure
- Run with `--limit 1` and inspect the company page manually
- The script logs which company it's processing - visit that URL in your browser

### Issue: Script is too slow
**Solution:**
- The script uses headless mode (already optimized)
- You can process in batches: `--batch "Fall 2025"`
- Or process companies in parallel (advanced - requires modification)

### Issue: Interrupted in the middle
**Solution:**
- Just run again with same options
- Script will skip companies that already have tags (unless you use `--no-skip-existing`)
- Progress is saved to database after each company

## Database Schema

The `industry` column in the `companies` table:
- Type: `TEXT[]` (PostgreSQL array)
- Example: `{'developer-tools', 'api', 'big-data'}`

### Querying Industry Tags

```sql
-- Find all companies with 'healthcare' tag
SELECT name, batch, industry 
FROM companies 
WHERE 'healthcare' = ANY(industry);

-- Find companies with multiple specific tags
SELECT name, batch, industry 
FROM companies 
WHERE industry @> ARRAY['developer-tools', 'api'];

-- Count companies by industry
SELECT unnest(industry) as tag, COUNT(*) as count
FROM companies
GROUP BY tag
ORDER BY count DESC;

-- Find companies with no industry tags
SELECT name, batch, url
FROM companies
WHERE industry IS NULL OR array_length(industry, 1) IS NULL;
```

## Best Practices

### 1. Start with a Test Run
```bash
python update_industries.py --limit 5
```
This helps you verify everything works before processing all companies.

### 2. Process by Batch
If you have many companies, process them by batch:
```bash
python update_industries.py --batch "Fall 2025"
python update_industries.py --batch "Summer 2024"
# etc.
```

### 3. Monitor Progress
The script logs everything. If you see consistent errors or "No tags found", stop and investigate.

### 4. Run Periodically
When new companies are added to your database, run this script to update their industry tags.

### 5. Backup First (Optional)
For peace of mind, backup your database before running:
```bash
pg_dump -h your-endpoint -U your_user -d yc_companies > backup_before_industry_update.sql
```

## Integration with Main Scraper

This script is separate from the main scraper (`yc_scraper_working.py`) because:
1. Industry tags are best extracted from individual company pages (more complete)
2. You can run this as a separate update step
3. Allows for re-processing if YC updates their tags

### Workflow

```
1. Run main scraper to get company data
   → python yc_scraper_working.py

2. Save to database
   → python save_to_postgres.py

3. Update industry tags
   → python update_industries.py

4. Query and use data!
```

## Notes

- The script runs in **headless mode** (no visible browser window)
- Each company update is **committed immediately** (safe to interrupt)
- **Respects YC's servers** with delays between requests
- **Idempotent**: Safe to run multiple times
- **Skip existing**: By default, won't re-scrape companies that already have tags

## Future Enhancements

Possible improvements for future versions:
- [ ] Parallel processing (multiple browser instances)
- [ ] Proxy rotation for faster processing
- [ ] Compare old vs new tags and log changes
- [ ] Export tag statistics
- [ ] Validate tags against known YC industry list

## Support

If you encounter issues:
1. Check the logs - they're very detailed
2. Try with `--limit 1` to test a single company
3. Verify the company page manually in your browser
4. Check if YC changed their HTML structure
5. Review `DATABASE_SETUP.md` for database issues

## License

Same as the main project.

