import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import DATABASES


DB_NAME = DATABASES['default']['NAME']

os.system(f"sudo -u postgres createdb {DB_NAME} --owner postgres")
os.system("python3 manage.py makemigrations")
os.system("python3 manage.py migrate")
