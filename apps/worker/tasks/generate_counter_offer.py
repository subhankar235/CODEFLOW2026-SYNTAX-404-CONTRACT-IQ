from celery_app import app


@app.task(bind=True)
def generate_counter_offer(self, clause_id: str):
    pass
