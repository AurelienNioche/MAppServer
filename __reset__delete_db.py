import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import DATABASES


DB_NAME = DATABASES['default']['NAME']


def delete_db():
    rsp = input("Are you sure you want to DELETE THE DATABASE? (Y/N)")
    if rsp.lower() in ('y', 'yes'):
        os.system(f'dropdb {DB_NAME}')
        os.system('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete')
        os.system('find . -path "*/migrations/*.pyc" -delete')
        print("If there is no error message, the database should have been deleted.")
    else:
        print("No database deleted.")


if __name__ == "__main__":
    delete_db()
