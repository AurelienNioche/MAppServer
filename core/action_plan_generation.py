import numpy as np
from datetime import datetime, timedelta
from pytz import timezone
import itertools
from itertools import product

from user.models import User
from core.activity import extract_actions
from MAppServer.settings import (
    TIME_ZONE,
    TIMESTEP,
    OFFER_WINDOW,
    CHALLENGE_WINDOW,
    N_CHALLENGES_PER_DAY,
    DISCARD_OVERLAPPING_STRATEGIES
)
from core.timestep_and_datetime import get_timestep_from_datetime, challenge_duration_to_n_timesteps


def get_challenges(
        start_time):

    class Challenge:
        def __init__(self, dt_earliest, dt_latest):
            self.dt_earliest = dt_earliest
            self.dt_latest = dt_latest
            self.dt_offer_begin = dt_earliest - timedelta(hours=OFFER_WINDOW)

    # Start time
    start_time = datetime.strptime(start_time, '%H:%M')
    start_time = timezone(TIME_ZONE).localize(start_time)

    # Generate datetime objects
    datetimes = [
        start_time + timedelta(hours=OFFER_WINDOW) +
        timedelta(hours=i*(CHALLENGE_WINDOW+OFFER_WINDOW))
        for i in range(N_CHALLENGES_PER_DAY)]

    challenges = [
        Challenge(
            dt_earliest=dt,
            dt_latest=dt + timedelta(hours=CHALLENGE_WINDOW)
        ) for dt in datetimes]
    return challenges


def generate_possibilities_for_single_challenge():
    """Generate all the possibilities for a single challenge."""
    # Duration in timesteps of a single challenge
    ch_dur = challenge_duration_to_n_timesteps()
    # Generate all possible combinations of 1's and 0's of length n
    all_combinations = list(product([0, 1], repeat=CHALLENGE_WINDOW))
    # Filter out combinations that don't have 'g' groups of 'k' ones
    valid_combinations = []
    for combination in all_combinations:
        # Convert combination to string
        str_comb = ''.join(map(str, combination))
        # Split string by '0'
        groups = str_comb.split('0')
        # Count groups of 'ch_dur' ones
        count = sum(1 for group in groups if group == '1'*ch_dur)
        if count != 1:
            continue
        count_2 = sum(1 for group in groups if '1' in group)
        if count_2 != 1:
            continue
        valid_combinations.append(combination)

    # Convert valid combinations to numpy array
    action_plans = np.array(valid_combinations, dtype=int)

    # Discard overlapping strategies if asked for it
    if DISCARD_OVERLAPPING_STRATEGIES:
        action_plans = action_plans[::-1]
        valid_action_plans = np.atleast_2d(action_plans[0])
        for i in range(1, action_plans.shape[0]):
            stacked = np.atleast_2d(np.vstack((valid_action_plans, np.atleast_2d(action_plans[i]))))
            _sum_columns = np.sum(stacked, axis=0)
            if np.any(_sum_columns > 1):
                continue
            else:
                valid_action_plans = stacked
        action_plans = valid_action_plans
    return action_plans


def get_possible_action_plans(
        challenges: list,
        now: datetime = None,
        u: User = None
) -> np.ndarray or tuple:

    h = TIMESTEP.size

    strategies = []
    related_timesteps = []

    t_idx = None
    last_challenge_t_idx = None
    action_taken = None
    if u is not None:
        t_idx = get_timestep_from_datetime(now)
        action_taken = extract_actions(u=u, now=now)
        last_challenge_t_idx = 0  # Every future will be compatible

    for ch in challenges:
        ch_earliest_t_idx = get_timestep_from_datetime(ch.dt_earliest)
        ch_latest_t_idx = get_timestep_from_datetime(ch.dt_latest)
        ch_offer_t_idx = get_timestep_from_datetime(ch.dt_offer_begin)
        if now is not None and ch_offer_t_idx <= t_idx:
            last_challenge_t_idx = ch_latest_t_idx
            continue
        window_duration_in_ts = ch_latest_t_idx - ch_earliest_t_idx
        timesteps = np.arange(ch_earliest_t_idx, ch_latest_t_idx)
        challenge_duration_in_ts = challenge_duration_to_n_timesteps()
        assert challenge_duration_in_ts % window_duration_in_ts, "Nope"
        strategies_for_single = generate_possibilities_for_single_challenge()
        strategies.append(strategies_for_single)
        related_timesteps.append(timesteps)

    action_plans = []
    for challenge_parts in itertools.product(*strategies):
        action_plan = np.zeros(h, dtype=int)
        for i, challenge_part in enumerate(challenge_parts):
            action_plan[related_timesteps[i]] = challenge_part

        action_plans.append(action_plan)
    action_plans = np.asarray(action_plans, dtype=int)

    if now is None:
        return action_plans
    else:
        # Changing the past is not a possibility
        # Select only the action plans which are compatible with the past
        mask = np.all(
            action_plans[:, :last_challenge_t_idx]
            == action_taken[:last_challenge_t_idx],
            axis=1)
        action_plans = action_plans[mask]
        # Take only the future
        future_action_plans = action_plans[:, t_idx:]
        return action_plans, future_action_plans
