from .activity_simulation import generate_nudge_effect, generate_observations
from .fit import fit_model
from .sample import sample

from test.data import data

from test.activity.activity import (
    build_pseudo_count_matrix, convert_timesteps_into_activity_level,
    build_position_transition_matrix, normalize_last_dim
)


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
    step_events = data.load_data(user=user, data_path=data_path)

    # Fit the model
    model, transforms = fit_model(
        step_events=step_events,
        child_models_n_components=child_models_n_components,
        random_state=seed
    )

    step_events = sample(
        model=model,
        transforms=transforms,
        n_samples=n_samples
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
