import numpy as np
from tqdm import tqdm

from .action_plan_selection import select_action_plan, normalize_last_dim


def test_assistant_model(
        position,
        velocity,
        timestep,
        n_episodes,
        n_restart,
        alpha_jitter,
        transition_velocity_atvv,
        transition_position_pvp,
        action_plans,
        log_prior_position,
        gamma,
        seed_assistant,
        seed_run
):
    # Seed for reproducibility
    rng = np.random.default_rng(seed=seed_run)
    # Initialize history
    hist_err = np.zeros((n_restart, n_episodes*(timestep.size-1)))
    hist_pos = np.zeros((n_restart, n_episodes, timestep.size-1))
    hist_vel = np.zeros_like(hist_pos)
    hist_epistemic = np.zeros((n_restart, n_episodes, len(action_plans)))
    hist_pragmatic = np.zeros_like(hist_epistemic)
    # Find initial position and velocity
    init_pos_idx = np.absolute(position).argmin()  # Something close to 0
    init_v_idx = np.absolute(velocity).argmin()    # Something close to 0
    # Number of actions
    n_action = np.unique(action_plans).size
    # Run the model
    for sample in range(n_restart):
        print("-"*80)
        print(f"sample {sample}")
        print("-"*80)
        # Initialize alpha
        alpha_atvv = np.zeros((n_action, timestep.size-1, velocity.size, velocity.size)) + alpha_jitter
        epoch = 0
        for ep_idx in range(n_episodes):
            # Select action plan
            action_plan_idx, pr_value, ep_value = select_action_plan(
                log_prior_position=log_prior_position,
                gamma=gamma,
                position=position,
                velocity=velocity,
                alpha_atvv=alpha_atvv,
                transition_position_pvp=transition_position_pvp,
                v_idx=init_v_idx,
                pos_idx=init_pos_idx,
                t_idx=0,
                action_plans=action_plans,
                seed=seed_assistant
            )
            # Record values
            hist_epistemic[sample, ep_idx] = ep_value
            hist_pragmatic[sample, ep_idx] = pr_value
            # Select the best action plan ('policy')
            policy = action_plans[action_plan_idx]
            print(f"Sample {sample} - Episode {ep_idx} - Policy {action_plan_idx}")
            # Run the policy
            v_idx = init_v_idx
            pos_idx = init_pos_idx
            # Going through the policy
            for t_idx in range(timestep.size - 1):
                # Pick new action
                a = policy[t_idx]
                # Draw new velocity
                new_v_idx = rng.choice(
                    np.arange(velocity.size),
                    p=transition_velocity_atvv[a, t_idx, v_idx, :])
                # Update pseudo-counts
                alpha_atvv[a, t_idx, v_idx, new_v_idx] += 1
                # Update velocity and position
                v_idx = new_v_idx
                pos_idx = rng.choice(
                    position.size,
                    p=transition_position_pvp[pos_idx, v_idx, :]
                )
                # Record position and velocity
                hist_pos[sample, ep_idx, t_idx] = position[pos_idx]
                hist_vel[sample, ep_idx, t_idx] = velocity[v_idx]
                # Log
                error = np.mean(np.absolute(transition_velocity_atvv - normalize_last_dim(alpha_atvv)))
                hist_err[sample, epoch] = error
            epoch += 1
    return {
            "gamma": gamma,
            "policy": "af",
            "error": hist_err,
            "epistemic": hist_epistemic,
            "pragmatic": hist_pragmatic,
            "position": hist_pos[:, :, :],
            "velocity": hist_vel[:, :, :]
    }
