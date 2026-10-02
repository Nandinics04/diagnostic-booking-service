import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app= Celery(
    "eve",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    imports=("app.tasks",),
)
