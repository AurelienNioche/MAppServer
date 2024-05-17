import numpy as np


def run(
    action_plans,
    transition,
    timestep,
    position,
    n_restart,
    seed
):
    rng = np.random.default_rng(seed=seed)
    runs = []
    for i_pol, policy in enumerate(action_plans):
        hist_pos = np.zeros((n_restart, timestep.size+1))
        for sample in range(n_restart):
            pos_idx = np.absolute(position).argmin()  # Something close to 0
            for t_idx in range(timestep.size):
                # Record where we are at the start of the timestep
                hist_pos[sample, t_idx] = position[pos_idx]
                # Select action
                a = policy[t_idx]
                # Select new position
                pos_idx = rng.choice(
                    np.arange(position.size),
                    p=transition[a, t_idx, pos_idx, :],
                )
            # Add the last position
            hist_pos[sample, -1] = position[pos_idx]
        # Record the run
        policy_name = f"{i_pol}"
        runs.append({"policy": policy_name, "position": hist_pos})
    return runs
