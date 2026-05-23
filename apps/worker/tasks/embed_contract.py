from celery_app import app


@app.task(bind=True)
def embed_contract(self, contract_id: str):
    pass
