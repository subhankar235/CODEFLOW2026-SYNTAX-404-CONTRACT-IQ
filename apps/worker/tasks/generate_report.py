import asyncio
import os
from uuid import UUID
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from celery_app import app
from app.db.session import SessionLocal
from app.models.contract import Contract
from app.models.clause import Clause
from app.models.analysis_result import AnalysisResult
from app.models.report import Report
from app.utils.pdf_generator import generate_contract_report
from app.repositories import report_repo

logger = get_task_logger(__name__)

@app.task(name="generate_report")
def generate_report_task(contract_id_str: str, report_id_str: str, language: str = "en"):
    """
    Celery task to generate a PDF report.
    """
    contract_id = UUID(contract_id_str)
    report_id = UUID(report_id_str)
    
    # Run the async logic in a sync wrapper for Celery
    return asyncio.run(process_report_generation(contract_id, report_id, language))

async def process_report_generation(contract_id: UUID, report_id: UUID, language: str):
    """Async logic for report generation."""
    async with SessionLocal() as db:
        try:
            # 1. Fetch all data
            # Use joinedload to get analysis_result and clauses in one go if possible
            query = (
                select(Contract)
                .options(
                    joinedload(Contract.analysis_result),
                    joinedload(Contract.clauses).joinedload(Clause.precedent_matches),
                    joinedload(Contract.clauses).joinedload(Clause.counter_offers)
                )
                .where(Contract.id == contract_id)
            )
            result = await db.execute(query)
            contract = result.scalars().first()
            
            if not contract:
                logger.error(f"Contract {contract_id} not found for report generation")
                return False

            # 2. Prepare data structure for PDF generator
            # We need to transform the DB models into the dictionary format expected by pdf_generator
            report_data = {
                "contract_id": str(contract.id),
                "original_filename": contract.original_filename,
                "contract_type": contract.contract_type,
                "detected_language": contract.detected_language,
                "user_name": "User", # We should ideally fetch the user name too
                "summary": {
                    "risk_score": contract.analysis_result.overall_risk_score if contract.analysis_result else 0,
                    "risk_level": "LOW", # Logic to determine level based on score could be here
                    "should_sign": contract.analysis_result.should_sign if contract.analysis_result else "Unknown",
                    "top_concerns": contract.analysis_result.top_concerns if contract.analysis_result else [],
                    "top_positives": contract.analysis_result.top_positives if contract.analysis_result else [],
                },
                "clauses": [
                    {
                        "text": cl.text,
                        "risk_level": cl.risk_level,
                        "risk_category": cl.risk_category,
                        "plain_english": cl.plain_english,
                        "worst_case_scenario": cl.worst_case_scenario,
                        "recommendation": cl.plain_english, # Or specific recommendation field if added
                    }
                    for cl in contract.clauses
                ],
                "power": {
                    "score": 50, # Placeholder or fetch from analysis result
                    "label": "Balanced",
                    "key_imbalances": [],
                    "leverage_points": []
                },
                "precedents": [
                    {
                        "case_name": m.case_name,
                        "year": m.case_year,
                        "jurisdiction": m.jurisdiction,
                        "outcome": m.outcome,
                        "precedent_summary": m.outcome,
                        "enforcement_likelihood": m.enforcement_likelihood
                    }
                    for cl in contract.clauses for m in cl.precedent_matches
                ],
                "counter_offers": [
                    {
                        "risk_category": cl.risk_category,
                        "conservative": {"clause_text": co.conservative_version, "explanation": "Safer option"},
                        "balanced": {"clause_text": co.balanced_version, "explanation": "Fair option"},
                        "aggressive": {"clause_text": co.aggressive_version, "explanation": "Protective option"}
                    }
                    for cl in contract.clauses for co in cl.counter_offers
                ]
            }

            # Determine risk level label
            score = report_data["summary"]["risk_score"]
            if score >= 70: report_data["summary"]["risk_level"] = "HIGH"
            elif score >= 40: report_data["summary"]["risk_level"] = "MEDIUM"
            elif score >= 10: report_data["summary"]["risk_level"] = "LOW"
            else: report_data["summary"]["risk_level"] = "SAFE"

            # 3. Generate PDF
            pdf_path = await generate_contract_report(report_data, language)
            
            # 4. Update report record
            report = await report_repo.get_report_by_id(db, report_id)
            if report:
                report.file_path = pdf_path
                await db.commit()
                logger.info(f"Report generated successfully: {pdf_path}")
                return True
            else:
                logger.error(f"Report record {report_id} not found after generation")
                return False

        except Exception as e:
            logger.error(f"Error generating report for contract {contract_id}: {str(e)}")
            return False
