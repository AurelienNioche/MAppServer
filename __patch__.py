import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User, Reward, Status

u = User.objects.filter(username="242K").first()
if u is not None:
    print(f"I found user {u.username}")

else:
    print(f"I did not found user {u.username}")


u = User.objects.filter(username="2.80+E02").first()
if u is not None:
    print(f"I found user {u.username}")
    # u.username = "28E02..."

else:
    print(f"I did not found user {u.username}")

