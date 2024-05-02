import os

from test.assistant_model.run import test_assistant_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from MAppServer.settings import TIME_ZONE

import numpy as np

from test.generative_model.core import generative_model
from test.plot import plot
from test.baseline import baseline
from test.assistant_model.action_plan_generation import get_possible_action_plans, get_challenges
from test.config.config import (
    USER, DATA_FOLDER, TIMESTEP, POSITION, SIGMA_POSITION_TRANSITION,
    VELOCITY, GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER,
    N_SAMPLES, CHILD_MODELS_N_COMPONENTS, LOG_PRIOR,
    N_RESTART, N_EPISODES, CHALLENGE_WINDOW, OFFER_WINDOW, N_CHALLENGE, FIRST_CHALLENGE_OFFER,
    SEED_GENERATIVE_MODEL, SEED_RUN, SEED_ASSISTANT, GAMMA
)


def main():

    challenges = get_challenges(
        time_zone=TIME_ZONE,
        challenge_window=CHALLENGE_WINDOW,
        offer_window=OFFER_WINDOW,
        n_challenges_per_day=N_CHALLENGE,
        start_time=FIRST_CHALLENGE_OFFER
    )

    action_plans = get_possible_action_plans(challenges=challenges, timestep=TIMESTEP)
    # print(f"Generated {len(action_plans)} action plans")

    transition_velocity_atvv, transition_position_pvp = generative_model(
        action_plans=action_plans,
        user=USER, data_path=DATA_FOLDER,
        timestep=TIMESTEP, n_samples=N_SAMPLES,
        child_models_n_components=CHILD_MODELS_N_COMPONENTS,
        velocity=VELOCITY, pseudo_count_jitter=GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
        position=POSITION, sigma_transition_position=SIGMA_POSITION_TRANSITION,
        seed=SEED_GENERATIVE_MODEL
    )
    # np.save("action_plans.npy", action_plans)
    # np.save("timestep.npy", TIMESTEP)
    # np.save("velocity.npy", VELOCITY)
    # np.save("position.npy", POSITION)
    # np.save("transition_velocity_atvv.npy", transition_velocity_atvv)
    # np.save("transition_position_pvp.npy", transition_position_pvp)

    # Run the baseline
    runs = baseline.run(
        action_plans=action_plans,
        transition_velocity_atvv=transition_velocity_atvv,
        transition_position_pvp=transition_position_pvp,
        timestep=TIMESTEP, position=POSITION, velocity=VELOCITY,
        n_restart=N_RESTART,
        seed=SEED_RUN
    )
    # pos_when_ap0 = runs[0]["position"]
    # n_restart, len_pos = pos_when_ap0.shape
    # for i in range(n_restart):
    #     print(f"Restart {i}:")
    #     for j in range(len_pos):
    #         print(f"Time {j}: a={action_plans[0][j]} pos={pos_when_ap0[i, j]}")
    # Compute performance of each action plan
    performance = [
        np.mean(r["position"][:, -1]) for r in runs
    ]
    # Sort action plans by performance
    idx = np.argsort(performance)[::-1]
    sorted_action_plans = action_plans[idx]
    for i, ap in enumerate(sorted_action_plans):
        print(f"#{i}: AP{idx[i]} {ap} with performance {performance[idx[i]]:.2f}")
    # Plot the runs
    plot.runs(*runs)
    # print("running the assistant model")
    af_run = test_assistant_model(
        action_plans=action_plans,
        log_prior_position=LOG_PRIOR,
        gamma=GAMMA,
        n_episodes=N_EPISODES,
        alpha_jitter=ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER,
        position=POSITION,
        velocity=VELOCITY,
        transition_velocity_atvv=transition_velocity_atvv,
        transition_position_pvp=transition_position_pvp,
        timestep=TIMESTEP,
        n_restart=N_RESTART,
        seed_run=SEED_RUN,
        seed_assistant=SEED_ASSISTANT
    )
    # Record the run
    runs.append(af_run)
    # Plot the runs
    plot.runs(*runs)
    # plot.plot_af(af_run)


if __name__ == "__main__":

    main()
