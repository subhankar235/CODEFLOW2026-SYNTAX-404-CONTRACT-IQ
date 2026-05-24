import httpx
import asyncio
import json
import hmac
import hashlib
import time

API_URL = "http://localhost:8000/api/v1"
WEBHOOK_SECRET = "whsec_dGVzdF9zZWNyZXRfdGVzdF9zZWNyZXRfdGVzdF9zZWNyZXR0"  # Match .env

async def test_auth_401():
    print("Testing 401 for unauthorized access...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/contracts/", headers={"Authorization": "Bearer invalidtoken"})
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            assert response.status_code == 401
        except Exception as e:
            print(f"Error: {e}")

async def test_webhook_simulated():
    print("\nTesting simulated user.created webhook...")
    
    payload = {
        "type": "user.created",
        "data": {
            "id": "user_2test123",
            "email_addresses": [
                {
                    "email_address": "test@example.com",
                    "id": "email_123"
                }
            ],
            "primary_email_address_id": "email_123"
        }
    }
    
    payload_str = json.dumps(payload)
    timestamp = str(int(time.time()))
    svix_id = f"msg_{timestamp}"
    
    # Simple svix-like signature generation (for testing purposes, svix uses hmac-sha256)
    # The actual svix library will verify this, so we need to match how it's signed
    to_sign = f"{svix_id}.{timestamp}.{payload_str}".encode("utf-8")
    secret_bytes = WEBHOOK_SECRET.encode("utf-8")
    if WEBHOOK_SECRET.startswith("whsec_"):
        import base64
        secret_bytes = base64.b64decode(WEBHOOK_SECRET[6:])
    
    signature = hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
    svix_signature = f"v1,{base64.b64encode(signature).decode('utf-8')}" if 'base64' in locals() else f"v1,{signature.hex()}"

    headers = {
        "svix-id": svix_id,
        "svix-timestamp": timestamp,
        "svix-signature": svix_signature,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/webhooks/clerk", content=payload_str, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Note: Server must be running for this to work
    asyncio.run(test_auth_401())
    asyncio.run(test_webhook_simulated())
