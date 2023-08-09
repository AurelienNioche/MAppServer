import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from datetime import datetime
import pytz

from MAppServer.settings import DATABASES

from MAppServer.settings \
    import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, TIME_ZONE
from user.models import User


def create_super_user():

    User.objects.create_superuser(username=f'{EMAIL_HOST_USER}',
                                  email=f'{EMAIL_HOST_USER}',
                                  password=f'{EMAIL_HOST_PASSWORD}',
                                  experiment="superuser",
                                  starting_date=datetime.now(tz=pytz.timezone(TIME_ZONE)),
                                  base_chest_amount=-1)
    print("Superuser created successfully.")


def delete_db():
    rsp = input("Are you sure you want to DELETE THE DATABASE if it exists? (Y/N)")
    if rsp.lower() in ('y', 'yes'):
        db_name = DATABASES['default']['NAME']
        os.system(f'dropdb {db_name}')
        os.system('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete')
        os.system('find . -path "*/migrations/*.pyc" -delete')
        print("If there is no error message, the database should have been deleted.")
    else:
        print("No database deleted.")


def create_db():

    db_name = DATABASES['default']['NAME']

    os.system(f"createdb {db_name} --owner postgres")
    os.system("python3 manage.py makemigrations")
    os.system("python3 manage.py makemigrations user")
    os.system("python3 manage.py migrate")


if __name__ == "__main__":
    delete_db()
    create_db()
    create_super_user()
