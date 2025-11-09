"""
Test script to verify industry tag extraction works correctly
Run this before running the full update_industries.py script
"""

import re
from bs4 import BeautifulSoup

# Sample HTML from YC company page (as provided by user)
SAMPLE_HTML = """
<div class="flex flex-row items-start gap-x-5 md:items-center">
    <div class="mt-2 h-16 w-16 shrink-0 rounded-xl md:mt-0 md:h-32 md:w-32">
        <img class="h-full w-full rounded-xl" src="https://bookface-images.s3.amazonaws.com/small_logos/fd2b15ce8a8e404c0ec54c33a17f938963c26455.png" alt="" style="filter: blur(0px);">
    </div>
    <div class="flex w-full flex-col space-y-1">
        <div class="my-0 flex w-full flex-wrap items-start justify-between gap-x-2 gap-y-1 md:flex-row md:items-center md:pr-4">
            <h1 class="my-0 text-2xl font-bold">Parse</h1>
        </div>
        <div class="my-0 hidden max-w-full md:block">
            <div class="mb-1 text-lg">Build an API to interact with any website in seconds. </div>
        </div>
        <div class="align-center my-0 flex flex-row flex-wrap gap-x-2 gap-y-2">
            <a target="_blank" href="/companies?batch=Fall 2025">
                <div class="yc-tw-Pill rounded-sm bg-[#E6E4DC] uppercase tracking-widest px-3 py-[3px] text-[12px] font-thin undefined flex flex-row items-center">
                    <div class="flex flex-row items-center gap-[6px]">
                        <svg viewBox="0 0 320 320" xmlns="http://www.w3.org/2000/svg" class="inline-block h-3 w-3 text-[#E36D34]" width="1.25em" height="1.25em">
                            <title>Y Combinator Logo</title>
                            <g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
                                <g>
                                    <polygon fill="#F05F22" points="0 320 320 320 320 0 0 0"></polygon>
                                    <polygon fill="#FFFFFF" points="173 175.8652 173 247.0002 146 247.0002 146 175.8652 77.086 73.0002 110 73.0002 159.628 148.9972 209 73.0002 241.914 73.0002"></polygon>
                                </g>
                            </g>
                        </svg>
                        <span>Fall 2025</span>
                    </div>
                </div>
            </a>
            <div class="yc-tw-Pill rounded-sm bg-[#E6E4DC] uppercase tracking-widest px-3 py-[3px] text-[12px] font-thin">
                <div class="flex flex-row items-center justify-between">
                    <div class="mr-[6px] h-3 w-3 rounded-full bg-green-500"></div>Active
                </div>
            </div>
            <a href="/companies/industry/developer-tools">
                <div class="yc-tw-Pill rounded-sm bg-[#E6E4DC] uppercase tracking-widest px-3 py-[3px] text-[12px] font-thin">developer-tools</div>
            </a>
            <a href="/companies/industry/api">
                <div class="yc-tw-Pill rounded-sm bg-[#E6E4DC] uppercase tracking-widest px-3 py-[3px] text-[12px] font-thin">api</div>
            </a>
            <a href="/companies/industry/big-data">
                <div class="yc-tw-Pill rounded-sm bg-[#E6E4DC] uppercase tracking-widest px-3 py-[3px] text-[12px] font-thin">big-data</div>
            </a>
        </div>
    </div>
</div>
"""

