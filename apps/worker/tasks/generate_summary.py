from celery_app import app


@app.task(bind=True)
def generate_summary(self, contract_id: str):
    pass
