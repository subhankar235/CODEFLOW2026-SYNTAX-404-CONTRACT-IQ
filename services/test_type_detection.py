import os
import sys
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'services', 'ai'))

from ai.app.pipelines.type_detection import detect_contract_type, TypeDetectionResult

# Test 1: Employment contract
employment_text = """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into as of January 1, 2024, 
between ABC Corporation ("Employer") and John Smith ("Employee").

1. POSITION AND DUTIES
The Employee shall serve as a Software Engineer and shall perform such duties 
as may be assigned by the Employer from time to time.

2. COMPENSATION
The Employer shall pay the Employee a base salary of $100,000 per annum, 
payable in bi-weekly installments.

3. BENEFITS
The Employee shall be entitled to participate in all benefit programs offered 
to employees of the Employer, including health insurance, retirement plans, 
and paid time off.

4. TERMINATION
The Employer may terminate this Agreement at any time, with or without cause, 
upon written notice to the Employee.

5. CONFIDENTIALITY
The Employee agrees to keep confidential all proprietary information, trade secrets, 
and confidential business information of the Employer.

6. NON-COMPETE
During the term of employment and for a period of 12 months following termination, 
the Employee shall not engage in any business that competes with the Employer 
within a 50-mile radius.

7. NON-SOLICITATION
The Employee shall not solicit any employees or customers of the Employer for 
a period of 12 months following termination.
"""

print("=== TEST 1: Employment Contract ===")
result = detect_contract_type(employment_text)
print(f"Type: {result.type}")
print(f"Confidence: {result.confidence}")
print(f"Party Roles: {result.party_roles}")
print(f"Needs Manual Review: {result.needs_manual_review}")
print()

# Test 2: NDA contract
nda_text = """
MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual Non-Disclosure Agreement ("Agreement") is entered into as of 
January 1, 2024, between Company A and Company B.

1. PURPOSE
The parties wish to explore a potential business relationship regarding 
technology collaboration.

2. CONFIDENTIAL INFORMATION
"Confidential Information" means any information disclosed by either party 
that is marked as confidential or would reasonably be understood to be 
confidential in nature.

3. OBLIGATIONS
Each party agrees to: (a) hold the other party's Confidential Information 
in strict confidence; (b) not disclose to any third party; (c) use only 
for the purpose of evaluating the proposed business relationship.

4. TERM
This Agreement shall remain in effect for a period of 2 years from the 
date of execution.

5. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.
"""

print("=== TEST 2: NDA Contract ===")
result = detect_contract_type(nda_text)
print(f"Type: {result.type}")
print(f"Confidence: {result.confidence}")
print(f"Party Roles: {result.party_roles}")
print(f"Needs Manual Review: {result.needs_manual_review}")
print()

# Test 3: Ambiguous text
ambiguous_text = """
This document contains certain terms and conditions related to services 
and payment. The parties agree to work together on a project.
"""

print("=== TEST 3: Ambiguous Text ===")
result = detect_contract_type(ambiguous_text)
print(f"Type: {result.type}")
print(f"Confidence: {result.confidence}")
print(f"Party Roles: {result.party_roles}")
print(f"Needs Manual Review: {result.needs_manual_review}")