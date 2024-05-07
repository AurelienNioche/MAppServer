import numpy as np
from tqdm import tqdm

from test.config.config import (
    INIT_POS_IDX, LOG_AT_EACH_EPISODE, LOG_PSEUDO_COUNT_UPDATE
)
from .action_plan_selection import select_action_plan, normalize_last_dim, make_a_step


def test_assistant_model(
        position,
        timestep,
        n_episodes,
        n_restart,
        alpha_jitter,
        transition,
        action_plans,
        log_prior_position,
        gamma,
        seed_assistant,
        seed_run
):
    # Seed for reproducibility
    rng = np.random.default_rng(seed=seed_run)
    # Initialize history
    hist_err = np.zeros((n_restart, n_episodes*timestep.size))
    hist_pos = np.zeros((n_restart, n_episodes, timestep.size+1))
    hist_epistemic = np.zeros((n_restart, n_episodes, len(action_plans)))
    hist_pragmatic = np.zeros_like(hist_epistemic)
    # Number of actions
    n_action = np.unique(action_plans).size
    # Run the model
    for sample in range(n_restart):
        # print("-"*80)
        # print(f"sample {sample}")
        # print("-"*80)
        # Initialize alpha
        pseudo_counts = np.zeros((n_action, timestep.size, position.size, position.size))
        # Add jitter
        # TODO: only in the upper triangle
        pseudo_counts += alpha_jitter
        epoch = 0
        for ep_idx in tqdm(range(n_episodes)):
            # Select action plan
            action_plan_idx, pr_value, ep_value = select_action_plan(
                log_prior_position=log_prior_position,
                gamma=gamma,
                position=position,
                pseudo_counts=pseudo_counts,
                pos_idx=INIT_POS_IDX,
                t_idx=0,
                action_plans=action_plans,
                seed=seed_assistant
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
            for t_idx in range(timestep.size):
                # Record position and velocity
                hist_pos[sample, ep_idx, t_idx] = position[pos_idx]
                # Make a step
                action, new_pos_idx = make_a_step(
                    policy=policy,
                    t_idx=t_idx,
                    pos_idx=pos_idx,
                    position=position,
                    transition=transition,
                    rng=rng
                )
                # Update pseudo-counts
                pseudo_counts[action, t_idx, pos_idx, new_pos_idx] += 1
                print("pseudo_counts sum", int(pseudo_counts.sum() - pseudo_counts.size * alpha_jitter))
                # Replace old value with the new value
                pos_idx = new_pos_idx
                # Log
                error = np.mean(np.absolute(transition - normalize_last_dim(pseudo_counts)))
                hist_err[sample, epoch] = error
            # Record the last position
            hist_pos[sample, ep_idx, -1] = position[pos_idx]
            epoch += 1
    return {
            "gamma": gamma,
            "policy": "af",
            "error": hist_err,
            "epistemic": hist_epistemic,
            "pragmatic": hist_pragmatic,
            "position": hist_pos[:, :, :]
    }
