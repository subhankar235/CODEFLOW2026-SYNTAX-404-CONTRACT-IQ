from celery_app import app


@app.task(bind=True)
def translate_results(self, contract_id: str, target_language: str):
    pass
