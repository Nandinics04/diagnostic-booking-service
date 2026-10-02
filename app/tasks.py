from celery.utils.log import get_task_logger
from app.celery_app import celery_app

logger=get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3,  default_retry_delay=5)
def prepare_booking_confirmation(self, booking_id: int)->None:
    try:
        logger.info("confirmation_task booking_id=%s", booking_id)
    except Exception as exc:
        raise self.retry(exc=exc)
            