import numpy as np
import scipy.stats as stats
from datetime import datetime, time
from glob import glob
import pandas as pd

from .activity_simulation import generate_nudge_effect, generate_observations
from .fit import fit_model
from .sample import sample

SECONDS_IN_DAY = 86400


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


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

def load_data(
        user: str,
        data_path: str,
        remove_empty_days: bool = True
) -> list:
    # Extract the file path
    file = glob(f"{data_path}/dump_latest/{user}_activity*.csv")[0]

    df = pd.read_csv(file, index_col=0)
    df.dt = pd.to_datetime(df.dt, utc=False, format="ISO8601")
    df.dt = df.dt.dt.tz_convert("Europe/London")

    step_events = extract_step_events(
        step_counts=df.step_midnight,
        datetimes=df.dt,
        remove_empty_days=remove_empty_days
    )
    return step_events

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
    # Extract the minimum and maximum timestamps in seconds (period where the data was collected)
    dt_min_sec = dt_min.timestamp() if dt_min is not None else 0
    dt_max_sec = dt_max.timestamp() if dt_max is not None else SECONDS_IN_DAY
    sec_per_timestep = SECONDS_IN_DAY / timestep.size
    # Add one bin for infinity
    bins = np.concatenate((velocity, np.full(1, np.inf)))
    # Clip the activity to the bins
    drv = np.clip(activity, bins[0], bins[-1])
    v_idx = np.digitize(drv, bins, right=False) - 1
    # Initialize the pseudo-count matrix
    alpha_atvv = np.zeros((n_action, timestep.size-1, velocity.size, velocity.size))
    alpha_atvv += jitter
    # Initialize the time counter
    dt = dt_min_sec if dt_min is not None else 0
    # Loop over the days
    for day in range(activity.shape[0]):
        # Loop over the timesteps
        for t in range(timestep.size - 1):
            # If the timestamp is outside the range, skip (just increment the time)
            if ((dt_min is not None and dt < dt_min_sec)
                    or (dt_max is not None and dt > dt_max_sec)):
                dt += sec_per_timestep
                continue
            # Increment the pseudo-count matrix
            alpha_atvv[actions[day, t], t, v_idx[day, t], v_idx[day, t + 1]] += 1
            dt += sec_per_timestep
    # Return the pseudo-count matrix
    return alpha_atvv

def compute_deriv_cum_steps(
        step_events: list,
        timestep: np.ndarray
) -> np.ndarray:
    """
    Compute the derivative of the cumulative steps
    """
    deriv_cum_steps = np.zeros((len(step_events), timestep.size))
    for idx_day, step_events_day in enumerate(step_events):
        cum_steps_day = np.sum(step_events_day <= timestep[:, None], axis=1)
        deriv_cum_steps_day = np.gradient(cum_steps_day, timestep+1)
        deriv_cum_steps_day /= timestep.size-1
        deriv_cum_steps[idx_day] = deriv_cum_steps_day
    return deriv_cum_steps


def generative_model(
        user, data_path, timestep, n_samples, child_models_n_components,
        velocity, pseudo_count_jitter, position, sigma_transition_position,
        action_plans,
        seed
):

    # print("generative_model ----------------")
    # print("user", user)
    # print("data_path", data_path)
    # print("timestep", timestep)
    # print("n_samples", n_samples)
    # print("child_models_n_components", child_models_n_components)
    # print("velocity", velocity)
    # print("pseudo_count_jitter", pseudo_count_jitter)
    # print("position", position)
    # print("sigma_transition_position", sigma_transition_position)
    # print("action_plans", action_plans)
    # print("seed", seed)

    # Load data
    step_events = load_data(user=user, data_path=data_path)

    # Fit the model
    model, transforms = fit_model(
        step_events=step_events,
        child_models_n_components=child_models_n_components,
        random_state=seed
    )

    step_events = sample(
        model=model,
        transforms=transforms,
        n_samples=n_samples,
        seed=seed
    )

    activity_samples = compute_deriv_cum_steps(
        step_events=step_events,
        timestep=timestep
    )

    nudge_effect = generate_nudge_effect(
        timestep=timestep,
        n_samples=n_samples,
        seed=seed
    )

    observed_activity, observed_action_plans = generate_observations(
        activity_samples=activity_samples,
        nudge_effect=nudge_effect,
        action_plans=action_plans,
        seed=seed
    )

    # Compute pseudo-count matrix
    alpha_atvv = build_pseudo_count_matrix(
        actions=observed_action_plans,
        activity=observed_activity,
        timestep=timestep,
        velocity=velocity,
        jitter=pseudo_count_jitter
    )

    # Compute expected probabilities
    transition_velocity_atvv = normalize_last_dim(alpha_atvv) # Expected value given Dirichlet distribution parameterised by alpha
    # Make sure that all probabilities sum to (more or less) one: np.allclose(np.sum(transition_velocity_atvv, axis=-1), 1)

    # Compute position transition matrix
    transition_position_pvp = build_position_transition_matrix(
        position=position,
        velocity=velocity,
        sigma_transition_position=sigma_transition_position
    )

    return transition_velocity_atvv, transition_position_pvp
