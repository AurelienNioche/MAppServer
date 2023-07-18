import os
from celery import shared_task

@shared_task
def update_beliefs():
    # This is a background task
    os.makedirs('tmp', exist_ok=True)
    print("hello from the background task")