def test_industry_extraction():
    """Test the industry tag extraction logic"""
    print("="*70)
    print("TESTING INDUSTRY TAG EXTRACTION")
    print("="*70)
    print("\nParsing sample HTML...")
    
    soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
    
    # Extract industry tags using the same logic as update_industries.py
    industry_tags = []
    
    # Pattern 1: Links to /companies/industry/{tag}
    industry_links = soup.find_all('a', href=re.compile(r'^/companies/industry/'))
    
    print("\nFound industry links:")
    for link in industry_links:
        href = link.get('href', '')
        match = re.search(r'/companies/industry/(.+)$', href)
        if match:
            industry_tag = match.group(1)
            industry_tag = industry_tag.strip()
            if industry_tag and industry_tag not in industry_tags:
                industry_tags.append(industry_tag)
                print(f"  ✓ {industry_tag}")
    
    # Check what we're filtering out
    print("\nChecking excluded tags:")
    all_pills = soup.find_all('div', class_=re.compile(r'yc-tw-Pill'))
    
    for pill in all_pills:
        pill_text = pill.get_text(strip=True)
        
        # Check if it's a batch indicator
        if pill.find('svg') and 'Y Combinator Logo' in str(pill):
            print(f"  ✗ Excluded (batch): {pill_text}")
            continue
        
        # Check if it's a status indicator
        if pill.find('div', class_=re.compile(r'rounded-full.*bg-green|bg-red|bg-gray')):
            print(f"  ✗ Excluded (status): {pill_text}")
            continue
        
        # Check batch patterns
        if re.match(r'^(Winter|Spring|Summer|Fall)\s+\d{4}$', pill_text, re.I):
            print(f"  ✗ Excluded (batch pattern): {pill_text}")
            continue
        
        # Check status
        if pill_text.lower() in ['active', 'inactive', 'public', 'acquired']:
            print(f"  ✗ Excluded (status word): {pill_text}")
            continue
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"✓ Found {len(industry_tags)} valid industry tags:")
    for tag in industry_tags:
        print(f"  • {tag}")
    
    print("\nExpected tags: developer-tools, api, big-data")
    expected = ['developer-tools', 'api', 'big-data']
    
    if set(industry_tags) == set(expected):
        print("\n✓✓✓ TEST PASSED! ✓✓✓")
        print("The extraction logic is working correctly!")
        return True
    else:
        print("\n✗✗✗ TEST FAILED ✗✗✗")
        print(f"Expected: {expected}")
        print(f"Got: {industry_tags}")
        return False


def test_database_connection():
    """Test database connection"""
    import os
    from dotenv import load_dotenv
    
    print("\n" + "="*70)
    print("TESTING DATABASE CONNECTION")
    print("="*70)
    
    # Check .env file
    if not os.path.exists('.env'):
        print("\n✗ .env file not found!")
        print("Create a .env file with your PostgreSQL credentials.")
        print("See DATABASE_SETUP.md for details.")
        return False
    
    print("✓ .env file found")
    
    # Load environment variables
    load_dotenv()
    
    # Check required variables
    required_vars = ['POSTGRES_HOST', 'POSTGRES_DATABASE', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"\n✗ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✓ All required environment variables present")
    
    # Try to import psycopg2
    try:
        import psycopg2
        print("✓ psycopg2 imported successfully")
    except ImportError:
        print("\n✗ psycopg2 not installed!")
        print("Run: pip install psycopg2-binary")
        return False
    
    # Try to connect
    try:
        print("\nAttempting connection...")
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM companies")
        count = cursor.fetchone()[0]
        
        print(f"✓ Connected successfully!")
        print(f"✓ Found {count} companies in database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        return False


def test_selenium_setup():
    """Test Selenium setup"""
    print("\n" + "="*70)
    print("TESTING SELENIUM SETUP")
    print("="*70)
    
    # Try to import Selenium
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ Selenium and dependencies imported successfully")
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        print("Run: pip install selenium webdriver-manager")
        return False
    
    # Try to create a driver
    try:
        print("\nAttempting to create Chrome driver...")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✓ Chrome driver created successfully!")
        
        # Test navigation
        print("Testing navigation to Y Combinator...")
        driver.get("https://www.ycombinator.com")
        
        print(f"✓ Successfully loaded: {driver.title}")
        
        driver.quit()
        print("✓ Driver closed successfully")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Selenium setup failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure Chrome browser is installed")
        print("  2. Update Chrome to latest version")
        print("  3. Try: pip install --upgrade selenium webdriver-manager")
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*70)
    print("# INDUSTRY UPDATER - PRE-FLIGHT CHECKS")
    print("#"*70)
    
    results = {
        'HTML Parsing': False,
        'Database Connection': False,
        'Selenium Setup': False
    }
    
    # Test 1: HTML parsing
    results['HTML Parsing'] = test_industry_extraction()
    
    # Test 2: Database connection
    results['Database Connection'] = test_database_connection()
    
    # Test 3: Selenium setup
    results['Selenium Setup'] = test_selenium_setup()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to run update_industries.py")
        print("\nNext steps:")
        print("  1. Start with a test run:")
        print("     python update_industries.py --limit 5")
        print("\n  2. Then run for real:")
        print("     python update_industries.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running update_industries.py")
    
    print()


if __name__ == "__main__":
    main()

