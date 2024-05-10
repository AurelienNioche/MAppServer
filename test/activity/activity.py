import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from pytz import timezone as tz

from MAppServer.settings import TIME_ZONE
from user.models import User
from test.config.config import (
    TIMESTEP,
    LOG_AT_EACH_TIMESTEP,
    LOG_PSEUDO_COUNT_UPDATE,
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER)

from test.assistant_model.action_plan_selection import compute_number_of_observations
from utils import logging

SECONDS_IN_DAY = 86400
LOGGER = logging.get(__name__)


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def step_events_to_cumulative_steps(
        step_events: list,
        timestep: np.ndarray
) -> np.ndarray:
    """Compute the cumulative steps from the step events."""
    n_days = len(step_events)
    cum_steps = np.zeros((n_days, timestep.size+1), dtype=float)
    for day_idx, step_events_day in enumerate(step_events):
        cum_steps_per_timestep = np.sum(step_events_day <= timestep[:, None], axis=1)
        cum_steps[day_idx] = np.concatenate((np.zeros(1, dtype=int), cum_steps_per_timestep))
        # deriv_cum_steps[idx_day, 1:] = cum_steps_day[1:] - cum_steps_day[:-1]
        if LOG_AT_EACH_TIMESTEP and n_days < 100:
            for t_idx, t in enumerate(timestep):
                print(f"day_idx {day_idx:02} t_idx {t_idx:02} cum_steps {cum_steps[day_idx, t_idx]}")
    return cum_steps


def cum_steps_to_pos_idx(cum_steps, position):
    all_v_idx = np.zeros_like(cum_steps, dtype=int)
    for idx_day, act in enumerate(cum_steps):
        all_v_idx[idx_day] = np.argmin(np.abs(position[:, None] - act), axis=0)
    return all_v_idx


def build_pseudo_count_matrix(
        actions: np.ndarray,
        cum_steps: np.ndarray,
        timestep: np.ndarray,
        position: np.ndarray,
        jitter: float,
        n_action: int = 2
) -> np.ndarray:
    """Compute the alpha matrix (pseudo-counts) for the transition matrix."""
    # Extract the number of days
    n_days = cum_steps.shape[0]

    DEBUG = False  # n_days < 100

    if DEBUG:
        for day in range(n_days):
            for t_idx in range(timestep.size):
                print("day", day, "t_idx", t_idx, cum_steps[day, t_idx])

    # Get the velocity index for each activity level
    all_idx = cum_steps_to_pos_idx(cum_steps=cum_steps, position=position)
    # Initialize the pseudo-count matrix
    pseudo_counts = np.zeros((n_action, timestep.size, position.size, position.size))
    # Create a mask where p_tp1 >= p_t
    mask = np.tri(position.size, position.size, 0, dtype=bool).T
    # Add jitter where mask is True
    # pseudo_counts[:, :, mask] += jitter

    sum_mask = np.sum(mask)

    pseudo_counts += jitter
    # Loop over the days
    for day in range(n_days):
        # Loop over the timesteps
        for t_idx in range(timestep.size):
            # Increment the pseudo-count matrix
            action = actions[day, t_idx]
            idx_at_t = all_idx[day, t_idx]
            idx_at_tp1 = all_idx[day, t_idx + 1]
            if DEBUG:
                print("UPDATE PSEUDO-COUNTS", "t_idx", t_idx, "action", action, "day", day, "pos_idx", idx_at_t, "new_pos_idx", idx_at_tp1)
            pseudo_counts[action, t_idx, idx_at_t, idx_at_tp1] += 1
    if DEBUG:
        n_obs = compute_number_of_observations(pseudo_counts)
        print("number of observations", n_obs)
        print("sum pseudo counts", np.sum(pseudo_counts))
        print("jitter sum", pseudo_counts.size*ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER)
        print("sum mask", sum_mask)
        print("sum -sum mask", np.sum(pseudo_counts) - sum_mask)
    # Return the pseudo-count matrix
    return pseudo_counts
