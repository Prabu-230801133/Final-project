"""
setup_db.py — Run this script AFTER configuring your .env file.
It creates the MySQL database and runs all Django migrations.

Usage:
  python setup_db.py

Prerequisites:
  1. MySQL Server running
  2. .env file configured with DB_USER and DB_PASSWORD
"""
import os
import sys
import subprocess
from decouple import config


def setup():
    db_name = config('DB_NAME', default='college_db')
    db_user = config('DB_USER', default='root')
    db_pass = config('DB_PASSWORD', default='')
    db_host = config('DB_HOST', default='localhost')
    db_port = config('DB_PORT', default='3306')

    mysql_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

    print(f"🔧 Setting up MySQL database: {db_name}")
    print(f"   Host: {db_host}:{db_port}, User: {db_user}")

    # Create the database
    create_cmd = [
        mysql_path,
        f"-u{db_user}",
    ]
    if db_pass:
        create_cmd.append(f"-p{db_pass}")

    create_cmd += [
        "-e",
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    ]

    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create database: {result.stderr}")
        print("   Please create the database manually in MySQL Workbench.")
    else:
        print(f"✅ Database '{db_name}' ready.")

    # Run migrations
    print("\n🔄 Running Django migrations...")
    migrate = subprocess.run(
        [sys.executable, "manage.py", "migrate"],
        capture_output=False
    )

    if migrate.returncode == 0:
        print("\n✅ Migrations complete!")

        # Run seed data
        print("\n🌱 Loading seed data...")
        subprocess.run([sys.executable, "seed_data.py"])
    else:
        print("\n❌ Migration failed. Check your .env database credentials.")


if __name__ == '__main__':
    setup()
