import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from test_user__create import test_user_xp_like__create


if __name__ == "__main__":
    experiment_name = "alpha-test-3"
    test_user_xp_like__create(username="mich-alph3", seed=123, experiment_name=experiment_name)
    # test_user_xp_like__create(username="stuA-alph2", seed=1234, experiment_name=experiment_name)
    # test_user_xp_like__create(username="stuB-alph2", seed=12345, experiment_name=experiment_name)

