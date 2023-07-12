import os

from MAppServer.settings import SERVER_USER, SERVER_DOMAIN

print("Dumping data remotely...")
os.system(f"cat __dump_data.py | ssh {SERVER_USER}@{SERVER_DOMAIN} python3 - ")
print("*" * 80)
print("Downloading data locally...")
os.system("python3 __download_data.py")

