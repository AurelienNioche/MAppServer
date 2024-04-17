import numpy as np
import os
from scipy.special import softmax
from test.generative_model.core import generative_model

from test.plot import plot
from test.baseline import baseline
from test.assistant_model.action_plan_generation import get_possible_action_plans, get_challenges
from test.assistant_model.run import test_assistant_model

USER = "11AV"
DATA_FOLDER = data_path = os.path.dirname(os.path.dirname(__file__)) + "/data"
N_TIMESTEP = 24
N_POSITION = 50
TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
POSITION = np.linspace(0, 20000, N_POSITION)
SIGMA_POSITION_TRANSITION = 10.0
N_VELOCITY = 30
# velocity = np.concatenate((np.zeros(1), np.geomspace(2, np.max(combined)+1, n_velocity-1)))
VELOCITY = np.linspace(0, 12000, N_VELOCITY)
PSEUDO_COUNT_JITTER = 1e-3

N_SAMPLES = 1000
CHILD_MODELS_N_COMPONENTS = 3
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)*2))
N_RESTART = 4
N_EPISODES = 200

SEC_IN_DAY = 86400

TIME_ZONE = "Europe/London"

N_CHALLENGES_PER_DAY = 3
CHALLENGE_WINDOW = 2
OFFER_WINDOW = 1
START_TIME = "7:00"

#
# def get_simple_action_plans():
#     """
#     Everything is possible.
#     """
#     return np.eye(N_TIMESTEP-1, dtype=int)


def main():

    challenges = get_challenges(
        time_zone=TIME_ZONE,
        challenge_window=CHALLENGE_WINDOW,
        offer_window=OFFER_WINDOW,
        n_challenges_per_day=N_CHALLENGES_PER_DAY,
        start_time=START_TIME
    )

    action_plans = get_possible_action_plans(challenges=challenges, timestep=TIMESTEP)

    transition_velocity_atvv, transition_position_pvp = generative_model(
        action_plans=action_plans,
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

    # Compute performance of each action plan
    performance = [
        np.mean(r["position"][:, -1]) for r in runs
    ]
    # Sort action plans by performance
    idx = np.argsort(performance)[::-1]
    sorted_action_plans = action_plans[idx]
    for i, ap in enumerate(sorted_action_plans):
        print(f"#{i}: AP{idx[i]} {ap} with performance {performance[idx[i]]:.2f}")

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




