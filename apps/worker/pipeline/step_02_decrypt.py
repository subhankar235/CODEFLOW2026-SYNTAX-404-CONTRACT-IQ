"""Pipeline step 02: Decrypt file."""

from typing import Any


def decrypt_file(local_path: str, **kwargs) -> dict:
    return {"decrypted_path": local_path, "success": True}