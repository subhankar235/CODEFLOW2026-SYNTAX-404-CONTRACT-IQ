from celery_app import app


@app.task(bind=True)
def generate_report(self, contract_id: str, report_id: str):
    pass
