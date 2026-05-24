import os
import json
import random
from pathlib import Path

BASE_DIR = Path("services/ai/data/favorable_clauses")
CATEGORIES = {
    "indemnity": "indemnity",
    "ip_assignment": "ip",
    "non_compete": "employment",
    "auto_renewal": "vendor",
    "limitation_of_liability": "vendor"
}

def generate_favorable_clauses():
    count = 0
    for clause_type, contract_domain in CATEGORIES.items():
        folder_path = BASE_DIR / clause_type
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Generate 6 favorable clauses per type (30 total)
        for i in range(6):
            if clause_type == "indemnity":
                favorable_text = f"Party A shall only indemnify Party B for direct damages arising out of Party A's gross negligence or willful misconduct, capped at ${random.randint(1,5)}0,000."
            elif clause_type == "ip_assignment":
                favorable_text = f"The Employee retains all rights to any intellectual property developed entirely on their own time without using the Employer's equipment, supplies, facilities, or trade secret information."
            elif clause_type == "non_compete":
                favorable_text = f"This non-compete clause shall only be in effect for a period of {random.randint(3,6)} months and only applies within a {random.randint(5,15)}-mile radius of the employee's primary work location."
            elif clause_type == "auto_renewal":
                favorable_text = f"This Agreement shall not automatically renew. Either party must provide written notice of their intent to renew at least {random.choice([30, 45, 60])} days prior to expiration."
            else: # limitation_of_liability
                favorable_text = f"In no event shall either party's aggregate liability exceed the total amounts paid or payable by Customer in the {random.choice([6, 12, 24])} months preceding the claim."

            data = {
                "clause_type": clause_type,
                "favorable_text": favorable_text,
                "domain": contract_domain,
                "explanation": "This version shifts risk back to the drafting party by imposing reasonable caps or exclusions."
            }
            
            file_path = folder_path / f"clause_{i+1:03d}.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            count += 1
            
    print(f"Successfully generated {count} mock favorable clauses.")

if __name__ == "__main__":
    generate_favorable_clauses()
