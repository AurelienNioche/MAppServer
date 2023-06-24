import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import DATABASES


def create_db():

    db_name = DATABASES['default']['NAME']

    os.system(f"createdb {db_name} --owner postgres")
    os.system("python3 manage.py makemigrations")
    os.system("python3 manage.py makemigrations user")
    os.system("python3 manage.py migrate")


if __name__ == "__main__":

    create_db()
