"""
Quick script to test AWS PostgreSQL database connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import psycopg2
    print("✓ psycopg2 is installed")
except ImportError:
    print("✗ psycopg2 not installed")
    print("  Run: pip install psycopg2-binary")
    exit(1)

print("\nTesting database connection...")
print("="*60)

# Get credentials
host = os.getenv('POSTGRES_HOST')
port = os.getenv('POSTGRES_PORT', '5432')
database = os.getenv('POSTGRES_DATABASE')
user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')

# Check if .env exists
if not os.path.exists('.env'):
    print("✗ .env file not found!")
    print("\nPlease create a .env file with:")
    print("""
POSTGRES_HOST=your-db-endpoint.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DATABASE=yc_companies
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
    """)
    exit(1)

# Check if credentials are set
if not all([host, database, user, password]):
    print("✗ Missing database credentials in .env file")
    print("\nPlease ensure all variables are set:")
    print(f"  POSTGRES_HOST: {'✓' if host else '✗'}")
    print(f"  POSTGRES_PORT: {'✓' if port else '✗'}")
    print(f"  POSTGRES_DATABASE: {'✓' if database else '✗'}")
    print(f"  POSTGRES_USER: {'✓' if user else '✗'}")
    print(f"  POSTGRES_PASSWORD: {'✓' if password else '✗'}")
    exit(1)

print("Credentials found:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Database: {database}")
print(f"  User: {user}")
print(f"  Password: {'*' * len(password)}")

print("\nAttempting connection...")

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    print("✓ Successfully connected to database!")
    
    # Get database version
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\nDatabase version:")
    print(f"  {version}")
    
    # Check existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    if tables:
        print(f"\nExisting tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("\nNo tables found (this is OK for first-time setup)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ DATABASE CONNECTION TEST PASSED")
    print("="*60)
    print("\nYou can now run: python save_to_postgres.py")
    
except psycopg2.OperationalError as e:
    print(f"✗ Connection failed: {e}")
    print("\nPossible issues:")
    print("  1. Check your database endpoint is correct")
    print("  2. Verify your database is running")
    print("  3. Check security group allows your IP address")
    print("  4. Verify username and password are correct")
    
except Exception as e:
    print(f"✗ Error: {e}")


