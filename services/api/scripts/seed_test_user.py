"""Seed script to create a test user for development."""
import asyncio
import uuid
from app.db.session import AsyncSessionLocal
from app.repositories import user_repo


async def seed_test_user(clerk_user_id: str = None, email: str = None):
    """Create a test user in the database."""
    clerk_id = clerk_user_id or "test_user_123"
    user_email = email or "test@example.com"
    
    async with AsyncSessionLocal() as session:
        existing = await user_repo.get_user_by_clerk_id(session, clerk_id)
        if existing:
            print(f"User already exists: {existing.email}")
            return existing
            
        user = await user_repo.create_user(
            session=session,
            clerk_user_id=clerk_id,
            email=user_email,
        )
        print(f"Created test user: {user.email} (ID: {user.id})")
        return user


if __name__ == "__main__":
    import sys
    clerk_id = sys.argv[1] if len(sys.argv) > 1 else None
    email = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(seed_test_user(clerk_id, email))