import numpy as np
import scipy.stats as stats
from datetime import datetime, time
from glob import glob
import pandas as pd

from .activity_simulation import generate_nudge_effect, generate_observations
from .fit import fit_model
from .sample import sample

from test.activity.activity import normalize_last_dim, extract_step_events, build_pseudo_count_matrix, build_position_transition_matrix, convert_timesteps_into_activity_level
SECONDS_IN_DAY = 86400


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


# def build_position_transition_matrix(
#         position: np.ndarray,
#         velocity: np.ndarray,
#         sigma_transition_position: float = 1e-3
# ) -> np.ndarray:
#     # Compute position transition matrix
#     tr = np.zeros((position.size, velocity.size, position.size))
#     for p_idx, p in enumerate(position):
#         for v_idx, v in enumerate(velocity):
#             dist = stats.norm.pdf(position, loc=p + v, scale=sigma_transition_position)
#             if np.sum(dist) == 0:
#                 if p + v < 0:
#                     dist[0] = 1
#                 elif p + v > position[-1]:
#                     dist[-1] = 1 # All weight on greatest position
#                 else:
#                     print(f"bounds: {position[0]}, {position[-1]}")
#                     print(f"p+v: {p+v}")
#                     raise ValueError("This should not happen, try increasing 'sigma_transition_position'")
#             tr[p_idx, v_idx, :] = dist
#
#     transition_position_pvp = normalize_last_dim(tr)
#
#     # Make sure that all probabilities sum to (more or less) one
#     np.allclose(np.sum(transition_position_pvp, axis=-1), 1)
#     return transition_position_pvp


# def compute_deriv_cum_steps(
#         step_events: list,
#         timestep: np.ndarray
# ) -> np.ndarray:
#     """
#     Compute the derivative of the cumulative steps
#     """
#     deriv_cum_steps = np.zeros((len(step_events), timestep.size))
#     for idx_day, step_events_day in enumerate(step_events):
#         cum_steps_day = np.sum(step_events_day <= timestep[:, None], axis=1)
#         deriv_cum_steps_day = np.gradient(cum_steps_day, timestep+1)
#         deriv_cum_steps_day /= timestep.size-1
#         deriv_cum_steps[idx_day] = deriv_cum_steps_day
#     return deriv_cum_steps


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
    )

    activity_samples = convert_timesteps_into_activity_level(
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
