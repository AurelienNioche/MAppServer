import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.utils import timezone

from MAppServer.settings import SERVER_DATA_DIR, SERVER_USER, SERVER_DOMAIN, SERVER_BASE_DIR, LOCAL_DATA_BACKUP


now = timezone.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

# scp local_file user@remote_host:remote_file
out = os.system(f"scp -r {SERVER_USER}@{SERVER_DOMAIN}:{SERVER_BASE_DIR}/{SERVER_DATA_DIR} {LOCAL_DATA_BACKUP}_{now_str}")
if out == 0:
    print("File successfully uploaded.")
else:
    print("Error while uploading file.")
