import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User, Reward, Status

username = "242K"
u = User.objects.filter(username=username).first()
if u is not None:
    print(f"I found user {u.username}")

else:
    print(f"I did not found user {username}")


username = "2.80E+02"
u = User.objects.filter(username=username).first()
if u is not None:
    print(f"I found user {username}")
    u.username = "28E1"
    u.save()

else:
    print(f"I did not found user {username}")

