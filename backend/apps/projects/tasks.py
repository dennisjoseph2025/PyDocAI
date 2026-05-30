from config.celery import app


@app.task
def example_task():
    pass
