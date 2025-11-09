"""
Y Combinator Companies Scraper - Enhanced Version
Extracts comprehensive company data including founders, jobs, and industry tags
"""

import os
import time
import json
import csv
import re
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse

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
    logger.info("✓ Selenium imported successfully")
except ImportError:
    logger.error("Selenium not installed. Please run: pip install selenium")
    exit(1)

# Import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    logger.info("✓ BeautifulSoup imported successfully")
except ImportError:
    logger.error("BeautifulSoup not installed. Please run: pip install beautifulsoup4")
    exit(1)

# Import webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    logger.info("✓ Webdriver-manager imported successfully")
except ImportError:
    logger.error("Webdriver-manager not installed. Please run: pip install webdriver-manager")
    exit(1)


class YCombinatorScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.driver = None
        self.companies = []
        self.wait = None
        self.fetch_detailed_info = True  # Default to True
        
    def setup_driver(self):
        """Set up Chrome WebDriver - simplified version"""
        logger.info("Setting up Chrome WebDriver...")
        
        try:
            # Chrome options - minimal for better compatibility
            chrome_options = Options()
            
            # Basic options that work reliably
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Remove headless for debugging
            # chrome_options.add_argument('--headless')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Page load strategy
            chrome_options.page_load_strategy = 'normal'
            
            # Create driver with automatic ChromeDriver management
            logger.info("Installing/Finding ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path: {driver_path}")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Create wait object
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✓ WebDriver setup successful!")
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
                
                logger.info("✓ Alternative WebDriver setup successful!")
                return True
                
            except Exception as e2:
                logger.error(f"Alternative setup also failed: {str(e2)}")
                return False
    
    def load_page(self, url):
        """Load the Y Combinator companies page"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for the page to load
            time.sleep(5)  # Give initial load time
            
            # Wait for company elements to appear
            logger.info("Waiting for companies to load...")
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/companies/']"))
            )
            
            logger.info("✓ Page loaded successfully!")
            return True
            
        except TimeoutException:
            logger.error("Timeout: Companies did not load")
            return False
        except Exception as e:
            logger.error(f"Error loading page: {str(e)}")
            return False
    
    def scroll_and_load_all(self):
        """Scroll to load all companies"""
        logger.info("Starting to scroll and load all companies...")
        
        last_count = 0
        no_change_count = 0
        scroll_count = 0
        
        while True:
            # Get current companies count
            companies = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/companies/']")
            current_count = len(companies)
            
            logger.info(f"Scroll {scroll_count + 1}: Found {current_count} companies")
            
            # Check if we're still loading new companies
            if current_count == last_count:
                no_change_count += 1
                if no_change_count >= 3:
                    logger.info("No new companies loaded after 3 scrolls. Assuming all loaded.")
                    break
            else:
                no_change_count = 0
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content
            time.sleep(2.5)
            
            last_count = current_count
            scroll_count += 1
            
            # Safety limit
            if scroll_count > 100:
                logger.warning("Reached maximum scroll limit (100)")
                break
        
        logger.info(f"✓ Scrolling complete! Total companies found: {current_count}")
        return current_count
    
    def extract_company_data(self):
        """Extract basic company list from the main page"""
        logger.info("Step 1: Extracting company list from main page...")
        
        # Get page source
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all company links - simpler approach
        all_links = soup.find_all('a', href=True)
        companies_data = {}
        
        for link in all_links:
            href = link.get('href', '')
            
            # Check if it's a company link
            if '/companies/' not in href:
                continue
                
            # Skip non-company pages
            if any(skip in href for skip in ['/jobs', '/founders', '/directory', '/apply', 'startup-school']):
                continue
            
            # Extract company slug
            parts = href.strip('/').split('/')
            if len(parts) >= 2 and parts[-2] == 'companies' and parts[-1]:
                company_slug = parts[-1]
                
                # Skip system pages
                if company_slug in ['founders', 'directory', 'apply']:
                    continue
                
                company_url = f"https://www.ycombinator.com/companies/{company_slug}"
                
                # Skip if already processed
                if company_url in companies_data:
                    continue
                
                # Get company name - need to be more careful about extraction
                company_name = ""
                
                # First try to get the h2 element within or near the link
                h2_elem = link.find('h2')
                if h2_elem:
                    company_name = h2_elem.get_text(strip=True)
                else:
                    # Try to find h2 in parent structure
                    parent = link.find_parent()
                    if parent:
                        h2_elem = parent.find('h2')
                        if h2_elem:
                            # Make sure this h2 contains a link to the same company
                            h2_link = h2_elem.find('a', href=lambda x: x and company_slug in x)
                            if h2_link:
                                company_name = h2_elem.get_text(strip=True)
                
                # If still no name, get link text but clean it up
                if not company_name:
                    company_name = link.get_text(strip=True)
                    # If the text is too long, it probably contains extra info
                    if len(company_name) > 50:
                        # Try to extract just the company name part
                        # Usually the company name is the first part before location/description
                        parts = company_name.split('\n')
                        if parts:
                            company_name = parts[0].strip()
                        # Also try splitting by common patterns
                        import re
                        match = re.match(r'^([A-Za-z0-9\s\.\-&]+?)(?:[A-Z][a-z]+,|Fall|Winter|Spring|Summer|\d{4})', company_name)
                        if match:
                            company_name = match.group(1).strip()
                
                # Skip if no valid name
                if not company_name or len(company_name) < 2:
                    continue
                
                # Initialize company data
                company = {
                    'url': company_url,
                    'name': company_name,
                    'description': '',
                    'batch': '',
                    'location': '',
                    'founded_year': '',
                    'team_size': '',
                    'status': '',
                    'industry': [],
                    'founders': [],
                    'company_website': '',
                    'jobs': []
                }
                
                # Try to extract basic info from the main page if available
                # Find the closest parent that contains this company's data
                container = link
                for _ in range(10):  # Look up to 10 levels
                    parent = container.find_parent()
                    if not parent:
                        break
                    # Check if this container has other company links - if so, it's too broad
                    other_company_links = parent.find_all('a', href=lambda x: x and '/companies/' in x and x != href)
                    if len(other_company_links) > 0:
                        break
                    container = parent
                
                if container and container != link:
                    # Extract description
                    desc_elem = container.find('p')
                    if desc_elem:
                        company['description'] = desc_elem.get_text(strip=True)
                    
                    # Extract batch - look for season + year pattern
                    container_text = container.get_text()
                    for season in ['Winter', 'Spring', 'Summer', 'Fall']:
                        for year in ['2024', '2025', '2026']:
                            pattern = f"{season} {year}"
                            if pattern in container_text:
                                company['batch'] = pattern
                                break
                        if company['batch']:
                            break
                    
                    # Extract industry from pills - only from this company's container
                    pill_wrapper = container.find('div', class_=lambda x: x and 'pillWrapper' in str(x))
                    if pill_wrapper:
                        pills = pill_wrapper.find_all('span', class_=lambda x: x and 'pill' in str(x))
                        for pill in pills:
                            pill_text = pill.get_text(strip=True)
                            # Skip batch info and YC badges
                            if (pill_text and 
                                not any(y in pill_text for y in ['2024', '2025', '2026', 'Winter', 'Spring', 'Summer', 'Fall']) and
                                pill_text not in company['industry']):
                                company['industry'].append(pill_text)
                
                companies_data[company_url] = company
        
        self.companies = list(companies_data.values())
        logger.info(f"✓ Extracted {len(self.companies)} companies from main page")
        
        # Display sample of extracted companies
        if self.companies:
            logger.info("\nSample of extracted companies:")
            for i, company in enumerate(self.companies[:5]):
                logger.info(f"  {i+1}. {company['name']} - {company['url']}")
            if len(self.companies) > 5:
                logger.info(f"  ... and {len(self.companies) - 5} more companies")
        
        # Now get detailed info for each company
        if self.fetch_detailed_info:
            logger.info("\nProceeding to extract detailed information...")
            self.get_detailed_company_info()
        else:
            logger.info("Skipping detailed info extraction (disabled in config)")
    
    def get_detailed_company_info(self):
        """Visit each company page to get founders, website, and jobs info"""
        logger.info(f"Step 2: Getting detailed info for {len(self.companies)} companies...")
        
        for i, company in enumerate(self.companies):
            try:
                logger.info(f"Processing {i+1}/{len(self.companies)}: {company['name']} - {company['url']}")
                
                # First, visit the main company page to get founders
                company_url = company['url']
                try:
                    logger.info(f"  Navigating to company page: {company_url}")
                    self.driver.get(company_url)
                    time.sleep(2)  # Wait for page load
                    
                    # Parse the company page
                    company_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Extract founders - handle multiple patterns
                    founders = []
                    logger.info("  Looking for founders on company page...")
                    
                    # Pattern 1: Section-based with "Active Founders" or "Former Founders"
                    founders_headings = company_soup.find_all(string=re.compile(r'(Active|Former)\s+Founders?', re.I))
                    
                    for founders_heading in founders_headings:
                        heading_text = founders_heading.strip()
                        logger.info(f"  Found {heading_text} section")
                        
                        # Find the parent container
                        founders_section = founders_heading.find_parent('section')
                        if not founders_section:
                            # Try finding parent div if section not found
                            founders_section = founders_heading.find_parent('div', class_=lambda x: x and 'relative' in str(x))
                        
                        if founders_section:
                            # Find all founder cards in this section
                            founder_cards = founders_section.find_all('div', class_='ycdc-card-new')
                            
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
                                    
                                    # Extract title - look for text-gray-600 or text-[15px]
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
                    
                    # Pattern 2: Simple "Founders" heading (e.g., in sidebar)
                    if not founders:
                        logger.info("  Trying alternative pattern: simple 'Founders' heading...")
                        simple_founders_div = company_soup.find('div', string=re.compile(r'^Founders?$', re.I))
                        
                        if simple_founders_div:
                            logger.info("  Found simple Founders section")
                            # Find the parent container and look for the next sibling with founder cards
                            parent = simple_founders_div.find_parent()
                            if parent:
                                # Look for space-y-4 div that contains the founder cards
                                cards_container = parent.find_next_sibling('div', class_=lambda x: x and 'space-y' in str(x))
                                if not cards_container:
                                    # Sometimes the cards are in the same parent
                                    cards_container = parent.find('div', class_=lambda x: x and 'space-y' in str(x))
                                
                                if cards_container:
                                    founder_cards = cards_container.find_all('div', class_='ycdc-card-new', recursive=False)
                                    
                                    for card in founder_cards:
                                        try:
                                            founder = {
                                                'name': '',
                                                'title': '',
                                                'linkedin': '',
                                                'twitter': ''
                                            }
                                            
                                            # Extract name
                                            name_div = card.find('div', class_=re.compile(r'(text-xl|text-lg).*font-bold'))
                                            if name_div:
                                                founder['name'] = name_div.get_text(strip=True)
                                            
                                            # Extract title
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
                    
                    company['founders'] = founders
                    logger.info(f"  Total founders found: {len(founders)}")
                    
                except Exception as e:
                    logger.warning(f"Error accessing company page for {company['name']}: {e}")
                    company['founders'] = []
                
                # Now navigate to the company's jobs page for other details
                jobs_url = f"{company['url']}/jobs"
                
                try:
                    logger.info(f"  Navigating to: {jobs_url}")
                    self.driver.get(jobs_url)
                    time.sleep(2)  # Wait for page load
                    
                    # Parse the jobs page
                    jobs_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Extract company details from the ycdc-card-new section
                    logger.info("  Extracting company details (founded year, team size, location)...")
                    
                    # Find the company info card with the details
                    info_card = jobs_soup.find('div', class_='ycdc-card-new')
                    if info_card:
                        # Find all flex-row divs that contain label-value pairs
                        detail_rows = info_card.find_all('div', class_=lambda x: x and 'flex' in x and 'flex-row' in x and 'justify-between' in x)
                        
                        for row in detail_rows:
                            spans = row.find_all('span')
                            if len(spans) >= 2:
                                label = spans[0].get_text(strip=True).lower()
                                value = spans[1].get_text(strip=True)
                                
                                if 'founded' in label:
                                    company['founded_year'] = value
                                    logger.info(f"  Founded: {value}")
                                elif 'team size' in label:
                                    company['team_size'] = value
                                    logger.info(f"  Team Size: {value}")
                                elif 'location' in label:
                                    company['location'] = value
                                    logger.info(f"  Location: {value}")
                                elif 'status' in label:
                                    company['status'] = value
                                    logger.info(f"  Status: {value}")
                                elif 'batch' in label:
                                    # Update batch if found on detail page
                                    if value and not company['batch']:
                                        company['batch'] = value
                                        logger.info(f"  Batch: {value}")
                    
                    # Extract company website from jobs page - look for the specific structure
                    website_container = jobs_soup.find('div', class_=lambda x: x and 'group' in str(x) and 'flex' in str(x))
                    if website_container:
                        website_link = website_container.find('a', href=lambda x: x and x.startswith('http') and 'ycombinator.com' not in x)
                        if website_link:
                            company['company_website'] = website_link.get('href', '')
                    
                    # Alternative: look for any external link with the website icon
                    if not company['company_website']:
                        all_external_links = jobs_soup.find_all('a', href=lambda x: x and x.startswith('http') and 'ycombinator.com' not in x)
                        for link in all_external_links:
                            # Check if it has the website icon (SVG)
                            if link.find('svg'):
                                company['company_website'] = link.get('href', '')
                                break
                    
                    # Extract jobs info from the jobs page
                    jobs = []
                    jobs_heading = jobs_soup.find(text=re.compile(r'Jobs at', re.I))
                    if jobs_heading:
                        jobs_section = jobs_heading.find_parent()
                        if jobs_section:
                            # Find the job listings container
                            jobs_container = jobs_section.find_next('div')
                            if jobs_container:
                                # Check if there are no jobs
                                no_jobs_text = jobs_container.find(text=re.compile(r'No jobs at.*are currently posted', re.I))
                                
                                if no_jobs_text:
                                    # No jobs available
                                    logger.info(f"  No jobs found for {company['name']}")
                                    jobs = []
                                else:
                                    # Find individual job entries
                                    job_rows = jobs_container.find_all('div', class_=lambda x: x and 'flex' in str(x) and 'py-4' in str(x))
                                    
                                    for job_row in job_rows:
                                        try:
                                            job = {
                                                'title': '',
                                                'description': ''
                                            }
                                        
                                            # Extract job title and URL
                                            title_link = job_row.find('a', href=lambda x: x and '/jobs/' in x)
                                            if title_link:
                                                job['title'] = title_link.get_text(strip=True)
                                                job_detail_url = f"https://www.ycombinator.com{title_link.get('href', '')}"
                                                
                                                # Navigate to job detail page to get description
                                                try:
                                                    logger.info(f"  Getting job details for: {job['title']}")
                                                    self.driver.get(job_detail_url)
                                                    time.sleep(2)  # Wait for job detail page to load
                                                
                                                    job_detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                                                    
                                                    # Extract job description starting from "About the role" section
                                                    about_role_heading = job_detail_soup.find('h2', class_='ycdc-section-title', string=re.compile(r'About the role', re.I))
                                                    if about_role_heading:
                                                        description_parts = []
                                                        
                                                        # Add the "About the role" heading
                                                        description_parts.append("About the role")
                                                        
                                                        # Get all content after "About the role" heading
                                                        current_element = about_role_heading.find_next_sibling()
                                                        
                                                        while current_element:
                                                            # If we hit another h2 section that's not "About [Company]", stop
                                                            if current_element.name == 'h2' and current_element.get('class') and 'ycdc-section-title' in current_element.get('class'):
                                                                # Check if it's "About [Company]" section
                                                                if re.search(r'About\s+', current_element.get_text(), re.I):
                                                                    # Add this section heading and continue
                                                                    description_parts.append('\n' + current_element.get_text(strip=True))
                                                                    current_element = current_element.find_next_sibling()
                                                                    continue
                                                                else:
                                                                    # Different section, stop here
                                                                    break
                                                            
                                                            # Extract text from this element preserving structure
                                                            if current_element.name:
                                                                # Get text with line breaks preserved
                                                                if current_element.name in ['p', 'div', 'section']:
                                                                    # For paragraphs and divs, get text with line breaks
                                                                    element_text = current_element.get_text(separator='\n', strip=True)
                                                                elif current_element.name in ['ul', 'ol']:
                                                                    # For lists, format items with bullets
                                                                    items = current_element.find_all('li')
                                                                    if items:
                                                                        list_text = []
                                                                        for item in items:
                                                                            list_text.append('• ' + item.get_text(strip=True))
                                                                        element_text = '\n'.join(list_text)
                                                                    else:
                                                                        element_text = current_element.get_text(separator='\n', strip=True)
                                                                elif current_element.name in ['h3', 'h4', 'h5', 'h6']:
                                                                    # For subheadings, add extra line break before
                                                                    element_text = '\n' + current_element.get_text(strip=True)
                                                                else:
                                                                    element_text = current_element.get_text(strip=True)
                                                                
                                                                if element_text:
                                                                    description_parts.append(element_text)
                                                            
                                                            current_element = current_element.find_next_sibling()
                                                        
                                                        # Join all parts with proper spacing
                                                        job['description'] = '\n\n'.join(description_parts)
                                                    
                                                    # If no "About the role" section, try alternative approach
                                                    if not job['description']:
                                                        # Look for any h2 with "About" in the text
                                                        about_headings = job_detail_soup.find_all('h2', string=re.compile(r'About', re.I))
                                                        if about_headings:
                                                            description_parts = []
                                                            for heading in about_headings:
                                                                description_parts.append(heading.get_text(strip=True))
                                                                # Get all content after this heading until next h2
                                                                current = heading.find_next_sibling()
                                                                section_content = []
                                                                while current and not (current.name == 'h2'):
                                                                    if current.name:
                                                                        text = current.get_text(separator='\n', strip=True)
                                                                        if text:
                                                                            section_content.append(text)
                                                                    current = current.find_next_sibling()
                                                                
                                                                if section_content:
                                                                    description_parts.append('\n'.join(section_content))
                                                            
                                                            job['description'] = '\n\n'.join(description_parts)
                                                    
                                                    # Don't remove formatting - just clean up extra blank lines
                                                    if job['description']:
                                                        # Remove multiple consecutive newlines but preserve single ones
                                                        lines = job['description'].split('\n')
                                                        cleaned_lines = []
                                                        for line in lines:
                                                            line = line.strip()
                                                            if line:  # Only add non-empty lines
                                                                cleaned_lines.append(line)
                                                        job['description'] = '\n'.join(cleaned_lines)
                                                    
                                                except Exception as e:
                                                    logger.warning(f"  Error getting job description for {job['title']}: {e}")
                                                    job['description'] = ''
                                            
                                            if job['title']:
                                                jobs.append(job)
                                                
                                        except Exception as e:
                                            logger.warning(f"Error extracting job info: {e}")
                                            continue
                    
                    # Assign the jobs list to the company
                    company['jobs'] = jobs
                    
                except Exception as e:
                    logger.warning(f"Error accessing jobs page for {company['name']}: {e}")
                    # Don't overwrite founders - they were already extracted from company page
                    company['jobs'] = []
                
                # Small delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error getting detailed info for {company.get('name', 'Unknown')}: {e}")
                # Set empty values for failed companies but continue processing
                # Note: founders may have been extracted already from company page
                if 'founders' not in company or not company['founders']:
                    company['founders'] = []
                if 'jobs' not in company:
                    company['jobs'] = []
                if 'company_website' not in company:
                    company['company_website'] = ''
                continue
        
        logger.info("✓ Finished getting detailed company information")
    
    def save_results(self):
        """Save results to JSON and CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_filename = f'yc_companies_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scrape_date': datetime.now().isoformat(),
                'total_companies': len(self.companies),
                'companies': self.companies
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved JSON: {json_filename}")
        
        # Save CSV - flatten the data for CSV format
        if self.companies:
            csv_filename = f'yc_companies_{timestamp}.csv'
            
            # Prepare flattened data for CSV
            csv_data = []
            for company in self.companies:
                # Create base row
                row = {
                    'name': company.get('name', ''),
                    'batch': company.get('batch', ''),
                    'founded_year': company.get('founded_year', ''),
                    'team_size': company.get('team_size', ''),
                    'status': company.get('status', ''),
                    'description': company.get('description', ''),
                    'location': company.get('location', ''),
                    'industry': ', '.join(company.get('industry', [])),
                    'url': company.get('url', ''),
                    'company_website': company.get('company_website', ''),
                    'founders_count': len(company.get('founders', [])),
                    'jobs_count': len(company.get('jobs', []))
                }
                
                # Add founder info (first founder for main CSV)
                founders = company.get('founders', [])
                if founders:
                    row['founder_name'] = founders[0].get('name', '')
                    row['founder_title'] = founders[0].get('title', '')
                    row['founder_linkedin'] = founders[0].get('linkedin', '')
                    row['founder_twitter'] = founders[0].get('twitter', '')
                else:
                    row['founder_name'] = ''
                    row['founder_title'] = ''
                    row['founder_linkedin'] = ''
                    row['founder_twitter'] = ''
                
                # Add job info (first job for main CSV)
                jobs = company.get('jobs', [])
                if jobs:
                    row['job_title'] = jobs[0].get('title', '')
                    row['job_description'] = jobs[0].get('description', '')[:500] + '...' if len(jobs[0].get('description', '')) > 500 else jobs[0].get('description', '')  # Truncate for CSV
                else:
                    row['job_title'] = ''
                    row['job_description'] = ''
                
                csv_data.append(row)
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'name', 'batch', 'founded_year', 'team_size', 'status', 'description', 'location', 
                    'industry', 'url', 'company_website',
                    'founders_count', 'founder_name', 'founder_title', 'founder_linkedin', 'founder_twitter',
                    'jobs_count', 'job_title', 'job_description'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            logger.info(f"✓ Saved CSV: {csv_filename}")
    
    def display_sample(self):
        """Display sample of scraped data"""
        if self.companies:
            logger.info("\n" + "="*60)
            logger.info("SAMPLE DATA (First 3 companies)")
            logger.info("="*60)
            
            for i, company in enumerate(self.companies[:3], 1):
                print(f"\n{i}. {company.get('name', 'N/A')}")
                print(f"   Batch: {company.get('batch', 'N/A')}")
                print(f"   Founded: {company.get('founded_year', 'N/A')}")
                print(f"   Team Size: {company.get('team_size', 'N/A')}")
                print(f"   Status: {company.get('status', 'N/A')}")
                print(f"   Location: {company.get('location', 'N/A')}")
                print(f"   Industry: {', '.join(company.get('industry', []))}")
                
                desc = company.get('description', 'N/A')
                if len(desc) > 80:
                    desc = desc[:80] + '...'
                print(f"   Description: {desc}")
                
                print(f"   Company Website: {company.get('company_website', 'N/A')}")
                print(f"   YC URL: {company.get('url', 'N/A')}")
                
                # Display founders
                founders = company.get('founders', [])
                if founders:
                    print(f"   Founders ({len(founders)}):")
                    for founder in founders[:2]:  # Show first 2 founders
                        print(f"     - {founder.get('name', 'N/A')} ({founder.get('title', 'N/A')})")
                        if founder.get('linkedin'):
                            print(f"       LinkedIn: {founder.get('linkedin')}")
                        if founder.get('twitter'):
                            print(f"       Twitter: {founder.get('twitter')}")
                else:
                    print(f"   Founders: None found")
                
                # Display jobs
                jobs = company.get('jobs', [])
                if jobs:
                    print(f"   Jobs ({len(jobs)}):")
                    for job in jobs[:2]:  # Show first 2 jobs
                        print(f"     - {job.get('title', 'N/A')}")
                        if job.get('description'):
                            desc = job.get('description', '')
                            if len(desc) > 150:
                                desc = desc[:150] + '...'
                            print(f"       Description: {desc}")
                else:
                    print(f"   Jobs: None found")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Browser closed")
    
    def scrape(self, url):
        """Main scraping method"""
        try:
            # Setup driver
            if not self.setup_driver():
                raise Exception("Failed to setup WebDriver")
            
            # Load page
            if not self.load_page(url):
                raise Exception("Failed to load page")
            
            # Scroll and load all companies
            total_companies = self.scroll_and_load_all()
            
            # Extract data
            self.extract_company_data()
            
            # Save results
            self.save_results()
            
            # Display sample
            self.display_sample()
            
            logger.info(f"\n✓ SCRAPING COMPLETE! Extracted {len(self.companies)} companies")
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            raise
        finally:
            self.close()


