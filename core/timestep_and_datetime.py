import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from datetime import datetime, time, timedelta
from pytz import timezone as tz

from MAppServer.settings import (
    TIME_ZONE,
    TIMESTEP,
    CHALLENGE_DURATION
)
from utils import logging
from utils.constants import SECONDS_IN_A_DAY


LOGGER = logging.get(__name__)


def get_datetime_from_timestep(t, now):
    """Get the datetime from a timestep index."""
    delta = timedelta(seconds=(t*SECONDS_IN_A_DAY/TIMESTEP.size))
    tm = (datetime.min + delta).time()
    return datetime.combine(now.date(), tm)


def get_timestep_from_datetime(dt):
    """Get the timestep index for a given datetime."""
    dt = dt.astimezone(tz(TIME_ZONE))
    timestep_duration = SECONDS_IN_A_DAY / TIMESTEP.size
    start_of_day = datetime.combine(dt, time.min, tzinfo=dt.tzinfo)
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def challenge_duration_to_n_timesteps():
    if len(TIMESTEP) != 24:
        raise NotImplementedError("Sorry mate")
    return CHALLENGE_DURATION
