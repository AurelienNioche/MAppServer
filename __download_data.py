import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime

from MAppServer.settings import SERVER_USER, SERVER_DOMAIN, DOWNLOAD_FOLDER, LATEST_DUMP_FOLDER__RELATIVE


now = datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

print("Destination folder:", DOWNLOAD_FOLDER)

if os.path.exists(DOWNLOAD_FOLDER):
    os.rmdir(DOWNLOAD_FOLDER)

os.makedirs(DOWNLOAD_FOLDER)

# scp local_file user@remote_host:remote_file
out = os.system(f"scp -r {SERVER_USER}@{SERVER_DOMAIN}:{LATEST_DUMP_FOLDER__RELATIVE} {DOWNLOAD_FOLDER}")
if out == 0:
    print(f"Files successfully uploaded in `{DOWNLOAD_FOLDER}`.")
else:
    print("Error while uploading.")
