import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from MAppServer.settings import DATABASES

from __init__create_db import create_db
from __init__create_super_user import create_super_user


def delete_db():
    rsp = input("Are you sure you want to DELETE THE DATABASE? (Y/N)")
    if rsp.lower() in ('y', 'yes'):
        db_name = DATABASES['default']['NAME']
        os.system(f'dropdb {db_name}')
        os.system('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete')
        os.system('find . -path "*/migrations/*.pyc" -delete')
        print("If there is no error message, the database should have been deleted.")
    else:
        print("No database deleted.")


if __name__ == "__main__":
    delete_db()
    create_db()
    create_super_user()
