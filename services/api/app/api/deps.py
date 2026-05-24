"""API dependencies — exports authentication and database session getters."""

from app.db.session import get_async_session
from app.core.security import get_current_user_id

get_db = get_async_session
get_current_user = get_current_user_id
