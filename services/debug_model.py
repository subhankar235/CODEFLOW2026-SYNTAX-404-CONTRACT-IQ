import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

from ai.models.openrouter_client import OpenRouterClient

async def debug():
    client = OpenRouterClient()
    system_prompt = """You are a contract-classification assistant. 
Analyse the contract excerpt and respond ONLY with a JSON object (no markdown fences) with these keys:
  type        – one of: Employment, NDA, Service Agreement, Vendor, SaaS, Lease, Partnership, Loan, IP Assignment, Settlement, Unknown
  confidence  – float 0.0–1.0
  party_roles – array of short role strings (e.g. ['employer','employee'])
Be concise and accurate."""

    text = "This is an employment contract between ABC Corp and John Smith. The employee will work as a software engineer."

    result = await client.chat_json(
        system_prompt=system_prompt,
        user_prompt=text,
        model="google/gemini-2.0-flash-001"
    )
    print("Result:", result)
    await client.close()

asyncio.run(debug())