def main():
    """Main function"""
    url = "https://www.ycombinator.com/companies?batch=Fall%202025&batch=Summer%202025&batch=Spring%202025&batch=Winter%202025&batch=Fall%202024&batch=Winter%202024&batch=Summer%202024&query=openroll"
    
    # Configuration
    FETCH_DETAILED_INFO = True  # Set to False for faster scraping (no founders/jobs data)
    
    logger.info("Starting Y Combinator Companies Scraper (Enhanced Version)...")
    logger.info(f"Target URL: {url}")
    logger.info(f"Fetch detailed info (founders/jobs): {FETCH_DETAILED_INFO}")
    
    scraper = YCombinatorScraper()
    scraper.fetch_detailed_info = FETCH_DETAILED_INFO  # Pass config to scraper
    
    try:
        scraper.scrape(url)
    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"\nFatal error: {str(e)}")
        
        # Provide troubleshooting steps
        print("\n" + "="*60)
        print("TROUBLESHOOTING STEPS:")
        print("="*60)
        print("1. Make sure Chrome browser is installed")
        print("2. Close all Chrome windows and try again")
        print("3. Update Chrome to the latest version")
        print("4. Try running as administrator")
        print("5. Check if antivirus is blocking ChromeDriver")
        print("\nIf Chrome opens but doesn't navigate:")
        print("- Check your internet connection")
        print("- Try disabling VPN if you're using one")
        print("- Make sure the Y Combinator website is accessible")
        print("\nTo speed up scraping, set FETCH_DETAILED_INFO = False in main()")


if __name__ == "__main__":
    main()
