import numpy as np
from tqdm import tqdm

from MAppServer.settings import (
    INIT_POS_IDX,
    LOG_AT_EACH_EPISODE,
    LOG_PSEUDO_COUNT_UPDATE,
    USE_PROGRESS_BAR,
    TIMESTEP,
    POSITION,
    GAMMA,
    N_DAY,
    TEST_N_RESTART,
    TEST_SEED_RUN,
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER
)
from core.action_plan_selection import select_action_plan, normalize_last_dim, make_a_step
from core.activity import initialize_pseudo_counts


def test_assistant_model(
        transition,
        action_plans
):
    # Seed for reproducibility
    rng = np.random.default_rng(seed=TEST_SEED_RUN)
    # Initialize history
    hist_err = np.zeros((TEST_N_RESTART, N_DAY*TIMESTEP.size))
    hist_pos = np.zeros((TEST_N_RESTART, N_DAY, TIMESTEP.size+1))
    hist_epistemic = np.zeros((TEST_N_RESTART, N_DAY, len(action_plans)))
    hist_pragmatic = np.zeros_like(hist_epistemic)
    # Run the model
    for sample in range(TEST_N_RESTART):
        # Initialize alpha
        pseudo_counts = initialize_pseudo_counts(jitter=ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER)
        epoch = 0
        _iter = range(N_DAY)
        if USE_PROGRESS_BAR:
            _iter = tqdm(_iter)
        for ep_idx in _iter:
            # Select action plan
            action_plan_idx, pr_value, ep_value = select_action_plan(
                pseudo_counts=pseudo_counts,
                pos_idx=INIT_POS_IDX,
                t_idx=0,
                action_plans=action_plans
            )
            # Record values
            hist_epistemic[sample, ep_idx] = ep_value
            hist_pragmatic[sample, ep_idx] = pr_value
            # Select the best action plan ('policy')
            policy = action_plans[action_plan_idx]
            if LOG_AT_EACH_EPISODE:
                print(f"restart #{sample} - episode #{ep_idx} - policy #{action_plan_idx}")
                print("-"*80)
            # Run the policy
            pos_idx = INIT_POS_IDX
            # Going through the policy
            for t_idx in range(TIMESTEP.size):
                # Record position and velocity
                hist_pos[sample, ep_idx, t_idx] = POSITION[pos_idx]
                # Make a step
                action, new_pos_idx = make_a_step(
                    policy=policy,
                    t_idx=t_idx,
                    pos_idx=pos_idx,
                    transition=transition,
                    rng=rng
                )
                # Update pseudo-counts
                pseudo_counts[action, t_idx, pos_idx, new_pos_idx] += 1
                if LOG_PSEUDO_COUNT_UPDATE:
                    print("UPDATE PSEUDO-COUNTS", "t_idx", t_idx, "action", action, "day", ep_idx, "pos_idx", pos_idx, "new_pos_idx", new_pos_idx)
                    # print("pseudo_counts sum", int(pseudo_counts.sum() - pseudo_counts.size * alpha_jitter))
                # Replace old value with the new value
                pos_idx = new_pos_idx
                # Log
                error = np.mean(np.absolute(transition - normalize_last_dim(pseudo_counts)))
                hist_err[sample, epoch] = error
            # Record the last position
            hist_pos[sample, ep_idx, -1] = POSITION[pos_idx]
            epoch += 1
    return {
            "gamma": GAMMA,
            "policy": "af",
            "error": hist_err,
            "epistemic": hist_epistemic,
            "pragmatic": hist_pragmatic,
            "position": hist_pos[:, :, :]
    }
