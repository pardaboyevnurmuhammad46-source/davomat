import os
from celery import Celery

# Django settings moduli 'davomat.settings' ekanligini ko'rsatamiz
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'davomat.settings')

app = Celery('davomat')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()