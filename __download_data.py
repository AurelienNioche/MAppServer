import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime
import shutil

from MAppServer.settings import SERVER_USER, SERVER_DOMAIN, DATA_FOLDER, DOWNLOAD_FOLDER, SERVER_LATEST_DUMP_RELATIVE_PATH


now = datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

print("Destination folder:", DOWNLOAD_FOLDER)

if os.path.exists(DOWNLOAD_FOLDER):
    shutil.rmtree(DOWNLOAD_FOLDER)

os.makedirs(DOWNLOAD_FOLDER)

# scp local_file user@remote_host:remote_file
out = os.system(f"rsync -r -h --info=progress2 --copy-links -e ssh {SERVER_USER}@{SERVER_DOMAIN}:{SERVER_LATEST_DUMP_RELATIVE_PATH} {DATA_FOLDER}")
if out == 0:
    print(f"Files successfully uploaded in `{DOWNLOAD_FOLDER}`.")
else:
    print("Error while uploading.")
