import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from test.user_simulation import creation
from MAppServer.settings import (
    TEST_USERNAME, TEST_EXPERIMENT_NAME, TEST_FIRST_CHALLENGE_OFFER,
    TEST_STARTING_DATE
)


def main():

    creation.create_test_user(
        challenge_accepted=False,
        starting_date=TEST_STARTING_DATE,
        username=TEST_USERNAME,
        experiment_name=TEST_EXPERIMENT_NAME,
        first_challenge_offer=TEST_FIRST_CHALLENGE_OFFER,
    )


if __name__ == "__main__":
    main()

