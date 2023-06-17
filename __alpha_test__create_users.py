import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from test_user__create import test_user_xp_like__create


if __name__ == "__main__":
    test_user_xp_like__create(username="michele", seed=123)
    test_user_xp_like__create(username="studentA", seed=1234)
    test_user_xp_like__create(username="studentB", seed=12345)

