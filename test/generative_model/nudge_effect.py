import numpy as np

from MAppServer.settings import LOC_NUDGE_EFFECT, SCALE_NUDGE_EFFECT, TIMESTEP


def generate_nudge_effect(action_plans, seed):
    rng = np.random.default_rng(seed=seed)
    best_action_plan = rng.integers(action_plans.shape[0])
    effect = action_plans[best_action_plan] * rng.normal(
        LOC_NUDGE_EFFECT, SCALE_NUDGE_EFFECT,
        size=TIMESTEP.size)
    effect = effect.astype(int)
    return effect
