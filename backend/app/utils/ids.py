"""
UUID4 session ID helpers
"""
import uuid
from typing import Optional


def generate_session_id() -> str:
    """Generate a new UUID4 session ID"""
    return str(uuid.uuid4())


def get_session_id_from_request(
    query_param: Optional[str] = None,
    header_value: Optional[str] = None
) -> str:
    """
    Get session ID with fallback priority:
    1. Query parameter
    2. Header value
    3. Generate new UUID4
    """
    if query_param:
        return query_param
    if header_value:
        return header_value
    return generate_session_id()

