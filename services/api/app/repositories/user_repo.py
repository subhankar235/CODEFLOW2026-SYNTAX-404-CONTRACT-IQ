"""User repository — database query functions for users."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User


async def create_user(
    session: AsyncSession,
    clerk_user_id: str,
    email: str,
    preferred_language: str = "en",
) -> User:
    """Create a new user."""
    user = User(
        clerk_user_id=clerk_user_id,
        email=email,
        preferred_language=preferred_language,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_clerk_id(
    session: AsyncSession, clerk_user_id: str
) -> Optional[User]:
    """Get user by Clerk user ID."""
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    return result.scalars().first()


async def update_user(
    session: AsyncSession,
    user_id: UUID,
    **kwargs,
) -> Optional[User]:
    """Update user fields."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    for key, value in kwargs.items():
        if hasattr(user, key) and key not in ("id", "created_at"):
            setattr(user, key, value)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: UUID) -> bool:
    """Delete a user."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return False

    await session.delete(user)
    await session.commit()
    return True


async def upsert_user(
    session: AsyncSession,
    clerk_user_id: str,
    email: str,
    **kwargs,
) -> User:
    """Upsert a user record based on Clerk user ID."""
    user = await get_user_by_clerk_id(session, clerk_user_id)
    if user:
        # Update existing user
        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ("id", "clerk_user_id", "created_at"):
                setattr(user, key, value)
        user.email = email  # Always update email if it changed
    else:
        # Create new user
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            **kwargs,
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user
