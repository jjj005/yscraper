"""
Script to update industry column from Y Combinator company pages
Extracts industry tags from individual company pages and updates the PostgreSQL database
"""

import os
import time
import logging
import re
from dotenv import load_dotenv
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required packages
try:
    import psycopg2
    logger.info("✓ psycopg2 imported successfully")
except ImportError:
    logger.error("psycopg2 not installed. Please run: pip install psycopg2-binary")
    exit(1)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, WebDriverException
    logger.info("✓ Selenium imported successfully")
except ImportError:
    logger.error("Selenium not installed. Please run: pip install selenium")
    exit(1)

try:
    from bs4 import BeautifulSoup
    logger.info("✓ BeautifulSoup imported successfully")
except ImportError:
    logger.error("BeautifulSoup not installed. Please run: pip install beautifulsoup4")
    exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    logger.info("✓ Webdriver-manager imported successfully")
except ImportError:
    logger.error("Webdriver-manager not installed. Please run: pip install webdriver-manager")
    exit(1)

# Load environment variables
load_dotenv()


class IndustryUpdater:
    def __init__(self):
        """Initialize the industry updater"""
        self.conn = None
        self.cursor = None
        self.driver = None
        self.wait = None
        self.stats = {
            'total': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            logger.info("Connecting to PostgreSQL database...")
            
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DATABASE'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            
            self.cursor = self.conn.cursor()
            logger.info("✓ Successfully connected to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        logger.info("Setting up Chrome WebDriver...")
        
        try:
            chrome_options = Options()
            
            # Basic options
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Headless mode for faster processing
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Page load strategy
            chrome_options.page_load_strategy = 'normal'
            
            # Create driver
            logger.info("Installing/Finding ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            # Create wait object
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("✓ WebDriver setup successful!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            return False
    
    def extract_industry_tags(self, company_url):
        """
        Extract industry tags from a company page
        
        Args:
            company_url: Full URL to the company page (e.g., https://www.ycombinator.com/companies/parse-bot)
        
        Returns:
            list: List of industry tags
        """
        try:
            logger.info(f"  Fetching: {company_url}")
            self.driver.get(company_url)
            time.sleep(2)  # Wait for page load
            
            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all pill containers with industry links
            industry_tags = []
            
            # Pattern 1: Links to /companies/industry/{tag}
            industry_links = soup.find_all('a', href=re.compile(r'^/companies/industry/'))
            
            for link in industry_links:
                # Extract the industry tag from the href
                href = link.get('href', '')
                match = re.search(r'/companies/industry/(.+)$', href)
                if match:
                    industry_tag = match.group(1)
                    # Clean and validate the tag
                    industry_tag = industry_tag.strip()
                    if industry_tag and industry_tag not in industry_tags:
                        industry_tags.append(industry_tag)
                        logger.info(f"    Found tag: {industry_tag}")
            
            # Pattern 2: Also check for pill text content (as fallback)
            # Look for pills that are not batch/status indicators
            pill_divs = soup.find_all('div', class_=re.compile(r'yc-tw-Pill'))
            
            for pill in pill_divs:
                # Skip if it's a batch indicator (contains YC logo svg or batch text)
                if pill.find('svg') and 'Y Combinator Logo' in str(pill):
                    continue
                
                # Skip if it's an Active/Inactive status (contains colored dot)
                if pill.find('div', class_=re.compile(r'rounded-full.*bg-green|bg-red|bg-gray')):
                    continue
                
                # Get the text content
                pill_text = pill.get_text(strip=True)
                
                # Skip batch patterns (Season Year)
                if re.match(r'^(Winter|Spring|Summer|Fall)\s+\d{4}$', pill_text, re.I):
                    continue
                
                # Skip Active/Inactive status
                if pill_text.lower() in ['active', 'inactive', 'public', 'acquired']:
                    continue
                
                # Check if this pill has a parent link to industry
                parent_link = pill.find_parent('a', href=re.compile(r'/companies/industry/'))
                if parent_link and pill_text and pill_text not in industry_tags:
                    # Normalize the tag (lowercase with hyphens)
                    normalized_tag = pill_text.lower().replace(' ', '-')
                    if normalized_tag not in industry_tags:
                        industry_tags.append(normalized_tag)
                        logger.info(f"    Found tag (from pill): {normalized_tag}")
            
            logger.info(f"  Total tags found: {len(industry_tags)}")
            return industry_tags
            
        except Exception as e:
            logger.error(f"  Error extracting tags from {company_url}: {e}")
            return []
    
    def get_companies(self, batch_filter=None, limit=None):
        """
        Get companies from database
        
        Args:
            batch_filter: Optional batch to filter by (e.g., 'Fall 2025')
            limit: Optional limit on number of companies to process
        
        Returns:
            list: List of (id, name, url) tuples
        """
        try:
            query = "SELECT id, name, url FROM companies WHERE url IS NOT NULL"
            params = []
            
            if batch_filter:
                query += " AND batch = %s"
                params.append(batch_filter)
            
            query += " ORDER BY id"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            logger.info(f"\n=== EXECUTING SQL QUERY ===")
            logger.info(f"Query: {query}")
            logger.info(f"Params: {params}")
            
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            companies = self.cursor.fetchall()
            logger.info(f"\n=== SQL RESULT ===")
            logger.info(f"Found {len(companies)} companies from PostgreSQL")
            
            if companies:
                logger.info(f"\nFirst company from database:")
                logger.info(f"  id: {companies[0][0]}")
                logger.info(f"  name: {companies[0][1]}")
                logger.info(f"  url: {companies[0][2]}")
            
            return companies
            
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_company_industry(self, company_id, company_name, company_url, industry_tags):
        """
        Update the industry column for a company
        
        Args:
            company_id: Company ID in database (not used, kept for compatibility)
            company_name: Company name (for logging)
            company_url: Company URL (for matching)
            industry_tags: List of industry tags
        """
        try:
            logger.info(f"\n  === STEP 1: FIND COMPANY BY URL ===")
            logger.info(f"  URL to match: {company_url}")
            
            # First check if the company exists by URL
            self.cursor.execute("""
                SELECT id, name, url, industry FROM companies WHERE url = %s
            """, (company_url,))
            existing = self.cursor.fetchone()
            
            if not existing:
                logger.error(f"  ✗ Company with URL={company_url} NOT FOUND in PostgreSQL!")
                return False
            
            found_id = existing[0]
            found_name = existing[1]
            found_url = existing[2]
            current_industry = existing[3]
            
            logger.info(f"  ✓ Found in PostgreSQL:")
            logger.info(f"    id: {found_id}")
            logger.info(f"    name: {found_name}")
            logger.info(f"    url: {found_url}")
            logger.info(f"    current industry: {current_industry}")
            
            logger.info(f"\n  === STEP 2: UPDATE DATABASE ===")
            logger.info(f"  New tags to save: {industry_tags}")
            
            # Update using URL to match exact company
            self.cursor.execute("""
                UPDATE companies 
                SET industry = %s::text[], updated_at = CURRENT_TIMESTAMP
                WHERE url = %s
            """, (industry_tags, company_url))
            
            rows_updated = self.cursor.rowcount
            logger.info(f"  SQL UPDATE executed: {rows_updated} row(s) affected")
            
            self.conn.commit()
            logger.info(f"  ✓ Transaction COMMITTED to PostgreSQL")
            
            logger.info(f"\n  === STEP 3: VERIFY UPDATE ===")
            
            if rows_updated > 0:
                # Verify the update by reading back using URL
                self.cursor.execute("""
                    SELECT id, name, industry FROM companies WHERE url = %s
                """, (company_url,))
                result = self.cursor.fetchone()
                
                if result:
                    verify_id = result[0]
                    verify_name = result[1]
                    saved_tags = result[2] if result[2] else []
                    
                    logger.info(f"  ✓ Read back from PostgreSQL:")
                    logger.info(f"    id: {verify_id}")
                    logger.info(f"    name: {verify_name}")
                    logger.info(f"    industry column: {saved_tags}")
                    logger.info(f"  ✓✓✓ SUCCESS! Database updated and verified!")
                    return True
                else:
                    logger.error(f"  ✗ Could not verify - company disappeared!")
                    return False
            else:
                logger.warning(f"  ⚠️  No rows updated!")
                return False
            
        except Exception as e:
            logger.error(f"  ✗ Error updating company {company_name}: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            return False
    
    def process_companies(self, batch_filter=None, limit=None, skip_existing=True):
        """
        Process companies and update their industry tags
        
        Args:
            batch_filter: Optional batch to filter by
            limit: Optional limit on number of companies
            skip_existing: Skip companies that already have industry tags
        """
        logger.info("\n" + "="*70)
        logger.info("STARTING INDUSTRY UPDATE PROCESS")
        logger.info("="*70)
        
        # Get companies
        companies = self.get_companies(batch_filter, limit)
        self.stats['total'] = len(companies)
        
        if not companies:
            logger.warning("No companies to process")
            return
        
        logger.info(f"\nProcessing {len(companies)} companies...")
        logger.info(f"Skip existing: {skip_existing}")
        logger.info("")
        
        for i, (company_id, company_name, company_url) in enumerate(companies, 1):
            try:
                logger.info(f"\n[{i}/{len(companies)}] Processing: {company_name}")
                logger.info(f"  URL: {company_url}")
                
                # Check if company already has industry tags
                if skip_existing:
                    self.cursor.execute(
                        "SELECT industry FROM companies WHERE id = %s",
                        (company_id,)
                    )
                    result = self.cursor.fetchone()
                    existing_industry = result[0] if result else None
                    
                    if existing_industry and len(existing_industry) > 0:
                        logger.info(f"  ⏭️  Skipping (already has {len(existing_industry)} tags: {existing_industry})")
                        self.stats['skipped'] += 1
                        continue
                
                # Extract industry tags
                industry_tags = self.extract_industry_tags(company_url)
                
                if industry_tags:
                    # Update database
                    logger.info(f"  Found {len(industry_tags)} tags: {', '.join(industry_tags)}")
                    if self.update_company_industry(company_id, company_name, company_url, industry_tags):
                        self.stats['updated'] += 1
                    else:
                        logger.error(f"  ✗ Failed to update database")
                        self.stats['errors'] += 1
                else:
                    logger.warning(f"  ⚠️  No industry tags found")
                    # Still update to empty array to mark as processed
                    if self.update_company_industry(company_id, company_name, company_url, []):
                        self.stats['updated'] += 1
                    else:
                        self.stats['errors'] += 1
                
                # Small delay to be respectful
                time.sleep(1)
                
                # Progress update every 10 companies
                if i % 10 == 0:
                    self.print_progress()
                
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                self.stats['errors'] += 1
                continue
        
        # Final summary
        self.print_summary()
    
    def print_progress(self):
        """Print progress update"""
        logger.info("\n" + "-"*70)
        logger.info("PROGRESS UPDATE")
        logger.info("-"*70)
        logger.info(f"  Total: {self.stats['total']}")
        logger.info(f"  Updated: {self.stats['updated']}")
        logger.info(f"  Skipped: {self.stats['skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info("-"*70 + "\n")
    
    def print_summary(self):
        """Print final summary"""
        logger.info("\n" + "="*70)
        logger.info("FINAL SUMMARY")
        logger.info("="*70)
        logger.info(f"  Total companies: {self.stats['total']}")
        logger.info(f"  Successfully updated: {self.stats['updated']}")
        logger.info(f"  Skipped (already had tags): {self.stats['skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info("="*70)
        
        # Calculate success rate
        if self.stats['total'] > 0:
            processed = self.stats['updated'] + self.stats['skipped']
            success_rate = (processed / self.stats['total']) * 100
            logger.info(f"\nSuccess rate: {success_rate:.1f}%")
    
    def close(self):
        """Close database and browser connections"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Browser closed")
        
        if self.cursor:
            self.cursor.close()
        
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update industry tags for Y Combinator companies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all companies
  python update_industries.py

  # Update only Fall 2025 batch
  python update_industries.py --batch "Fall 2025"

  # Update first 10 companies (for testing)
  python update_industries.py --limit 10

  # Update all, including those with existing tags
  python update_industries.py --no-skip-existing

  # Combine options
  python update_industries.py --batch "Fall 2025" --limit 20
        """
    )
    
    parser.add_argument(
        '--batch',
        help='Filter by batch (e.g., "Fall 2025", "Summer 2024")',
        default=None
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of companies to process (useful for testing)',
        default=None
    )
    
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Process all companies, even those with existing industry tags'
    )
    
    args = parser.parse_args()
    
    # Check for .env file
    if not os.path.exists('.env'):
        logger.error("\n.env file not found!")
        logger.error("Please create a .env file with your PostgreSQL credentials")
        logger.error("See DATABASE_SETUP.md for details")
        return
    
    # Initialize updater
    updater = IndustryUpdater()
    
    try:
        # Connect to database
        if not updater.connect_db():
            logger.error("Failed to connect to database")
            return
        
        # Setup Selenium driver
        if not updater.setup_driver():
            logger.error("Failed to setup WebDriver")
            return
        
        # Process companies
        updater.process_companies(
            batch_filter=args.batch,
            limit=args.limit,
            skip_existing=not args.no_skip_existing
        )
        
    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user")
        updater.print_summary()
    except Exception as e:
        logger.error(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        updater.close()


if __name__ == "__main__":
    main()

