import os

from MAppServer.settings import USER_CREATION_CSV_PATH, SERVER_USER, SERVER_DOMAIN, SERVER_BASE_DIR
from utils import logging

logger = logging.get(__name__)

# scp local_file user@remote_host:remote_file
out = os.system(f"scp {USER_CREATION_CSV_PATH}/* {SERVER_USER}@{SERVER_DOMAIN}:{SERVER_BASE_DIR}/{USER_CREATION_CSV_PATH}")
if out == 0:
    logger.info("Files successfully uploaded.")
else:
    logger.info("Error while uploading files.")
