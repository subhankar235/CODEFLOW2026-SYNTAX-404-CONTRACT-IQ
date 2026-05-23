from celery_app import app


@app.task(bind=True)
def process_contract(self, contract_id: str, file_url: str):
    pass
