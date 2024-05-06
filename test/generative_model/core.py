import numpy as np
import scipy.stats as stats
from datetime import datetime, time
from glob import glob
import pandas as pd

from .activity_simulation import generate_nudge_effect, generate_observations
from .fit import fit_model
from .sample import sample

from test.activity.activity import (
    normalize_last_dim,
    extract_step_events,
    build_pseudo_count_matrix,
    step_events_to_cumulative_steps
)
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


def generative_model(
        user,
        data_path,
        timestep,
        n_samples,
        child_models_n_components,
        pseudo_count_jitter,
        position,
        action_plans,
        seed
) -> np.ndarray:

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
    # -------------------------------
    # Load data
    step_events = load_data(user=user, data_path=data_path)
    # Fit the model
    model, transforms = fit_model(
        step_events=step_events,
        child_models_n_components=child_models_n_components,
        random_state=seed
    )
    # Sample from the model
    step_events = sample(
        model=model,
        transforms=transforms,
        n_samples=n_samples,
    )

    cum_steps_without_nudging = step_events_to_cumulative_steps(
        step_events=step_events,
        timestep=timestep
    )

    nudge_effect = generate_nudge_effect(
        timestep=timestep,
        n_samples=n_samples,
        seed=seed
    )

    cum_steps, actions = generate_observations(
        cum_steps=cum_steps_without_nudging,
        nudge_effect=nudge_effect,
        action_plans=action_plans,
        seed=seed
    )

    # Compute pseudo-count matrix
    pseudo_counts = build_pseudo_count_matrix(
        actions=actions,
        cum_steps=cum_steps,
        position=position,
        timestep=timestep,
        jitter=pseudo_count_jitter,
        log_update_count=False
    )
    # Compute expected probabilities
    transition = normalize_last_dim(pseudo_counts)  # Expected value given Dirichlet distribution parameterised by alpha
    # Make sure that all probabilities sum to (more or less) one
    assert np.allclose(np.sum(transition, axis=-1), 1)
    return transition
