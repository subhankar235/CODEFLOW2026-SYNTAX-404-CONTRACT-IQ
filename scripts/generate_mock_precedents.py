import os
import json
import random
from pathlib import Path

BASE_DIR = Path("services/ai/data/precedents")
CATEGORIES = {
    "employment": ["non_compete", "termination", "severance"],
    "ip": ["ip_assignment", "work_for_hire"],
    "nda": ["confidentiality", "non_solicitation"],
    "vendor": ["indemnity", "limitation_of_liability", "auto_renewal", "payment"]
}

COURTS = ["Supreme Court of California", "Delaware Court of Chancery", "New York Court of Appeals", "9th Circuit Court of Appeals", "Texas Supreme Court"]

def generate_mock_precedents():
    count = 0
    for folder, clause_types in CATEGORIES.items():
        folder_path = BASE_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Generate 16 cases per folder to ensure at least 60 total
        for i in range(16):
            clause_type = random.choice(clause_types)
            case_name = f"Company {chr(65+random.randint(0,25))} vs Individual {random.randint(100, 999)}"
            year = random.randint(2010, 2024)
            jurisdiction = random.choice(COURTS)
            outcome_flag = random.choice(["enforced", "partially enforced", "struck down"])
            
            summary = f"In this case, the court reviewed a {clause_type} clause. The court {outcome_flag} the clause because it was deemed {'reasonable' if outcome_flag == 'enforced' else 'overly broad'}. This sets a strong precedent in {jurisdiction} regarding {clause_type.replace('_', ' ')}."
            
            data = {
                "case_name": case_name,
                "year": year,
                "jurisdiction": jurisdiction,
                "outcome": f"The clause was {outcome_flag}.",
                "summary": summary,
                "clause_type": clause_type
            }
            
            file_path = folder_path / f"case_{i+1:03d}.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            count += 1
            
    print(f"Successfully generated {count} mock precedent cases.")

if __name__ == "__main__":
    generate_mock_precedents()
