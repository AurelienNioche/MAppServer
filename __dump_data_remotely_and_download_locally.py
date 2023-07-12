import os

from MAppServer.settings import SERVER_USER, SERVER_DOMAIN

out = os.system(f"cat __dump_data.py | ssh {SERVER_USER}@{SERVER_DOMAIN} python3 - ")
os.system("python3 __download_data.py")
