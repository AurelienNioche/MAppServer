import os

from MAppServer.settings import USER_CREATION_CSV_PATH, SERVER_USER, SERVER_DOMAIN, SERVER_BASE_DIR

# scp local_file user@remote_host:remote_file
out = os.system(f"scp -r {USER_CREATION_CSV_PATH} {SERVER_USER}@{SERVER_DOMAIN}:{SERVER_BASE_DIR}/{USER_CREATION_CSV_PATH}")
if out == 0:
    print("Files successfully uploaded.")
else:
    print("Error while uploading files.")
