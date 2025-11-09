"""
Script to reprocess companies with empty founders
Extracts founders from the right panel of company pages
"""

import os
import time
import json
import re
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Selenium components
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, WebDriverException
    logger.info("Selenium imported successfully")
except ImportError:
    logger.error("Selenium not installed. Please run: pip install selenium")
    exit(1)

# Import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    logger.info("BeautifulSoup imported successfully")
except ImportError:
    logger.error("BeautifulSoup not installed. Please run: pip install beautifulsoup4")
    exit(1)

# Import webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    logger.info("Webdriver-manager imported successfully")
except ImportError:
    logger.error("Webdriver-manager not installed. Please run: pip install webdriver-manager")
    exit(1)


class FoundersReprocessor:
    def __init__(self):
        """Initialize the reprocessor"""
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        logger.info("Setting up Chrome WebDriver...")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.page_load_strategy = 'normal'
            
            logger.info("Installing/Finding ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path: {driver_path}")
            
            # Fix for Windows: webdriver-manager sometimes returns wrong file
            # Make sure we have the actual .exe file
            if os.name == 'nt':  # Windows
                if not driver_path.endswith('.exe'):
                    # Try to find chromedriver.exe in the same directory
                    driver_dir = os.path.dirname(driver_path)
                    possible_exe = os.path.join(driver_dir, 'chromedriver.exe')
                    if os.path.exists(possible_exe):
                        driver_path = possible_exe
                        logger.info(f"Fixed driver path to: {driver_path}")
                    else:
                        # Look in chromedriver-win32 subdirectory
                        possible_exe = os.path.join(driver_dir, 'chromedriver-win32', 'chromedriver.exe')
                        if os.path.exists(possible_exe):
                            driver_path = possible_exe
                            logger.info(f"Fixed driver path to: {driver_path}")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("WebDriver setup successful!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            
            # Try alternative approach - direct Chrome initialization
            try:
                logger.info("Trying direct Chrome initialization...")
                chrome_options = Options()
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
                self.wait = WebDriverWait(self.driver, 20)
                
                logger.info("Alternative WebDriver setup successful!")
                return True
                
            except Exception as e2:
                logger.error(f"Alternative setup also failed: {str(e2)}")
                return False
    
    def extract_founders_from_page(self, url):
        """Extract founders from company page - focusing on right panel"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            founders = []
            logger.info("Looking for founders...")
            
            # Strategy 1: Look for "Founders" heading in the right panel
            # The structure is: <div class="mb-2 mt-8 text-xl font-bold">Founders</div>
            # Followed by: <div class="space-y-4"> containing founder cards
            
            founders_heading = soup.find('div', class_=lambda x: x and 'text-xl' in str(x) and 'font-bold' in str(x), 
                                        string=re.compile(r'^Founders?$', re.I))
            
            if not founders_heading:
                # Try alternative: mb-2 mt-8 text-xl font-bold
                all_headings = soup.find_all('div', class_=lambda x: x and 'mb-2' in str(x) and 'mt-8' in str(x))
                for heading in all_headings:
                    if heading.get_text(strip=True).lower() == 'founders':
                        founders_heading = heading
                        break
            
            if founders_heading:
                logger.info("Found 'Founders' heading in right panel")
                
                # Find the next sibling which should be the space-y-4 div with founder cards
                founders_container = founders_heading.find_next_sibling('div', class_=lambda x: x and 'space-y' in str(x))
                
                if founders_container:
                    # Find all founder cards
                    founder_cards = founders_container.find_all('div', class_='ycdc-card-new', recursive=False)
                    logger.info(f"Found {len(founder_cards)} founder cards")
                    
                    for card in founder_cards:
                        try:
                            founder = {
                                'name': '',
                                'title': '',
                                'linkedin': '',
                                'twitter': ''
                            }
                            
                            # Extract name - look for text-xl font-bold or text-lg font-bold
                            name_div = card.find('div', class_=re.compile(r'(text-xl|text-lg).*font-bold'))
                            if name_div:
                                founder['name'] = name_div.get_text(strip=True)
                            
                            # Extract title - look for text-gray-600 or similar
                            title_div = card.find('div', class_=re.compile(r'text-gray-600|text-sm text-gray-600|text-\[15px\]'))
                            if title_div:
                                founder['title'] = title_div.get_text(strip=True)
                            
                            # Extract social links
                            links = card.find_all('a', href=True)
                            for link in links:
                                href = link.get('href', '')
                                if 'linkedin.com' in href:
                                    founder['linkedin'] = href
                                elif 'twitter.com' in href or 'x.com' in href:
                                    founder['twitter'] = href
                            
                            if founder['name']:
                                founders.append(founder)
                                logger.info(f"  Found founder: {founder['name']} - {founder['title']}")
                        
                        except Exception as e:
                            logger.warning(f"  Error extracting founder from card: {e}")
            
            # Strategy 2: Try the original patterns from the scraper if Strategy 1 didn't work
            if not founders:
                logger.info("Trying alternative patterns...")
                
                # Pattern: Section-based with "Active Founders" or "Former Founders"
                founders_headings = soup.find_all(string=re.compile(r'(Active|Former)\s+Founders?', re.I))
                
                for heading in founders_headings:
                    heading_text = heading.strip()
                    logger.info(f"Found {heading_text} section")
                    
                    founders_section = heading.find_parent('section')
                    if not founders_section:
                        founders_section = heading.find_parent('div', class_=lambda x: x and 'relative' in str(x))
                    
                    if founders_section:
                        founder_cards = founders_section.find_all('div', class_='ycdc-card-new')
                        
                        for card in founder_cards:
                            try:
                                founder = {
                                    'name': '',
                                    'title': '',
                                    'linkedin': '',
                                    'twitter': ''
                                }
                                
                                name_div = card.find('div', class_=re.compile(r'(text-xl|text-lg).*font-bold'))
                                if name_div:
                                    founder['name'] = name_div.get_text(strip=True)
                                
                                title_div = card.find('div', class_=re.compile(r'text-gray-600|text-sm text-gray-600|text-\[15px\]'))
                                if title_div:
                                    founder['title'] = title_div.get_text(strip=True)
                                
                                links = card.find_all('a', href=True)
                                for link in links:
                                    href = link.get('href', '')
                                    if 'linkedin.com' in href:
                                        founder['linkedin'] = href
                                    elif 'twitter.com' in href or 'x.com' in href:
                                        founder['twitter'] = href
                                
                                if founder['name']:
                                    founders.append(founder)
                                    logger.info(f"  Found founder: {founder['name']} - {founder['title']}")
                            
                            except Exception as e:
                                logger.warning(f"  Error extracting founder from card: {e}")
            
            logger.info(f"Total founders extracted: {len(founders)}")
            return founders
            
        except Exception as e:
            logger.error(f"Error extracting founders from {url}: {e}")
            return []
    
    def save_new_json(self, companies_with_founders):
        """Save reprocessed companies to a new JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'yc_companies_reprocessed_{timestamp}.json'
        
        logger.info(f"\nSaving results to: {output_file}")
        
        try:
            output_data = {
                'scrape_date': datetime.now().isoformat(),
                'total_companies': len(companies_with_founders),
                'companies': companies_with_founders
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(companies_with_founders)} companies to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    def get_company_details(self, url):
        """Get complete company details from jobs page"""
        try:
            jobs_url = f"{url}/jobs"
            logger.info(f"  Getting company details from: {jobs_url}")
            
            self.driver.get(jobs_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            company_data = {
                'founded_year': '',
                'team_size': '',
                'location': '',
                'status': '',
                'batch': '',
                'description': '',
                'industry': [],
                'company_website': ''
            }
            
            # Extract company info from the info card
            info_card = soup.find('div', class_='ycdc-card-new')
            if info_card:
                detail_rows = info_card.find_all('div', class_=lambda x: x and 'flex' in x and 'flex-row' in x and 'justify-between' in x)
                
                for row in detail_rows:
                    spans = row.find_all('span')
                    if len(spans) >= 2:
                        label = spans[0].get_text(strip=True).lower()
                        value = spans[1].get_text(strip=True)
                        
                        if 'founded' in label:
                            company_data['founded_year'] = value
                        elif 'team size' in label:
                            company_data['team_size'] = value
                        elif 'location' in label:
                            company_data['location'] = value
                        elif 'status' in label:
                            company_data['status'] = value
                        elif 'batch' in label:
                            company_data['batch'] = value
            
            # Get company name from page
            name_elem = soup.find('h1')
            if name_elem:
                company_data['name'] = name_elem.get_text(strip=True)
            
            # Get description
            desc_elem = soup.find('p', class_=lambda x: x and 'text-' in str(x))
            if desc_elem:
                company_data['description'] = desc_elem.get_text(strip=True)
            
            # Get company website
            website_links = soup.find_all('a', href=lambda x: x and x.startswith('http') and 'ycombinator.com' not in x)
            for link in website_links:
                if link.find('svg'):  # Has website icon
                    company_data['company_website'] = link.get('href', '')
                    break
            
            return company_data
            
        except Exception as e:
            logger.warning(f"  Error getting company details: {e}")
            return {}
    
    def reprocess(self, companies_file):
        """Main reprocessing method"""
        try:
            # Setup driver
            if not self.setup_driver():
                raise Exception("Failed to setup WebDriver")
            
            # Load companies to reprocess
            logger.info(f"Loading companies from: {companies_file}")
            with open(companies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            companies_to_process = data.get('companies', [])
            logger.info(f"Found {len(companies_to_process)} companies to reprocess")
            
            # Process each company and build complete data
            reprocessed_companies = []
            
            for i, company_info in enumerate(companies_to_process):
                try:
                    url = company_info.get('url', '')
                    name = company_info.get('name', 'Unknown')
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Processing {i+1}/{len(companies_to_process)}: {name}")
                    logger.info(f"{'='*60}")
                    
                    # Extract founders from company page
                    founders = self.extract_founders_from_page(url)
                    
                    # Get additional company details
                    company_details = self.get_company_details(url)
                    
                    # Build complete company object
                    company = {
                        'url': url,
                        'name': company_details.get('name', name),
                        'description': company_details.get('description', ''),
                        'batch': company_details.get('batch', company_info.get('batch', '')),
                        'location': company_details.get('location', ''),
                        'founded_year': company_details.get('founded_year', company_info.get('founded_year', '')),
                        'team_size': company_details.get('team_size', ''),
                        'status': company_details.get('status', ''),
                        'industry': company_details.get('industry', []),
                        'founders': founders,
                        'company_website': company_details.get('company_website', ''),
                        'jobs': []
                    }
                    
                    reprocessed_companies.append(company)
                    
                    logger.info(f"  Company data complete:")
                    logger.info(f"    Founders: {len(founders)}")
                    logger.info(f"    Batch: {company['batch']}")
                    logger.info(f"    Location: {company['location']}")
                    
                    # Small delay to be respectful
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {name}: {e}")
                    # Add company with empty founders on error
                    reprocessed_companies.append({
                        'url': url,
                        'name': name,
                        'description': '',
                        'batch': company_info.get('batch', ''),
                        'location': '',
                        'founded_year': company_info.get('founded_year', ''),
                        'team_size': '',
                        'status': '',
                        'industry': [],
                        'founders': [],
                        'company_website': '',
                        'jobs': []
                    })
                    continue
            
            # Save to new JSON file
            output_file = self.save_new_json(reprocessed_companies)
            
            logger.info(f"\n{'='*60}")
            logger.info("REPROCESSING COMPLETE!")
            logger.info(f"{'='*60}")
            logger.info(f"Processed {len(companies_to_process)} companies")
            logger.info(f"Successfully extracted founders for {sum(1 for c in reprocessed_companies if c['founders'])} companies")
            if output_file:
                logger.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Reprocessing failed: {str(e)}")
            raise
        finally:
            self.close()


def main():
    """Main function"""
    companies_file = 'companies_to_reprocess.json'
    
    if not os.path.exists(companies_file):
        logger.error(f"File not found: {companies_file}")
        logger.error("Please run find_empty_founders.py first")
        return
    
    logger.info("Starting Founders Reprocessor...")
    logger.info(f"Input file: {companies_file}")
    
    reprocessor = FoundersReprocessor()
    
    try:
        reprocessor.reprocess(companies_file)
    except KeyboardInterrupt:
        logger.warning("\nReprocessing interrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {str(e)}")


if __name__ == "__main__":
    main()

