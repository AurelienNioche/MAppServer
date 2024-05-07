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
from test.config.config import LOG_ACTIVITY


SECONDS_IN_DAY = 86400


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def step_events_to_cumulative_steps(
        step_events: list,
        timestep: np.ndarray,
        log_cumulative_steps: bool = False,
) -> np.ndarray:
    """Compute the cumulative steps from the step events."""
    cum_steps = np.zeros((len(step_events), timestep.size+1), dtype=float)
    for idx_day, step_events_day in enumerate(step_events):
        cum_steps[idx_day] = np.concatenate((np.zeros(1, dtype=int), np.sum(step_events_day <= timestep[:, None], axis=1)))
        # deriv_cum_steps[idx_day, 1:] = cum_steps_day[1:] - cum_steps_day[:-1]
        if log_cumulative_steps:
            print("day", idx_day, "cum_steps", cum_steps[idx_day])
    return cum_steps


def cum_steps_to_pos_idx(cum_steps, position, log_update_count=False):
    # Add one bin for infinity
    # bins = velocity # np.concatenate((velocity, np.full(1, np.inf)))
    # Clip the activity to the bins
    # drv = np.clip(activity, bins[0], bins[-1])
    # all_v_idx = np.digitize(drv, bins, right=True) # - 1
    all_v_idx = np.zeros_like(cum_steps, dtype=int)
    for idx_day, act in enumerate(cum_steps):
        all_v_idx[idx_day] = np.argmin(np.abs(position[:, None] - act), axis=0)
        if log_update_count:
            print("day", idx_day)
            print("act", act)
            print("v_idx", all_v_idx[idx_day])
        #activity_to_velocity_index(act, velocity)
    return all_v_idx

# def position_to_position_index(position, position):
#     return np.argmin(np.abs(position_bins[:, None] - position), axis=0)


def build_pseudo_count_matrix(
        actions: np.ndarray,
        cum_steps: np.ndarray,
        timestep: np.ndarray,
        position: np.ndarray,
        jitter: float,
        dt_min: datetime = None,
        dt_max: datetime = None,
        n_action: int = 2,
        log_update_count: bool = False
) -> np.ndarray:
    """Compute the alpha matrix (pseudo-counts) for the transition matrix."""
    # Extract the minimum and maximum timestamps in seconds (period where the data was collected)
    dt_min_sec = dt_min.timestamp() if dt_min is not None else 0
    dt_max_sec = dt_max.timestamp() if dt_max is not None else SECONDS_IN_DAY
    sec_per_timestep = SECONDS_IN_DAY / timestep.size
    # Get the velocity index for each activity level
    all_idx = cum_steps_to_pos_idx(cum_steps=cum_steps, position=position, log_update_count=log_update_count)
    # # Initialize the pseudo-count matrix
    # alpha_atvv = np.zeros((n_action, timestep.size, position.size, position.size))
    # for p_t in range(position.size):
    #     for p_tp1 in range(position.size):
    #         if p_tp1 >= p_t:
    #             alpha_atvv[:, :, p_t, p_tp1] += jitter
    # Initialize the pseudo-count matrix
    pseudo_counts = np.zeros((n_action, timestep.size, position.size, position.size))
    # Create a mask where p_tp1 >= p_t
    mask = np.tri(position.size, position.size, 0, dtype=bool).T
    # Add jitter where mask is True
    pseudo_counts[:, :, mask] += jitter
    # Initialize the time counter
    dt = dt_min_sec if dt_min is not None else 0
    if LOG_ACTIVITY:
        print("activity", cum_steps.shape)
    # Loop over the days
    for day in range(cum_steps.shape[0]):
        # # TODO: For now, we're skipping days with no activity,
        # #   but we might want to change that in the future
        # if skip_empty_days and cum_steps[day].sum() == 0:
        #     continue
        # Loop over the timesteps
        for t_idx in range(timestep.size):
            # If the timestamp is outside the range, skip (just increment the time)
            if ((dt_min is not None and dt < dt_min_sec)
                    or (dt_max is not None and dt > dt_max_sec)):
                dt += sec_per_timestep
                continue
            # Increment the pseudo-count matrix
            action = actions[day, t_idx]
            idx_at_t = all_idx[day, t_idx]
            idx_at_tp1 = all_idx[day, t_idx + 1]
            print("UPDATE PSEUDO-COUNTS", "t_idx", t_idx, "action", action, "day", day, "pos_idx", idx_at_t, "new_pos_idx", idx_at_tp1)
            pseudo_counts[action, t_idx, idx_at_t, idx_at_tp1] += 1
            dt += sec_per_timestep
    # Return the pseudo-count matrix
    return pseudo_counts


def get_timestep(dt, timestep, timezone=TIME_ZONE):
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