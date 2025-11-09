"""
Script to save Y Combinator companies data to AWS PostgreSQL database
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import psycopg2
try:
    import psycopg2
    from psycopg2.extras import execute_batch
    logger.info("psycopg2 imported successfully")
except ImportError:
    logger.error("psycopg2 not installed. Please run: pip install psycopg2-binary")
    exit(1)

# Load environment variables
load_dotenv()


class PostgresDataLoader:
    def __init__(self):
        """Initialize the database loader"""
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            logger.info("Connecting to PostgreSQL database...")
            
            # Get connection parameters from environment variables
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DATABASE'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        logger.info("Creating tables...")
        
        try:
            # Companies table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    url VARCHAR(500) UNIQUE NOT NULL,
                    name VARCHAR(500),
                    description TEXT,
                    batch VARCHAR(50),
                    location VARCHAR(200),
                    founded_year VARCHAR(10),
                    team_size VARCHAR(50),
                    status VARCHAR(50),
                    company_website VARCHAR(500),
                    industry TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Founders table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS founders (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                    name VARCHAR(300),
                    title VARCHAR(200),
                    linkedin VARCHAR(500),
                    twitter VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, name)
                )
            """)
            
            # Jobs table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                    title VARCHAR(500),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, title)
                )
            """)
            
            # Create indexes for better performance
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_companies_url ON companies(url)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_companies_batch ON companies(batch)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_founders_company_id ON founders(company_id)
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id)
            """)
            
            self.conn.commit()
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()
            raise
    
    def insert_company(self, company_data):
        """Insert or update a company and its related data"""
        try:
            # Insert or update company
            self.cursor.execute("""
                INSERT INTO companies (
                    url, name, description, batch, location, founded_year,
                    team_size, status, company_website, industry, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (url) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    batch = EXCLUDED.batch,
                    location = EXCLUDED.location,
                    founded_year = EXCLUDED.founded_year,
                    team_size = EXCLUDED.team_size,
                    status = EXCLUDED.status,
                    company_website = EXCLUDED.company_website,
                    industry = EXCLUDED.industry,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                company_data.get('url'),
                company_data.get('name'),
                company_data.get('description'),
                company_data.get('batch'),
                company_data.get('location'),
                company_data.get('founded_year'),
                company_data.get('team_size'),
                company_data.get('status'),
                company_data.get('company_website'),
                company_data.get('industry', [])
            ))
            
            company_id = self.cursor.fetchone()[0]
            
            # Delete existing founders and jobs (we'll re-insert them)
            self.cursor.execute("DELETE FROM founders WHERE company_id = %s", (company_id,))
            self.cursor.execute("DELETE FROM jobs WHERE company_id = %s", (company_id,))
            
            # Insert founders
            founders = company_data.get('founders', [])
            if founders:
                founder_data = [
                    (
                        company_id,
                        founder.get('name'),
                        founder.get('title'),
                        founder.get('linkedin'),
                        founder.get('twitter')
                    )
                    for founder in founders
                ]
                
                execute_batch(self.cursor, """
                    INSERT INTO founders (company_id, name, title, linkedin, twitter)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (company_id, name) DO NOTHING
                """, founder_data)
            
            # Insert jobs
            jobs = company_data.get('jobs', [])
            if jobs:
                job_data = [
                    (
                        company_id,
                        job.get('title'),
                        job.get('description')
                    )
                    for job in jobs
                ]
                
                execute_batch(self.cursor, """
                    INSERT INTO jobs (company_id, title, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (company_id, title) DO NOTHING
                """, job_data)
            
            return company_id
            
        except Exception as e:
            logger.error(f"Error inserting company {company_data.get('name')}: {e}")
            raise
    
    def load_json_file(self, json_file):
        """Load companies from a JSON file into the database"""
        logger.info(f"\nLoading: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            companies = data.get('companies', [])
            logger.info(f"Found {len(companies)} companies")
            
            inserted_count = 0
            error_count = 0
            
            for i, company in enumerate(companies, 1):
                try:
                    company_id = self.insert_company(company)
                    inserted_count += 1
                    
                    if i % 10 == 0:
                        logger.info(f"  Processed {i}/{len(companies)} companies...")
                        self.conn.commit()  # Commit every 10 companies
                    
                except Exception as e:
                    logger.error(f"  Error processing company {i}: {e}")
                    error_count += 1
                    self.conn.rollback()
                    continue
            
            # Final commit
            self.conn.commit()
            
            logger.info(f"Completed: {inserted_count} companies inserted/updated, {error_count} errors")
            return inserted_count, error_count
            
        except Exception as e:
            logger.error(f"Error loading file {json_file}: {e}")
            return 0, 0
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            logger.info("\nDatabase Statistics:")
            logger.info("="*60)
            
            # Total companies
            self.cursor.execute("SELECT COUNT(*) FROM companies")
            total_companies = self.cursor.fetchone()[0]
            logger.info(f"Total companies: {total_companies}")
            
            # Total founders
            self.cursor.execute("SELECT COUNT(*) FROM founders")
            total_founders = self.cursor.fetchone()[0]
            logger.info(f"Total founders: {total_founders}")
            
            # Total jobs
            self.cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = self.cursor.fetchone()[0]
            logger.info(f"Total jobs: {total_jobs}")
            
            # Companies by batch
            self.cursor.execute("""
                SELECT batch, COUNT(*) as count 
                FROM companies 
                WHERE batch IS NOT NULL AND batch != ''
                GROUP BY batch 
                ORDER BY batch DESC
            """)
            
            logger.info("\nCompanies by batch:")
            for row in self.cursor.fetchall():
                logger.info(f"  {row[0]}: {row[1]}")
            
            # Companies with founders
            self.cursor.execute("""
                SELECT COUNT(DISTINCT company_id) FROM founders
            """)
            companies_with_founders = self.cursor.fetchone()[0]
            logger.info(f"\nCompanies with founders: {companies_with_founders}")
            
            # Companies without founders
            companies_without_founders = total_companies - companies_with_founders
            logger.info(f"Companies without founders: {companies_without_founders}")
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("\nDatabase connection closed")


def main():
    """Main function"""
    logger.info("="*60)
    logger.info("Y Combinator Data -> PostgreSQL")
    logger.info("="*60)
    
    # Check for .env file
    if not os.path.exists('.env'):
        logger.error("\n.env file not found!")
        logger.error("Please create a .env file with the following variables:")
        logger.error("""
POSTGRES_HOST=your-db-endpoint.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
        """)
        return
    
    # Initialize loader
    loader = PostgresDataLoader()
    
    try:
        # Connect to database
        if not loader.connect():
            logger.error("Failed to connect to database")
            return
        
        # Create tables
        loader.create_tables()
        
        # Find all JSON files
        json_files = [f for f in os.listdir('.') if f.startswith('yc_companies_') and f.endswith('.json')]
        
        if not json_files:
            logger.warning("No JSON files found!")
            return
        
        logger.info(f"\nFound {len(json_files)} JSON file(s)")
        
        # Ask user which files to load
        print("\nAvailable files:")
        for i, file in enumerate(json_files, 1):
            print(f"  {i}. {file}")
        
        print(f"  {len(json_files) + 1}. Load ALL files")
        
        choice = input(f"\nEnter choice (1-{len(json_files) + 1}): ").strip()
        
        files_to_load = []
        if choice.isdigit():
            choice_num = int(choice)
            if choice_num == len(json_files) + 1:
                files_to_load = json_files
            elif 1 <= choice_num <= len(json_files):
                files_to_load = [json_files[choice_num - 1]]
        
        if not files_to_load:
            logger.error("Invalid choice")
            return
        
        # Load selected files
        total_inserted = 0
        total_errors = 0
        
        for json_file in files_to_load:
            inserted, errors = loader.load_json_file(json_file)
            total_inserted += inserted
            total_errors += errors
        
        # Show statistics
        loader.get_statistics()
        
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Files processed: {len(files_to_load)}")
        logger.info(f"Companies inserted/updated: {total_inserted}")
        logger.info(f"Errors: {total_errors}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        loader.close()


if __name__ == "__main__":
    main()

