import numpy as np
import os
from scipy.special import softmax

from .activity_simulation import generate_nudge_effect, generate_observations
from .fit import fit_model
from .sample import sample

from test.data import data

from test.plot import plot

from test.baseline import baseline

from test.activity.activity import (
    build_pseudo_count_matrix, compute_deriv_cum_steps,
    build_position_transition_matrix, normalize_last_dim
)


def generative_model(
        user, data_path, timestep, n_samples, child_models_n_components,
        velocity, pseudo_count_jitter, position, sigma_transition_position
):

    # Load data
    step_events = data.load_data(user=user, data_path=data_path)

    # Fit the model
    model, transforms = fit_model(step_events=step_events, child_models_n_components=child_models_n_components)

    step_events = sample(model=model, transforms=transforms, n_samples=n_samples)

    activity_samples = compute_deriv_cum_steps(step_events=step_events, timestep=timestep)

    nudge_effect = generate_nudge_effect(timestep=timestep, n_samples=n_samples)

    observations, actions = generate_observations(
        activity_samples=activity_samples,
        nudge_effect=nudge_effect,
        timestep=timestep
    )

    # Compute pseudo-count matrix
    alpha_atvv = build_pseudo_count_matrix(
        actions=actions,
        observations=observations,
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

    # Generate action plans
    h = timestep.size - 1
    action_plans = np.zeros((h, h), dtype=int) #list(itertools.product(range(n_action), repeat=h))
    action_plans[:] = np.eye(h)

    return transition_velocity_atvv, transition_position_pvp, action_plans
