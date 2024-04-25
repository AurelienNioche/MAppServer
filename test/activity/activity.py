import os

import \
    pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import numpy as np
from scipy import stats
from datetime import datetime, time, timedelta
from pytz import timezone as tz

from user.models import User


SECONDS_IN_DAY = 86400


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def convert_timesteps_into_activity_level(
        step_events: list,
        timestep: np.ndarray
) -> np.ndarray:
    """
    Convert the timesteps into activity level
    by computing the "derivative of the cumulative steps"
    (sounds weird but it is what it is, given the discretization of the data)
    (if you're not happpy with that, you can go back to the continuous world
     and enjoy the gradient of the cumulative steps)
    """
    deriv_cum_steps = np.zeros((len(step_events), timestep.size))
    for idx_day, step_events_day in enumerate(step_events):
        cum_steps_day = np.sum(step_events_day <= timestep[:, None], axis=1)
        deriv_cum_steps_day = np.gradient(cum_steps_day, timestep+1)
        deriv_cum_steps_day /= timestep.size-1
        deriv_cum_steps[idx_day] = deriv_cum_steps_day
    return deriv_cum_steps


def build_pseudo_count_matrix(
        actions: np.ndarray,
        activity: np.ndarray,
        timestep: np.ndarray,
        velocity: np.ndarray,
        jitter: float,
        dt_min: datetime = None,
        dt_max: datetime = None,
        n_action: int = 2,
) -> np.ndarray:

    """
    Compute the alpha matrix (pseudo-counts) for the transition matrix
    """
    # Initialize the pseudo-count matrix
    alpha_atvv = np.zeros((n_action, timestep.size-1, velocity.size, velocity.size))
    alpha_atvv += jitter
    # Return the pseudo-count matrix if there is no activity
    if activity.size == 0:
        return alpha_atvv
    # Extract the minimum and maximum timestamps in seconds (period where the data was collected)
    dt_min_sec = dt_min.timestamp() if dt_min is not None else 0
    dt_max_sec = dt_max.timestamp() if dt_max is not None else SECONDS_IN_DAY
    sec_per_timestep = SECONDS_IN_DAY / timestep.size
    # Add one bin for infinity
    bins = np.concatenate((velocity, np.full(1, np.inf)))
    # Clip the activity to the bins
    drv = np.clip(activity, bins[0], bins[-1])
    v_indexes = np.digitize(drv, bins, right=False) - 1
    # Initialize the time counter
    dt = dt_min_sec if dt_min is not None else 0
    # Loop over the days
    for day in range(activity.shape[0]):
        # Loop over the timesteps
        for t_idx in range(timestep.size - 1):
            # If the timestamp is outside the range
            # skip (just increment the time)
            if ((dt_min_sec is not None and dt < dt_min_sec)
                    or (dt_max_sec is not None and dt > dt_max_sec)):
                # just increment the time...
                dt += sec_per_timestep
                # ...and skip
                continue
            # Increment the pseudo-count matrix
            a_idx = actions[day, t_idx]
            v_idx = v_indexes[day, t_idx]
            v_idx_next = v_indexes[day, t_idx + 1]
            alpha_atvv[a_idx, t_idx, v_idx, v_idx_next] += 1
            dt += sec_per_timestep
    # Return the pseudo-count matrix
    return alpha_atvv


def build_position_transition_matrix(
        position: np.ndarray,
        velocity: np.ndarray,
        sigma_transition_position: float = 1e-3
) -> np.ndarray:
    # Compute position transition matrix
    tr = np.zeros((position.size, velocity.size, position.size))
    for p_idx, p in enumerate(position):
        for v_idx, v in enumerate(velocity):
            dist = stats.norm.pdf(position, loc=p + v, scale=sigma_transition_position)
            if np.sum(dist) == 0:
                if p + v < 0:
                    dist[0] = 1
                elif p + v > position[-1]:
                    dist[-1] = 1 # All weight on greatest position
                else:
                    print(f"bounds: {position[0]}, {position[-1]}")
                    print(f"p+v: {p+v}")
                    raise ValueError("This should not happen, try increasing 'sigma_transition_position'")
            tr[p_idx, v_idx, :] = dist

    transition_position_pvp = normalize_last_dim(tr)

    # Make sure that all probabilities sum to (more or less) one
    np.allclose(np.sum(transition_position_pvp, axis=-1), 1)
    return transition_position_pvp


