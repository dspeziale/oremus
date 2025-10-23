"""
Database Migration Script
Adds the missing 'santo_principale' column to the santi table
"""

import sqlite3
import os
from pathlib import Path


def backup_database(db_path: str):
    """Create a backup of the database before migration"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False

    backup_path = f"{db_path}.backup"
    try:
        with open(db_path, 'rb') as source:
            with open(backup_path, 'wb') as dest:
                dest.write(source.read())
        print(f"✅ Backup created at: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def add_santo_principale_column(db_path: str):
    """Add the santo_principale column to existing santi table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(santi);")
        columns = [col[1] for col in cursor.fetchall()]

        if 'santo_principale' in columns:
            print("✓ Column 'santo_principale' already exists")
            conn.close()
            return True

        # Add the column
        print("Adding 'santo_principale' column...")
        cursor.execute('ALTER TABLE santi ADD COLUMN santo_principale TEXT;')

        # Populate the column based on tipo = 'principale'
        print("Populating 'santo_principale' column...")
        cursor.execute('''
            UPDATE santi 
            SET santo_principale = nome_santo 
            WHERE tipo = 'principale'
        ''')

        conn.commit()
        print(f"✅ Updated {cursor.rowcount} rows")
        conn.close()
        return True

    except sqlite3.OperationalError as e:
        print(f"❌ Migration failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_schema(db_path: str):
    """Verify the schema after migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n📋 Current santi table schema:")
        print("-" * 50)

        cursor.execute("PRAGMA table_info(santi);")
        columns = cursor.fetchall()

        for col_id, col_name, col_type, not_null, default, pk in columns:
            nullable = "NOT NULL" if not_null else "NULL"
            print(f"  {col_name:20} {col_type:10} {nullable}")

        print("-" * 50)

        # Show sample data
        cursor.execute("SELECT COUNT(*) FROM santi;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total saints in database: {count}")

        if count > 0:
            print("\n📌 Sample data:")
            cursor.execute('''
                SELECT giorno, nome_santo, tipo, santo_principale 
                FROM santi 
                LIMIT 3
            ''')
            for row in cursor.fetchall():
                print(f"  {row}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def main():
    db_path = "instance/oremus.db"

    print("=" * 60)
    print("🔄 DATABASE MIGRATION SCRIPT")
    print("=" * 60)

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Please run your data import script first.")
        return False

    print(f"📁 Target database: {db_path}\n")

    # Backup database
    print("Step 1: Creating backup...")
    if not backup_database(db_path):
        print("❌ Failed to create backup. Migration aborted.")
        return False

    # Add column
    print("\nStep 2: Adding missing column...")
    if not add_santo_principale_column(db_path):
        print("❌ Migration failed. Your backup is at {db_path}.backup")
        return False

    # Verify
    print("\nStep 3: Verifying schema...")
    if not verify_schema(db_path):
        print("❌ Verification failed")
        return False

    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYour database has been updated and is ready to use.")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)