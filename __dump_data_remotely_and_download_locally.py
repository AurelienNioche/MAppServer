import os

from MAppServer.settings import SERVER_USER, SERVER_DOMAIN, SERVER_BASE_DIR

out = os.system(f"cat __dump_data.py | ssh {SERVER_USER}@{SERVER_DOMAIN} python3 - ")
print(out)
# os.system("python3 __download_data.py")