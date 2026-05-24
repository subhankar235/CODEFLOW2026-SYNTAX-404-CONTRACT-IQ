"""Seed script to create test scan data for development."""
import asyncio
import uuid
from datetime import datetime
from app.db.session import AsyncSessionLocal
from app.repositories import user_repo, contract_repo, clause_repo, scan_job_repo
from app.models.analysis_result import AnalysisResult


async def seed_scan_data(clerk_user_id: str = None, filename: str = "sample_contract.pdf"):
    """Create a test contract with clauses and analysis results."""
    clerk_id = clerk_user_id or "test_user_123"
    
    async with AsyncSessionLocal() as session:
        # Get or create user
        user = await user_repo.get_user_by_clerk_id(session, clerk_id)
        if not user:
            user = await user_repo.create_user(
                session=session,
                clerk_user_id=clerk_id,
                email="test@example.com",
            )
        
        # Create contract
        contract = await contract_repo.create_contract(
            session=session,
            user_id=user.id,
            file_ref="https://example.com/sample.pdf",
            original_filename=filename,
            file_type="pdf",
            detected_language="en",
        )
        
        # Create clauses
        sample_clauses = [
            {
                "text": "The party shall not compete with the Company within a 50-mile radius for a period of 2 years after termination.",
                "position_index": 0,
                "risk_level": "HIGH",
                "risk_category": "non_compete",
                "plain_english": "You cannot work for a competitor for 2 years within 50 miles after leaving.",
                "worst_case_scenario": "You may be unable to find employment in your field for 2 years",
                "financial_exposure": "Loss of income potential: $200,000+",
                "negotiable": True,
                "confidence": 0.85,
            },
            {
                "text": "All intellectual property created during the term of this agreement shall be the sole property of the Company.",
                "position_index": 1,
                "risk_level": "MEDIUM",
                "risk_category": "ip_assignment",
                "plain_english": "Any work you create belongs to the company, not you.",
                "worst_case_scenario": "You lose rights to any inventions or creative work done during employment",
                "financial_exposure": "Potential lost royalties: Unknown",
                "negotiable": True,
                "confidence": 0.92,
            },
            {
                "text": "The Company may terminate this agreement at any time without notice or cause.",
                "position_index": 2,
                "risk_level": "HIGH",
                "risk_category": "termination",
                "plain_english": "The company can fire you anytime without warning.",
                "worst_case_scenario": "You could be let go immediately with no recourse",
                "financial_exposure": "Immediate loss of income",
                "negotiable": False,
                "confidence": 0.95,
            },
            {
                "text": "This agreement shall be governed by the laws of the State of Delaware.",
                "position_index": 3,
                "risk_level": "SAFE",
                "risk_category": "governing_law",
                "plain_english": "Delaware law applies to this contract.",
                "worst_case_scenario": "Standard legal provision, low risk",
                "financial_exposure": None,
                "negotiable": True,
                "confidence": 0.98,
            },
            {
                "text": "Payment shall be made within 30 days of invoice submission.",
                "position_index": 4,
                "risk_level": "LOW",
                "risk_category": "payment",
                "plain_english": "You get paid within 30 days after sending an invoice.",
                "worst_case_scenario": "Standard payment terms",
                "financial_exposure": None,
                "negotiable": True,
                "confidence": 0.90,
            },
        ]
        
        for cl in sample_clauses:
            await clause_repo.create_clause(
                session=session,
                contract_id=contract.id,
                **cl
            )
        
        # Create scan job as complete
        scan_job = await scan_job_repo.create_scan_job(
            session=session,
            contract_id=contract.id,
            status="complete",
            progress_pct=100.0,
        )
        
        # Create analysis result
        analysis = AnalysisResult(
            contract_id=contract.id,
            overall_risk_score=72,
            should_sign="yes_with_changes",
            top_concerns=[
                "Broad non-compete clause restricts future employment",
                "Company can terminate without notice",
                "Full IP assignment of all work product"
            ],
            top_positives=[
                "Standard payment terms at 30 days",
                "Clear governing law provision",
                "Negotiable terms on IP and non-compete"
            ],
            negotiating_power="Weak",
            power_score=45,
            power_label="Favors Counterparty",
            leverage_points=[
                "Request narrower geographic scope for non-compete",
                "Add notice period for termination",
                "Negotiate co-ownership of IP"
            ]
        )
        session.add(analysis)
        
        await session.commit()
        
        print(f"Created contract: {contract.id}")
        print(f"Created {len(sample_clauses)} clauses")
        print(f"Created scan job: {scan_job.id}")
        print(f"Created analysis result")
        return contract.id, scan_job.id


if __name__ == "__main__":
    import sys
    clerk_id = sys.argv[1] if len(sys.argv) > 1 else None
    filename = sys.argv[2] if len(sys.argv) > 2 else "sample_contract.pdf"
    contract_id, job_id = asyncio.run(seed_scan_data(clerk_id, filename))
    print(f"\nTo test, navigate to: /scan/{job_id}")