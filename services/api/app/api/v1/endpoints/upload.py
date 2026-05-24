import logging
import os
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import check_upload_limit
from app.core.security import get_current_user_id
from app.db.session import get_async_session
from app.models.analysis_result import AnalysisResult
from app.repositories import clause_repo, contract_repo, scan_job_repo
from app.schemas.contract import ContractCreate
from app.schemas.scan_job import ScanResponse, ScanStatus
from app.core.celery import celery_app
from app.services import contract_service

logger = logging.getLogger(__name__)

router = APIRouter()


def decrypt_content(encrypted_data: bytes, key_hex: str) -> bytes:
    """Decrypt AES-GCM encrypted content using the provided hex key."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import binascii
    
    print(f"[DECRYPT] Data length: {len(encrypted_data)}, Key: {key_hex[:20]}...")
    
    key = binascii.unhexlify(key_hex)
    
    # Extract IV (first 12 bytes for GCM)
    iv = encrypted_data[:12]
    # Rest is encrypted content (includes auth tag)
    encrypted_content = encrypted_data[12:]
    
    print(f"[DECRYPT] IV length: {len(iv)}, Content: {len(encrypted_content)}")
    
    # Decrypt with AESGCM
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, encrypted_content, None)
    
    print(f"[DECRYPT] Success, decrypted: {len(decrypted)} bytes")
    return decrypted


async def extract_text_from_url(file_url: str, encryption_key: str = None) -> str:
    """Download and extract text from uploaded file using real parsers."""
    import io
    import tempfile

    logger.info(f"Extracting text from: {file_url[:80]}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(file_url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download file: HTTP {response.status_code}")
        content = response.content

    # Save to a temp file for the parsers
    suffix = ".pdf" if file_url.lower().endswith(".pdf") else ".docx"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(content)

        # Try PDF parser from the AI service's pipeline
        try:
            from app.parser.pdf_parser import parse_pdf
            pdf_result = parse_pdf(tmp_path)
            if pdf_result.success and pdf_result.text and len(pdf_result.text.strip()) > 50:
                logger.info(f"PDF parsed: {len(pdf_result.text)} chars, {pdf_result.page_count} pages")
                if pdf_result.needs_ocr:
                    raise ValueError("PDF appears to be scanned (no extractable text)")
                return pdf_result.text
        except ImportError:
            # Fallback to pdfminer if the AI parser module isn't directly importable
            pass
        except Exception as e:
            logger.warning(f"PDF parser failed: {e}")
            # Continue to try other methods

        # Try DOCX parser
        try:
            from app.parser.docx_parser import parse_docx
            docx_result = parse_docx(tmp_path)
            if docx_result.success and docx_result.text and len(docx_result.text.strip()) > 50:
                logger.info(f"DOCX parsed: {len(docx_result.text)} chars")
                return docx_result.text
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"DOCX parser failed: {e}")

        # Try as plain text
        text = content.decode("utf-8", errors="ignore").strip()
        if len(text) > 50:
            logger.info(f"Plain text extracted: {len(text)} chars")
            return text

        raise ValueError(
            "Could not extract sufficient text from the uploaded file. "
            "Ensure the file is a readable PDF, DOCX, or text file."
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


async def analyze_with_ai(contract_text: str, contract_type: str) -> dict:
    """Call AI service to analyze contract using the real pipeline."""
    import logging
    logger = logging.getLogger(__name__)

    ai_url = settings.ai_service_url
    logger.info(f"Calling AI service at {ai_url}/api/v1/analyze")

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{ai_url}/api/v1/analyze",
            json={
                "contract_text": contract_text,
                "contract_type": contract_type,
            },
        )
        if response.status_code != 200:
            body = response.text[:500]
            raise ValueError(f"AI service returned HTTP {response.status_code}: {body}")

        result = response.json()
        logger.info(f"AI service returned {len(result.get('clauses', []))} clauses")
        return result


async def process_contract_real(
    db: AsyncSession,
    contract_id: str,
    file_url: str,
    encryption_key: str = None,
):
    """Process a contract using the real AI pipeline. No dummy fallbacks."""
    import logging
    from uuid import UUID

    logger = logging.getLogger(__name__)
    logger.info(f"Processing contract {contract_id}")

    # 1. Extract text from uploaded file using real parsers
    contract_text = await extract_text_from_url(file_url, encryption_key)
    if not contract_text or len(contract_text.strip()) < 50:
        raise ValueError("Extracted text is too short (<50 chars) for meaningful analysis")

    # 2. Call AI service
    analysis_result = await analyze_with_ai(contract_text, "general")

    # 3. Save clauses to database
    clauses_data = analysis_result.get("clauses", [])
    contract_uuid = UUID(contract_id)

    for cl in clauses_data:
        await clause_repo.create_clause(
            session=db,
            contract_id=contract_uuid,
            text=cl.get("text", ""),
            position_index=cl.get("position_index", 0),
            risk_level=cl.get("risk_level", "MEDIUM"),
            risk_category=cl.get("risk_category", "other"),
            plain_english=cl.get("plain_english", ""),
            worst_case_scenario=cl.get("worst_case", ""),
            financial_exposure=cl.get("financial_exposure"),
            negotiable=cl.get("negotiable", True),
            confidence=cl.get("confidence", 0.5),
        )

    # 4. Update scan job to complete
    jobs = await scan_job_repo.get_scan_jobs_by_contract_id(db, contract_uuid)
    if jobs:
        jobs[0].status = "complete"
        jobs[0].progress_pct = 100

    # 5. Create analysis result
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        contract_id=contract_uuid,
        overall_risk_score=analysis_result.get("overall_risk_score", 50),
        should_sign=analysis_result.get("should_sign", "review"),
        top_concerns=analysis_result.get("top_concerns", []),
        top_positives=analysis_result.get("top_positives", []),
        negotiating_power=analysis_result.get("negotiating_power", "Moderate"),
        power_score=analysis_result.get("power_score", 0),
        power_label=analysis_result.get("power_label", "Balanced"),
        leverage_points=analysis_result.get("leverage_points", []),
    )
    db.add(analysis)
    await db.commit()
    logger.info(f"Contract {contract_id} processed successfully ({len(clauses_data)} clauses)")


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Upload a contract - returns immediately.
    Processing happens in background or on scan page.
    """
    # Check rate limit
    await check_upload_limit(user_id)

    # Create contract and job
    (
        job_id,
        contract_id,
        scan_status,
        encryption_key,
    ) = await contract_service.create_contract_and_job(db, user_id, contract_data)

    # Look up internal user UUID for Celery tasks
    from app.repositories import user_repo
    db_user = await user_repo.get_user_by_clerk_id(db, user_id)
    internal_user_id = str(db_user.id) if db_user else user_id

    # Trigger blockchain registration in the background
    celery_app.send_task(
        "tasks.register_contract_on_chain",
        kwargs={
            "contract_id": str(contract_id),
            "file_url": contract_data.file_url,
            "user_id": user_id,
        },
    )

    # Trigger contract analysis in the background
    celery_app.send_task(
        "tasks.process_contract",
        kwargs={
            "contract_id_str": str(contract_id),
            "file_url": contract_data.file_url,
            "user_id": internal_user_id,
        },
    )

    # Return immediately — Celery worker processes the scan
    return ScanResponse(
        job_id=job_id, contract_id=contract_id, status=ScanStatus.PROCESSING, progress_pct=10.0
    )


@router.post("/process/{jobId}")
async def process_contract(
    jobId: str,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """Trigger contract processing (called from scan page)"""
    from uuid import UUID
    
    # Get job by jobId
    job = await scan_job_repo.get_scan_job_by_id(db, jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    contract = await contract_repo.get_contract_by_id(db, job.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Process contract using the real pipeline — no dummy fallbacks
    try:
        await process_contract_real(db, str(contract.id), str(contract.file_ref), None)
        job.status = "complete"
        job.progress_pct = 100
        await db.commit()
        return {"status": "complete"}
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        await db.commit()
        logger.exception(f"Contract processing failed for {contract.id}")
        raise HTTPException(status_code=500, detail=str(e))