def get_timestep(dt, timestep, timezone="Europe/London"):
    """
    Get the timestep index for a given datetime
    """
    dt = dt.astimezone(tz(timezone))
    timestep_duration = SECONDS_IN_DAY / timestep.size
    start_of_day = datetime.combine(dt, time.min, tzinfo=dt.tzinfo)
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def get_datetime_from_timestep(t, now, timestep):
    delta = timedelta(seconds=(t*SECONDS_IN_DAY/timestep.size))
    tm = (datetime.min + delta).time()
    return datetime.combine(now.date(), tm)


# def is_nudged(now, username):
#     u = User.objects.filter(username=username).first()
#     assert u is not None, f"User {username} not found."
#     for c in u.challenge_set.filter(accepted=True):
#         print(c.dt_begin, c.dt_end, now)
#         if c.dt_begin <= now <= c.dt_end:
#             print("yeah")
#         else:
#             print("no")
#     ch = u.challenge_set.filter(accepted=True, dt_begin__lte=now, dt_end__gte=now)
#     return ch.exists()


def extract_step_events(
        step_counts: pd.Series or np.ndarray,
        datetimes: pd.Series,
        remove_empty_days: bool = False):

    if isinstance(step_counts, pd.Series):
        step_counts = step_counts.to_numpy()
    all_pos = step_counts
    all_dt = datetimes

    min_date = all_dt.min().date()
    days = np.asarray([(dt.date() - min_date).days for dt in all_dt])
    uniq_days = np.unique(days)
    all_timestamp = np.asarray([
        (dt - datetime.combine(dt, time.min, dt.tz)).total_seconds()
        for dt in all_dt
    ])
    # Make it a fraction of day (between 0 and 1)
    all_timestamp /= SECONDS_IN_DAY
    # List of step events for each day, the event itself being the timestamp of the step
    step_events = [[] for _ in range(uniq_days.size)]
    # print("step_events", step_events)
    # Loop over the unique days
    for idx_day, day in enumerate(uniq_days):
        # print("idx_day", idx_day, "day", day)
        is_day = days == day
        obs_timestamp, obs_pos = all_timestamp[is_day], all_pos[is_day]
        # print("obs_timestamp", obs_timestamp, "obs_pos", obs_pos)
        # Sort the data by timestamp
        idx = np.argsort(obs_timestamp)
        obs_timestamp, obs_pos = obs_timestamp[idx], obs_pos[idx]

        # Compute the number of steps between each observed timestamp
        diff_obs_pos = np.diff(obs_pos)

        for ts, dif in zip(obs_timestamp, diff_obs_pos):
            # TODO: In the future, we probably want to spread that
            #  over a period assuming something like 6000 steps per hour
            step_events[idx_day] += [ts for _ in range(dif)]
            # print("ts", ts, "dif", dif)
    # print("step_events after loop", step_events)
    # if len(all_timestamp) == 3:
    #     exit(0)
    # Remove empty days
    if remove_empty_days:
        step_events = [i for i in step_events if len(i)]
    # print("n_days after filtering empty days", len(step_events))
    return step_events


def extract_actions(
        u: User,
        timestep: np.ndarray,
        now: datetime = None
) -> np.ndarray:

    """
    Extract the actions taken by the assistant
    """
    # Get all the challenges for this user
    if now is None:
        all_ch = u.challenge_set.all()
    else:
        all_ch = u.challenge_set.filter(dt_begin__date=now.date())
    # Get the unique dates for this user (by looking at the beginning of the challenges)
    dates = sorted(np.unique([ch.dt_begin.date() for ch in all_ch]))
    # Initialize the actions array
    actions = np.zeros((len(dates), timestep.size - 1), dtype=int)
    # Get the date and timestep for each challenge
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in all_ch])
    ch_timestep = np.asarray([get_timestep(ch.dt_begin, timestep=timestep) for ch in all_ch])
    # Set the actions
    for date, t in zip(ch_date, ch_timestep):
        actions[date, t] = 1

    if actions.shape[0] == 1:
        actions = actions.flatten()
    return actions
