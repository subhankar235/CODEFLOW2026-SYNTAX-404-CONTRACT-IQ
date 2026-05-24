#!/usr/bin/env python
"""
Database verification script - Test connection and model imports.

Usage:
    cd services/api
    python -m scripts.verify_database
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.db.session import engine
from app.core.config import settings


async def verify_connection():
    """Verify database connection."""
    print("[*] Testing database connection...")
    try:
        async with engine.begin() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("[+] Database connection successful")
        return True
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return False


async def verify_pgvector():
    """Verify pgvector extension is installed."""
    print("\n[*] Checking pgvector extension...")
    try:
        async with engine.begin() as connection:
            result = await connection.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()
            if row:
                print("[+] pgvector extension is installed")
                return True
            else:
                print("[!] pgvector extension not installed (run migrations to install)")
                return False
    except Exception as e:
        print(f"[-] Error checking pgvector: {e}")
        return False


async def verify_tables():
    """Verify all tables exist."""
    print("\n[*] Checking database tables...")
    expected_tables = [
        "users",
        "contracts",
        "clauses",
        "scan_jobs",
        "analysis_results",
        "counter_offers",
        "precedent_matches",
        "reports",
        "embeddings",
    ]

    try:
        async with engine.begin() as connection:
            # Query the information_schema to check for tables
            result = await connection.execute(
                text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
            )
            existing_tables = [row[0] for row in result.fetchall()]

        missing_tables = [t for t in expected_tables if t not in existing_tables]

        if not missing_tables:
            print("[+] All 9 tables exist:")
            for table in expected_tables:
                print(f"   - {table}")
            return True
        else:
            print(f"[-] Missing {len(missing_tables)} tables:")
            for table in missing_tables:
                print(f"   - {table}")
            print("\nRun migrations to create tables:")
            print("  python -m scripts.run_migrations upgrade head")
            return False

    except Exception as e:
        print(f"[-] Error checking tables: {e}")
        return False


async def verify_models():
    """Verify all models can be imported."""
    print("\n[*] Verifying ORM models...")
    try:
        from app.models import (
            User,
            Contract,
            Clause,
            ScanJob,
            AnalysisResult,
            CounterOffer,
            PrecedentMatch,
            Report,
            Embedding,
        )

        models = [
            User,
            Contract,
            Clause,
            ScanJob,
            AnalysisResult,
            CounterOffer,
            PrecedentMatch,
            Report,
            Embedding,
        ]

        print("[+] All 9 models imported successfully:")
        for model in models:
            print(f"   - {model.__name__}")
        return True

    except ImportError as e:
        print(f"[-] Error importing models: {e}")
        return False


async def verify_repositories():
    """Verify all repositories can be imported."""
    print("\n[*] Verifying repositories...")
    try:
        from app.repositories import (
            create_user,
            create_contract,
            create_clause,
            create_scan_job,
            create_report,
            create_precedent_match,
        )

        print("[+] All repository functions imported successfully")
        return True

    except ImportError as e:
        print(f"[-] Error importing repositories: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("DATABASE VERIFICATION — Phase 1 Checklist")
    print("=" * 60)
    print(f"Database URL: {settings.database_url[:50]}...")
    print()

    results = []

    # Test connection
    results.append(("Connection", await verify_connection()))

    # Test pgvector
    results.append(("pgvector", await verify_pgvector()))

    # Test tables
    results.append(("Tables", await verify_tables()))

    # Test models
    results.append(("Models", await verify_models()))

    # Test repositories
    results.append(("Repositories", await verify_repositories()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name:.<40} {status}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n[OK] PHASE 1 -- Database Foundation: COMPLETE")
        print("\nNext steps:")
        print("  1. Migrations already applied!")
        print("  2. Proceed to PHASE 2 -- Authentication")
        return 0
    else:
        print(f"\n[!] {total - passed} check(s) failed. Please fix before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
