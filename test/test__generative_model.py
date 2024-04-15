import numpy as np
import os
from scipy.special import softmax

from generative_model.core import generative_model


from data.data import load_data

from plot import plot

from baseline import baseline

from activity.activity import (build_pseudo_count_matrix, compute_deriv_cum_steps,
                               build_position_transition_matrix, normalize_last_dim)

from assistant_model.assistant_model import test_assistant_model

USER = "11AV"
DATA_FOLDER = data_path = os.path.dirname(os.path.dirname(__file__)) + "/data"
N_TIMESTEP = 11
N_POSITION = 60
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
POSITION = np.linspace(0, 20000, N_POSITION)
SIGMA_POSITION_TRANSITION = 10.0
N_VELOCITY = 60
# velocity = np.concatenate((np.zeros(1), np.geomspace(2, np.max(combined)+1, n_velocity-1)))
VELOCITY = np.linspace(0, 15000+1, N_VELOCITY)
PSEUDO_COUNT_JITTER = 1e-3

N_SAMPLES = 1000
CHILD_MODELS_N_COMPONENTS = 3
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
N_RESTART = 4
N_EPISODES = 200


def main():
    transition_velocity_atvv, transition_position_pvp, action_plans = generative_model(
        user=USER, data_path=DATA_FOLDER,
        timestep=TIMESTEP, n_samples=N_SAMPLES,
        child_models_n_components=CHILD_MODELS_N_COMPONENTS,
        velocity=VELOCITY, pseudo_count_jitter=PSEUDO_COUNT_JITTER,
        position=POSITION, sigma_transition_position=SIGMA_POSITION_TRANSITION
    )
    # Run the baseline
    runs = baseline.run(
        action_plans=action_plans,
        transition_velocity_atvv=transition_velocity_atvv,
        transition_position_pvp=transition_position_pvp,
        timestep=TIMESTEP, position=POSITION, velocity=VELOCITY,
        n_restart=N_RESTART
    )

    plot.runs(*runs)

    # Select action plan
    af_run = test_assistant_model(
        action_plans=action_plans,
        log_prior_position=LOG_PRIOR,
        gamma=1.0,
        n_episodes=N_EPISODES,
        alpha_jitter=0.1,
        position=POSITION,
        velocity=VELOCITY,
        transition_velocity_atvv=transition_velocity_atvv,
        transition_position_pvp=transition_position_pvp,
        timestep=TIMESTEP,
        n_restart=N_RESTART
    )
    runs.append(af_run)
    plot.runs(*runs)
    plot.plot_af(af_run)


if __name__ == "__main__":

    main()




