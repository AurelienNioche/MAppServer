import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import DATABASES


DB_NAME = DATABASES['default']['NAME']

os.system(f"createdb {DB_NAME} --owner postgres")
os.system("python3 manage.py makemigrations user user_progress")
os.system("python3 manage.py migrate")
