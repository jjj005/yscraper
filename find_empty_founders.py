"""
Script to find companies with empty founders array in JSON files
"""

import json
import os
from datetime import datetime

def find_companies_with_empty_founders(json_file):
    """Find companies with empty founders array"""
    print(f"\nAnalyzing: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        companies = data.get('companies', [])
        empty_founders = []
        
        for company in companies:
            founders = company.get('founders', [])
            if not founders or len(founders) == 0:
                empty_founders.append({
                    'name': company.get('name', 'Unknown'),
                    'url': company.get('url', ''),
                    'batch': company.get('batch', ''),
                    'founded_year': company.get('founded_year', '')
                })
        
        print(f"  Total companies: {len(companies)}")
        print(f"  Companies with empty founders: {len(empty_founders)}")
        
        return empty_founders
    
    except Exception as e:
        print(f"  Error reading file: {e}")
        return []

def main():
    """Main function"""
    # Find all JSON files in current directory
    json_files = [f for f in os.listdir('.') if f.startswith('yc_companies_') and f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found!")
        return
    
    print(f"Found {len(json_files)} JSON file(s)")
    
    all_empty_founders = []
    
    for json_file in json_files:
        empty_founders = find_companies_with_empty_founders(json_file)
        all_empty_founders.extend(empty_founders)
    
    # Remove duplicates based on URL
    unique_companies = {}
    for company in all_empty_founders:
        url = company['url']
        if url not in unique_companies:
            unique_companies[url] = company
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total unique companies with empty founders: {len(unique_companies)}")
    
    # Save to a file for reprocessing
    output_file = 'companies_to_reprocess.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'count': len(unique_companies),
            'companies': list(unique_companies.values())
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved list to: {output_file}")
    
    # Display first 10 companies
    if unique_companies:
        print(f"\nFirst 10 companies to reprocess:")
        for i, company in enumerate(list(unique_companies.values())[:10], 1):
            print(f"  {i}. {company['name']} ({company['batch']})")
            print(f"     URL: {company['url']}")

if __name__ == "__main__":
    main()

