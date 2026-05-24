import asyncio
import os
from celery.utils.log import get_task_logger

from celery_app import app
from app.db.session import SessionLocal
from app.repositories import report_repo

logger = get_task_logger(__name__)

@app.task(name="cleanup_expired_reports")
def cleanup_expired_reports_task():
    """
    Celery Beat task to clean up expired reports and delete their PDF files.
    """
    return asyncio.run(process_cleanup())

async def process_cleanup():
    """Async logic for cleaning up expired reports."""
    async with SessionLocal() as db:
        try:
            # 1. Fetch expired reports before deleting them from DB
            from datetime import datetime, timezone
            from sqlalchemy import select
            from app.models.report import Report
            
            now = datetime.now(timezone.utc)
            query = select(Report).where(Report.share_expires_at <= now)
            result = await db.execute(query)
            expired_reports = result.scalars().all()
            
            if not expired_reports:
                logger.info("No expired reports found for cleanup.")
                return 0

            count = 0
            for report in expired_reports:
                # 2. Delete the PDF file from disk
                if report.file_path and os.path.exists(report.file_path):
                    try:
                        os.remove(report.file_path)
                        logger.info(f"Deleted PDF file: {report.file_path}")
                    except Exception as fe:
                        logger.warning(f"Could not delete PDF file {report.file_path}: {str(fe)}")
                
                # 3. Delete the DB record
                await db.delete(report)
                count += 1

            # 4. Commit changes
            await db.commit()
            logger.info(f"Cleaned up {count} expired reports.")
            return count

        except Exception as e:
            logger.error(f"Error during expired reports cleanup: {str(e)}")
            return 0
