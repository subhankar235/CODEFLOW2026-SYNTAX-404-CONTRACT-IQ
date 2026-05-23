from celery_app import app


@app.task(bind=True)
def cleanup_expired_reports(self):
    pass
