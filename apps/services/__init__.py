"""Dummy streaming service."""


async def publish_clause(job_id: str, data: dict):
    pass


async def publish_complete(job_id: str, data: dict):
    pass


async def publish_error(job_id: str, error: str):
    pass


async def publish_progress(job_id: str, pct: int):
    pass