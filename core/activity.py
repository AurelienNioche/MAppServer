import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import numpy as np
import pandas as pd
from datetime import datetime, time

from MAppServer.settings import (
    POSITION,
    TIMESTEP,
    LOG_AT_EACH_TIMESTEP
)
from user.models import User
from core.timestep_and_datetime import get_timestep_from_datetime, challenge_duration_to_n_timesteps
from utils import logging
from utils.constants import SECONDS_IN_A_DAY


LOGGER = logging.get(__name__)


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def step_events_to_cumulative_steps(step_events: list) -> np.ndarray:
    """Compute the cumulative steps from the step events."""
    n_days = len(step_events)
    cum_steps = np.zeros((n_days, TIMESTEP.size+1), dtype=int)
    for day_idx, step_events_day in enumerate(step_events):
        cum_steps_per_timestep = np.sum(step_events_day <= TIMESTEP[:, None], axis=1)
        cum_steps[day_idx] = np.concatenate((np.zeros(1, dtype=int), cum_steps_per_timestep))
        # deriv_cum_steps[idx_day, 1:] = cum_steps_day[1:] - cum_steps_day[:-1]
        if LOG_AT_EACH_TIMESTEP and n_days < 100:
            for t_idx, t in enumerate(TIMESTEP):
                print(f"day_idx {day_idx:02} t_idx {t_idx:02} cum_steps {cum_steps[day_idx, t_idx]}")
    return cum_steps


def cum_steps_to_pos_idx(cum_steps):
    all_v_idx = np.zeros_like(cum_steps, dtype=int)
    for idx_day, act in enumerate(cum_steps):
        all_v_idx[idx_day] = np.argmin(np.abs(POSITION[:, None] - act), axis=0)
    return all_v_idx


def initialize_pseudo_counts(jitter, n_action: int = 2):
    """Initialize the pseudo-count matrix.

    Note that for the mask, it is equivalent to do:
        for p_t in range(position.size):
            for p_tp1 in range(position.size):
                if p_tp1 >= p_t:
                    pseudo_counts[:, :, p_t, p_tp1] += jitter
    """
    pseudo_counts = np.zeros((n_action, TIMESTEP.size, POSITION.size, POSITION.size), dtype=float)
    # Create a mask where p_tp1 >= p_t (upper triangle)
    mask = np.tri(POSITION.size, POSITION.size, 0, dtype=bool).T
    # Add jitter where mask is True
    pseudo_counts[:, :, mask] += jitter
    return pseudo_counts


def build_pseudo_count_matrix(
        actions: np.ndarray,
        cum_steps: np.ndarray,
        jitter: float,
        n_action: int = 2
) -> np.ndarray:
    """Compute the alpha matrix (pseudo-counts) for the transition matrix."""
    # Extract the number of days
    n_days = cum_steps.shape[0]
    # Get the position indexes
    all_idx = cum_steps_to_pos_idx(cum_steps=cum_steps)
    # Initialise it
    pseudo_counts = initialize_pseudo_counts(
        jitter=jitter,
        n_action=n_action
    )
    # Loop over the days
    for day in range(n_days):
        # Loop over the timesteps
        for t_idx in range(TIMESTEP.size):
            # Increment the pseudo-count matrix
            action = actions[day, t_idx]
            idx_at_t = all_idx[day, t_idx]
            idx_at_tp1 = all_idx[day, t_idx + 1]
            pseudo_counts[action, t_idx, idx_at_t, idx_at_tp1] += 1

    return pseudo_counts


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
    # noinspection PyTestUnpassedFixture
    all_timestamp = np.asarray([
        (dt - datetime.combine(dt, time.min, dt.tz)).total_seconds()
        for dt in all_dt
    ])
    # Make it a fraction of day (between 0 and 1)
    all_timestamp /= SECONDS_IN_A_DAY
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
    actions = np.zeros((len(dates), TIMESTEP.size), dtype=int)
    # Get the date and timestep for each challenge
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in all_ch])
    ch_timestep = np.asarray([get_timestep_from_datetime(ch.dt_begin) for ch in all_ch])
    # Duration of a challenge in timesteps
    ch_dur = challenge_duration_to_n_timesteps()
    # Set the actions
    for date, t in zip(ch_date, ch_timestep):
        for _t in range(ch_dur):
            actions[date, t + _t] = 1
    # Handle special case
    if actions.shape[0] == 1:
        actions = actions.flatten()
    return actions
