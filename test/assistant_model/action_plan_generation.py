import numpy as np
from datetime import datetime, time, timedelta
from pytz import timezone
import itertools

SEC_IN_DAY = 86400


def get_timestep(dt, timestep):
    """
    Get the timestep index for a given datetime
    """
    timestep_duration = SEC_IN_DAY / timestep.size
    start_of_day = datetime.combine(dt, time.min, tzinfo=dt.tzinfo)
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def get_challenges(time_zone, challenge_window, offer_window, n_challenges_per_day,
                   start_time="7:00"):

    class Challenge:
        def __init__(self, dt_earliest=None, dt_latest=None):
            self.dt_earliest = dt_earliest
            self.dt_latest = dt_latest

    # Start time
    start_time = datetime.strptime(start_time, '%H:%M')
    start_time = timezone(time_zone).localize(start_time)

    # Generate datetime objects
    datetimes = [start_time + timedelta(hours=offer_window) +
                 timedelta(hours=i*(challenge_window+offer_window))
                 for i in range(n_challenges_per_day)]

    challenges = [Challenge(dt_earliest=dt, dt_latest=dt + timedelta(hours=challenge_window))
                  for dt in datetimes]
    return challenges


def get_possible_action_plans(challenges, timestep) -> np.ndarray:

    h = timestep.size - 1

    strategies = []
    related_timesteps = []

    # begin_of_day = local(challenges.first().dt_earliest).replace(hour=0, minute=0, second=0, microsecond=0)
    # delta_t = timedelta(seconds=SEC_IN_DAY/N_TIMESTEP)

    for ch in challenges:
        # print("Challenge:", local(ch.dt_earliest), local(ch.dt_latest))
        ch_earliest_t_idx = get_timestep(ch.dt_earliest, timestep)
        ch_latest_t_idx = get_timestep(ch.dt_latest, timestep)
        duration_in_timestep = ch_latest_t_idx - ch_earliest_t_idx
        # print(timedelta(seconds=duration_in_timestep*SEC_IN_DAY/N_TIMESTEP))
        # print("duration in timestep", duration_in_timestep)
        # print("duration in time", ch.dt_latest - ch.dt_earliest)
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

    # print(f"action plan ({len(action_plan)})", action_plan)
    return np.asarray(action_plans, dtype=int)
