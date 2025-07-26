import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_counter.settings')

celery_app = Celery('blog_counter')

celery_app.config_from_object('django.conf:settings', namespace='CELERY')

