import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import numpy as np

from utils import logging
from core.action_plan_generation import get_possible_action_plans, get_challenges
from MAppServer.settings import (
    USER_FOR_GENERATIVE_MODEL,
    DATA_FOLDER,
    TIMESTEP,
    POSITION,
    GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
    N_SAMPLES_FOR_GENERATIVE_MODEL,
    CHILD_MODELS_N_COMPONENTS,
    TEST_N_RESTART,
    TEST_FIRST_CHALLENGE_OFFER,
    SEED_GENERATIVE_MODEL,
    TEST_SEED_RUN
)
from test.generative_model.core import generative_model
from test.plot import plot
from test.run import baseline
from test.run.assistant_model import test_assistant_model

LOGGER = logging.get(__name__)


def main():
    # Generate the challenges
    challenges = get_challenges(start_time=TEST_FIRST_CHALLENGE_OFFER)
    # Generate the action plans
    action_plans = get_possible_action_plans(challenges=challenges)
    # Generate the transition model
    transition = generative_model(
        action_plans=action_plans,
        user=USER_FOR_GENERATIVE_MODEL,
        data_path=DATA_FOLDER,
        n_samples=N_SAMPLES_FOR_GENERATIVE_MODEL,
        child_models_n_components=CHILD_MODELS_N_COMPONENTS,
        pseudo_count_jitter=GENERATIVE_MODEL_PSEUDO_COUNT_JITTER,
        seed=SEED_GENERATIVE_MODEL
    )
    # Run the baseline
    runs = baseline.run(
        action_plans=action_plans,
        transition=transition,
        timestep=TIMESTEP,
        position=POSITION,
        n_restart=TEST_N_RESTART,
        seed=TEST_SEED_RUN
    )
    # Compute performance of each action plan
    performance = [
        np.mean(r["position"][:, -1]) for r in runs
    ]
    # Sort action plans by performance
    idx = np.argsort(performance)[::-1]
    sorted_action_plans = action_plans[idx]
    for i, ap in enumerate(sorted_action_plans):
        LOGGER.info(f"#{i}: AP{idx[i]} {ap} with performance {performance[idx[i]]:.2f}")
    # Plot the runs
    plot.runs(*runs)
    # print("running the assistant model")
    af_run = test_assistant_model(
        action_plans=action_plans,
        transition=transition
    )
    # Record the run
    runs.append(af_run)
    # Plot the runs
    plot.runs(*runs)
    # Plot the day progression
    plot.plot_day_progression(af_run)


if __name__ == "__main__":
    main()
