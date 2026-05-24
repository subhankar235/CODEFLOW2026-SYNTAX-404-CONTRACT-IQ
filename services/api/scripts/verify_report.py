import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.pdf_generator import generate_contract_report

async def verify():
    print("Verifying PDF Report Generation...")
    
    # Dummy data
    contract_data = {
        "contract_id": "test-uuid-123",
        "original_filename": "Test_Contract.pdf",
        "contract_type": "Service Agreement",
        "detected_language": "en",
        "user_name": "John Doe",
        "summary": {
            "risk_score": 45,
            "risk_level": "MEDIUM",
            "should_sign": "Proceed with caution",
            "top_concerns": ["Indemnity clause is too broad", "Termination period is short"],
            "top_positives": ["Clear payment terms", "Standard confidentiality"]
        },
        "clauses": [
            {
                "text": "The provider shall indemnify the client for all losses...",
                "risk_level": "HIGH",
                "risk_category": "Indemnity",
                "plain_english": "You pay for everything if something goes wrong.",
                "worst_case_scenario": "Unlimited financial liability.",
                "recommendation": "Cap the indemnity to the contract value."
            }
        ],
        "power": {
            "score": 65,
            "label": "Provider Biased",
            "key_imbalances": [{"clause": "Indemnity", "why": "One-sided protection"}],
            "leverage_points": ["Request mutual indemnity"]
        }
    }

    try:
        pdf_path = await generate_contract_report(contract_data, "en")
        print(f"Success! PDF generated at: {pdf_path}")
        
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print(f"File exists and is non-zero: {os.path.getsize(pdf_path)} bytes")
        else:
            print("Error: Generated file is empty or missing!")
            
    except Exception as e:
        print(f"Verification failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify())
