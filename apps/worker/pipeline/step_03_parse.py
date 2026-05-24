"""Pipeline step 03: Parse document."""

from typing import Any


def parse_document(local_path: str, **kwargs) -> dict:
    return {"text": "sample text", "success": True}