# def build_pseudo_count_matrix(
#         actions: np.ndarray,
#         cum_steps: np.ndarray,
#         timestep: np.ndarray,
#         position: np.ndarray,
#         jitter: float,
#         dts: np.ndarray = None,
#         n_action: int = 2
# ) -> np.ndarray:
#     """Compute the alpha matrix (pseudo-counts) for the transition matrix."""
#     # Extract the minimum and maximum timestamps in seconds (period where the data was collected)
#     dt_min_sec = 0
#     dt_max_sec = SECONDS_IN_DAY
#     if dts is not None and len(dts):
#         dt_min_sec = dts.min().timestamp()
#         dt_max_sec = dts.max().timestamp()
#     sec_per_timestep = SECONDS_IN_DAY / timestep.size
#     # Get the velocity index for each activity level
#     all_idx = cum_steps_to_pos_idx(cum_steps=cum_steps, position=position)
#     # Initialize the pseudo-count matrix
#     pseudo_counts = np.zeros((n_action, timestep.size, position.size, position.size))
#     # Create a mask where p_tp1 >= p_t
#     mask = np.tri(position.size, position.size, 0, dtype=bool).T
#     # Add jitter where mask is True
#     pseudo_counts[:, :, mask] += jitter
#     # Extrat the number of days
#     n_days = cum_steps.shape[0]
#     # Initialize the time counter
#     dt = dt_min_sec
#     if LOG_ACTIVITY:
#         print("activity", cum_steps.shape)
#     # Loop over the days
#     for day in range(n_days):
#         # # TODO: For now, we're skipping days with no activity,
#         # #   but we might want to change that in the future
#         # if skip_empty_days and cum_steps[day].sum() == 0:
#         #     continue
#         # Loop over the timesteps
#         for t_idx in range(timestep.size):
#             # If the timestamp is outside the range, skip (just increment the time)
#             if dt < dt_min_sec or dt > dt_max_sec:
#                 dt += sec_per_timestep
#                 continue
#             # Increment the pseudo-count matrix
#             action = actions[day, t_idx]
#             idx_at_t = all_idx[day, t_idx]
#             idx_at_tp1 = all_idx[day, t_idx + 1]
#             if n_days < 100 and LOG_PSEUDO_COUNT_UPDATE:
#                 print("UPDATE PSEUDO-COUNTS", "t_idx", t_idx, "action", action, "day", day, "pos_idx", idx_at_t, "new_pos_idx", idx_at_tp1)
#             pseudo_counts[action, t_idx, idx_at_t, idx_at_tp1] += 1
#             dt += sec_per_timestep
#     # Return the pseudo-count matrix
#     return pseudo_counts


def get_timestep(dt, timestep=TIMESTEP, timezone=TIME_ZONE):
    """Get the timestep index for a given datetime"""
    dt = dt.astimezone(tz(timezone))
    timestep_duration = SECONDS_IN_DAY / timestep.size
    start_of_day = datetime.combine(dt, time.min, tzinfo=dt.tzinfo)
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def get_datetime_from_timestep(t, now, timestep):
    """Get the datetime from a timestep index"""
    delta = timedelta(seconds=(t*SECONDS_IN_DAY/timestep.size))
    tm = (datetime.min + delta).time()
    return datetime.combine(now.date(), tm)


def extract_step_events(
        step_counts: pd.Series or np.ndarray,
        datetimes: pd.Series,
        remove_empty_days: bool = False):

    if isinstance(step_counts, pd.Series):
        step_counts = step_counts.to_numpy()
    all_pos = step_counts
    all_dt = datetimes
    # Get the minimum date
    min_date = all_dt.min().date()
    # Get days as indexes with 0 being the first day, 1 being the second day, etc.
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
    # Loop over the unique days
    for idx_day, day in enumerate(uniq_days):
        is_day = days == day
        obs_timestamp, obs_pos = all_timestamp[is_day], all_pos[is_day]
        # Sort the data by timestamp
        idx = np.argsort(obs_timestamp)
        obs_timestamp, obs_pos = obs_timestamp[idx], obs_pos[idx]
        # Compute the number of steps between each observed timestamp
        diff_obs_pos = np.diff(obs_pos)
        # Add as many step events as the difference since the last record
        for ts, dif in zip(obs_timestamp, diff_obs_pos):
            # TODO: In the future, we probably want to spread that
            #  over a period assuming something like 6000 steps per hour
            step_events[idx_day] += [ts for _ in range(dif)]
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
    actions = np.zeros((len(dates), timestep.size), dtype=int)
    # Get the date and timestep for each challenge
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in all_ch])
    ch_timestep = np.asarray([get_timestep(ch.dt_begin, timestep=timestep) for ch in all_ch])
    # Set the actions
    for date, t in zip(ch_date, ch_timestep):
        actions[date, t] = 1

    if actions.shape[0] == 1:
        actions = actions.flatten()
    return actions


# #%%
# from test.config.config import POSITION as position, TIMESTEP as timestep
#
# n_action = 2
# jitter = 0.01
#
# # Initialize the pseudo-count matrix
# pseudo_counts = np.zeros((n_action, timestep.size, position.size, position.size))
#
# # Create a mask where p_tp1 >= p_t
# mask = np.tri(position.size, position.size, 0, dtype=bool).T
#
# # Add jitter where mask is True
# pseudo_counts[:, :, mask] += jitter
#
# alpha_atvv = np.zeros((n_action, timestep.size, position.size, position.size))
# for p_t in range(position.size):
#     for p_tp1 in range(position.size):
#         if p_tp1 >= p_t:
#             alpha_atvv[:, :, p_t, p_tp1] += jitter
#
# print(np.allclose(alpha_atvv, pseudo_counts))