import numpy as np
from datetime import datetime, time, timedelta
from pytz import timezone
import itertools

from user.models import User
from test.activity.activity import extract_actions

from MAppServer.settings import TIME_ZONE

SEC_IN_DAY = 86400


def get_timestep(dt, timestep):
    """
    Get the timestep index for a given datetime
    """
    timestep_duration = SEC_IN_DAY / timestep.size
    dt = dt.astimezone(timezone(TIME_ZONE))
    start_of_day = datetime.combine(dt, time.min, tzinfo=dt.tzinfo)
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def get_challenges(time_zone, challenge_window, offer_window, n_challenges_per_day,
                   start_time):

    class Challenge:
        def __init__(self, dt_earliest, dt_latest):
            self.dt_earliest = dt_earliest
            self.dt_latest = dt_latest
            self.dt_offer_begin = dt_earliest - timedelta(hours=offer_window)

    # Start time
    start_time = datetime.strptime(start_time, '%H:%M')
    start_time = timezone(time_zone).localize(start_time)

    # Generate datetime objects
    datetimes = [
        start_time + timedelta(hours=offer_window) +
        timedelta(hours=i*(challenge_window+offer_window))
        for i in range(n_challenges_per_day)]

    challenges = [
        Challenge(
            dt_earliest=dt,
            dt_latest=dt + timedelta(hours=challenge_window)
        ) for dt in datetimes]
    return challenges


def get_possible_action_plans(
        challenges: list,
        timestep: np.ndarray,
        now: datetime = None,
        u: User = None
) -> np.ndarray or tuple:

    h = timestep.size

    strategies = []
    related_timesteps = []

    t_idx = None
    last_challenge_t_idx = None
    action_taken = None
    if u is not None:
        t_idx = get_timestep(now, timestep=timestep)
        # print("t_idx", t_idx)
        action_taken = extract_actions(u=u, timestep=timestep, now=now)
        last_challenge_t_idx = 0  # Every future will be compatible

    for ch in challenges:
        # print("Challenge:", local(ch.dt_earliest), local(ch.dt_latest))
        ch_latest_t_idx = get_timestep(ch.dt_latest, timestep=timestep)
        ch_offer_t_idx = get_timestep(ch.dt_offer_begin, timestep=timestep)

        if now is not None and ch_offer_t_idx <= t_idx:
            last_challenge_t_idx = ch_latest_t_idx
            continue

        ch_earliest_t_idx = get_timestep(ch.dt_earliest, timestep=timestep)

        duration_in_timestep = ch_latest_t_idx - ch_earliest_t_idx
        timesteps = np.arange(ch_earliest_t_idx, ch_latest_t_idx)
        strategy = np.eye(duration_in_timestep, dtype=int)
        strategies.append(strategy)
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
