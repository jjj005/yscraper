# Founders Reprocessing Guide

## Overview

I've analyzed your JSON files and found **47 companies** with empty `founders` arrays that need to be reprocessed.

## Files Created

1. **`find_empty_founders.py`** - Identifies companies with empty founders
2. **`reprocess_founders.py`** - Extracts founders from company pages
3. **`companies_to_reprocess.json`** - List of companies to fix (already generated)

## Summary of Empty Founders

- `yc_companies_20251013_042409.json`: 27 companies with empty founders
- `yc_companies_20251013_085852.json`: 18 companies with empty founders  
- `yc_companies_20251013_105334.json`: 2 companies with empty founders
- **Total unique companies**: 47

## Sample Companies to Reprocess

1. Caire Health (S21) - https://www.ycombinator.com/companies/caire-health
2. bloop (S21) - https://www.ycombinator.com/companies/bloop
3. Zuma (S21) - https://www.ycombinator.com/companies/resident-boost
4. Mentum (S21) - https://www.ycombinator.com/companies/mentum
5. Patterns (S21) - https://www.ycombinator.com/companies/patterns
... and 42 more

## How to Run

### Step 1: Already completed ✓
```bash
python find_empty_founders.py
```
This has already been run and generated `companies_to_reprocess.json`

### Step 2: Reprocess the companies
```bash
python reprocess_founders.py
```

This will:
1. Open Chrome browser (visible, not headless)
2. Visit each of the 47 company pages
3. Extract founder information from the right panel
4. Update all 3 JSON files with the new founder data
5. Take approximately 2-3 minutes (with 2 second delay between pages)

## What the Reprocessor Does

The `reprocess_founders.py` script:

1. **Loads** the list of companies from `companies_to_reprocess.json`
2. **Visits** each company page using Selenium
3. **Extracts** founders from the right panel using multiple strategies:
   - Looks for "Founders" heading in the sidebar
   - Finds founder cards with class `ycdc-card-new`
   - Extracts: name, title, LinkedIn URL, Twitter URL
4. **Updates** all JSON files in-place (preserves all other data)
5. **Logs** progress for each company

## Founder Extraction Strategy

The script specifically targets the **right panel** structure:
```html
<div class="mb-2 mt-8 text-xl font-bold">Founders</div>
<div class="space-y-4">
  <div class="ycdc-card-new">
    <!-- Founder name, title, social links -->
  </div>
</div>
```

It also has fallback patterns for:
- "Active Founders" sections
- "Former Founders" sections
- Alternative card layouts

## Expected Results

After running, you should see:
- Updated founders data in all 3 JSON files
- Console output showing which companies were updated
- Summary of how many founders were found for each company

## Notes

- The script will **NOT** create new files - it updates existing ones
- Chrome browser will open visibly so you can see the progress
- Each page visit has a 2-second delay to be respectful to the server
- If a company still has no founders found, it will remain empty (some companies may legitimately have no founder info on their page)

## Manual Verification

After running, you can verify with:
```bash
python find_empty_founders.py
```
This should show fewer (or zero) companies with empty founders.

## Troubleshooting

If you encounter issues:

1. **Chrome doesn't open**: Make sure Chrome browser is installed
2. **ChromeDriver error**: The script will auto-download the correct version
3. **Timeout errors**: Increase the `time.sleep()` values in the script
4. **Still finding empty founders**: Some companies may not have founder info visible on their public pages

## Next Steps

1. Run `python reprocess_founders.py` when ready
2. Wait for it to complete (~2-3 minutes)
3. Verify results by running `find_empty_founders.py` again
4. Check a few updated companies manually to ensure data quality



