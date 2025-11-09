# PostgreSQL Database Setup Guide

## Overview

This guide helps you save Y Combinator companies data to an AWS PostgreSQL database.

## Prerequisites

1. **AWS RDS PostgreSQL Instance**
   - Create an RDS PostgreSQL instance in AWS
   - Note down the endpoint, port, database name, username, and password
   - Ensure your IP is whitelisted in the security group

2. **Install Required Package**
   ```bash
   pip install psycopg2-binary
   ```
   
   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Database Schema

The script creates three tables:

### 1. `companies` table
- `id` (SERIAL PRIMARY KEY)
- `url` (VARCHAR, UNIQUE) - YC company URL
- `name` (VARCHAR) - Company name
- `description` (TEXT) - Company description
- `batch` (VARCHAR) - YC batch (e.g., "W24", "S21")
- `location` (VARCHAR) - Company location
- `founded_year` (VARCHAR) - Year founded
- `team_size` (VARCHAR) - Team size
- `status` (VARCHAR) - Company status (Active/Inactive)
- `company_website` (VARCHAR) - Company website URL
- `industry` (TEXT[]) - Array of industry tags
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### 2. `founders` table
- `id` (SERIAL PRIMARY KEY)
- `company_id` (INTEGER) - Foreign key to companies
- `name` (VARCHAR) - Founder name
- `title` (VARCHAR) - Founder title/role
- `linkedin` (VARCHAR) - LinkedIn URL
- `twitter` (VARCHAR) - Twitter/X URL
- `created_at` (TIMESTAMP)

### 3. `jobs` table
- `id` (SERIAL PRIMARY KEY)
- `company_id` (INTEGER) - Foreign key to companies
- `title` (VARCHAR) - Job title
- `description` (TEXT) - Job description
- `created_at` (TIMESTAMP)

## Setup Instructions

### Step 1: Configure Database Credentials

Create a `.env` file in your project root with your AWS PostgreSQL credentials:

```bash
POSTGRES_HOST=your-db-endpoint.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DATABASE=yc_companies
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

**Note:** A template is provided in `env_template.txt`

### Step 2: Run the Script

```bash
python save_to_postgres.py
```

### Step 3: Select Files to Load

The script will show you all available JSON files:
```
Available files:
  1. yc_companies_20251013_042409.json
  2. yc_companies_20251013_085852.json
  3. yc_companies_20251013_105334.json
  4. yc_companies_reprocessed_20251020_140000.json
  5. Load ALL files

Enter choice (1-5):
```

Choose a file number or select the last option to load all files.

## Features

### ✅ Automatic Table Creation
- Creates all necessary tables on first run
- Creates indexes for better query performance
- No manual SQL setup required

### ✅ Upsert Logic
- Updates existing companies if they already exist (based on URL)
- Prevents duplicate entries
- Keeps data fresh

### ✅ Relational Data
- Properly links founders and jobs to companies
- Maintains referential integrity with foreign keys
- CASCADE delete (if company is deleted, founders and jobs are too)

### ✅ Batch Processing
- Commits every 10 companies for better performance
- Continues on error (logs and skips problematic records)

### ✅ Statistics
- Shows database statistics after loading:
  - Total companies
  - Total founders
  - Total jobs
  - Companies by batch
  - Companies with/without founders

## Example Output

```
============================================================
Y Combinator Data -> PostgreSQL
============================================================
INFO:__main__:psycopg2 imported successfully
INFO:__main__:Connecting to PostgreSQL database...
INFO:__main__:Successfully connected to database
INFO:__main__:Creating tables...
INFO:__main__:Tables created successfully

Found 3 JSON file(s)

Available files:
  1. yc_companies_20251013_042409.json
  2. yc_companies_20251013_085852.json
  3. yc_companies_20251013_105334.json
  4. Load ALL files

Enter choice (1-4): 4

Loading: yc_companies_20251013_042409.json
Found 420 companies
  Processed 10/420 companies...
  Processed 20/420 companies...
  ...
Completed: 420 companies inserted/updated, 0 errors

Database Statistics:
============================================================
Total companies: 1920
Total founders: 3840
Total jobs: 520

Companies by batch:
  W24: 450
  S24: 380
  W25: 290
  ...

Companies with founders: 1873
Companies without founders: 47

============================================================
SUMMARY
============================================================
Files processed: 3
Companies inserted/updated: 1920
Errors: 0
============================================================
```

## Querying the Data

Once data is loaded, you can query it using SQL:

### Get all companies in a specific batch
```sql
SELECT name, location, founded_year, status
FROM companies
WHERE batch = 'W24'
ORDER BY name;
```

### Get companies with their founders
```sql
SELECT c.name, c.batch, f.name as founder_name, f.title
FROM companies c
LEFT JOIN founders f ON c.id = f.company_id
WHERE c.batch = 'W24'
ORDER BY c.name, f.name;
```

### Get companies with most founders
```sql
SELECT c.name, c.batch, COUNT(f.id) as founder_count
FROM companies c
LEFT JOIN founders f ON c.id = f.company_id
GROUP BY c.id, c.name, c.batch
ORDER BY founder_count DESC
LIMIT 10;
```

### Get active companies with job openings
```sql
SELECT c.name, c.location, COUNT(j.id) as job_count
FROM companies c
INNER JOIN jobs j ON c.id = j.company_id
WHERE c.status = 'Active'
GROUP BY c.id, c.name, c.location
ORDER BY job_count DESC;
```

### Search by industry
```sql
SELECT name, batch, location, industry
FROM companies
WHERE 'Healthcare' = ANY(industry)
ORDER BY batch DESC;
```

## Troubleshooting

### Connection Issues
- **Problem:** "Failed to connect to database"
- **Solutions:**
  - Check your `.env` file credentials
  - Verify your AWS RDS instance is running
  - Check security group rules allow your IP
  - Ensure the database endpoint is correct

### SSL/TLS Issues
If you get SSL errors, you might need to adjust the connection:
```python
# In save_to_postgres.py, modify the connect() method:
self.conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    database=os.getenv('POSTGRES_DATABASE'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    sslmode='require'  # Add this line
)
```

### Permission Issues
- Make sure your database user has CREATE TABLE permissions
- For existing databases, user needs INSERT, UPDATE, DELETE permissions

## Security Notes

⚠️ **Important Security Practices:**

1. **Never commit .env file** - Already in .gitignore
2. **Use strong passwords** for database access
3. **Restrict database access** - Only allow specific IPs in security group
4. **Use IAM authentication** (optional but recommended for AWS RDS)
5. **Rotate credentials regularly**

## Next Steps

After loading data, you can:
1. Connect to the database using tools like pgAdmin, DBeaver, or DataGrip
2. Build dashboards using Metabase, Grafana, or similar
3. Create API endpoints to serve this data
4. Run analytics and generate reports
5. Export data to other formats (CSV, Excel, etc.)

## Maintenance

### Update existing data
Just run the script again with the same or newer JSON files. The upsert logic will:
- Update changed records
- Add new records
- Keep existing records

### Backup database
```bash
pg_dump -h your-endpoint.rds.amazonaws.com -U your_user -d yc_companies > backup.sql
```

### Restore database
```bash
psql -h your-endpoint.rds.amazonaws.com -U your_user -d yc_companies < backup.sql
```

