import httpx
import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# Base directory for temporary files
TEMP_DIR = (
    Path("/tmp/legaltech")
    if os.name != "nt"
    else Path(os.environ.get("TEMP", "C:\\temp")) / "legaltech"
)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

IV_SIZE = 12  # 96-bit IV for AES-GCM


async def download_file(file_url: str) -> str:
    """
    Download a file from a URL and save it to a temporary location.
    Returns the absolute path to the temporary file.
    """
    temp_filename = f"{uuid.uuid4()}.tmp"
    temp_path = TEMP_DIR / temp_filename

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Downloading file from {file_url}")
            response = await client.get(file_url, follow_redirects=True)
            response.raise_for_status()

            with open(temp_path, "wb") as f:
                f.write(response.content)

            logger.info(f"File saved to {temp_path}")
            return str(temp_path.absolute())
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise Exception(f"File download failed: {str(e)}")


def cleanup_file(file_path: str):
    """
    Delete a temporary file.
    """
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            logger.info(f"Cleaned up file {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")


def _hex_to_bytes(hex_key: str) -> bytes:
    """
    Convert hex string to bytes (256-bit AES key).
    """
    return bytes.fromhex(hex_key)


async def decrypt_file(file_path: str, decryption_key: Optional[str] = None) -> str:
    """
    Decrypt an AES-256-GCM encrypted file.

    The encrypted file format is:
    [12 bytes IV][encrypted data]

    Args:
        file_path: Path to the encrypted file
        decryption_key: Hex-encoded decryption key from the frontend

    Returns:
        Path to the decrypted file
    """
    if not decryption_key:
        logger.warning("No decryption key provided, returning encrypted file")
        return file_path

    try:
        logger.info(f"Decrypting file {file_path}")

        # Read encrypted data
        with open(file_path, "rb") as f:
            encrypted_data = f.read()

        if len(encrypted_data) < IV_SIZE:
            raise ValueError("Encrypted file too small - missing IV")

        # Extract IV (first 12 bytes) and ciphertext
        iv = encrypted_data[:IV_SIZE]
        ciphertext = encrypted_data[IV_SIZE:]

        # Convert hex key to bytes
        key = _hex_to_bytes(decryption_key)

        # Decrypt using AES-GCM
        aesgcm = AESGCM(key)
        decrypted_data = aesgcm.decrypt(iv, ciphertext, None)

        # Create decrypted file path
        original_path = Path(file_path)
        decrypted_path = (
            original_path.parent
            / f"{original_path.stem}_decrypted{original_path.suffix}"
        )

        # Write decrypted data
        with open(decrypted_path, "wb") as f:
            f.write(decrypted_data)

        logger.info(f"File decrypted successfully to {decrypted_path}")

        # Clean up the encrypted temp file
        cleanup_file(file_path)

        return str(decrypted_path)

    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise Exception(f"File decryption failed: {str(e)}")
