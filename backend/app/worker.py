from celery import Celery
from app.core.config import get_settings
celery_app=Celery("videarn",broker=get_settings().redis_url,backend=get_settings().redis_url)
