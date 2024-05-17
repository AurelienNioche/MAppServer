import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from test.user_simulation import creation


def main():

    creation.create_test_user(
        challenge_accepted=False,
        starting_date="18/05/2024",
        username="sebastian",
        experiment_name="alpha-testing",
        first_challenge_offer="7:00",
    )


if __name__ == "__main__":
    main()

