import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime

from MAppServer.settings import SERVER_DATA_DIR, SERVER_USER, SERVER_DOMAIN, SERVER_BASE_DIR, LOCAL_DATA_BACKUP, LATEST_DUMP_FOLDER


now = datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

destination_folder = f"{LOCAL_DATA_BACKUP}/download"
print("Destination folder:", destination_folder)

if os.path.exists(destination_folder):
    os.remove(destination_folder)

os.makedirs(destination_folder)

# scp local_file user@remote_host:remote_file
out = os.system(f"scp -r {SERVER_USER}@{SERVER_DOMAIN}:{SERVER_BASE_DIR}/{LATEST_DUMP_FOLDER} {destination_folder}")
if out == 0:
    print(f"Files successfully uploaded in `{destination_folder}`.")
else:
    print("Error while uploading.")
