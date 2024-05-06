import numpy as np


def run(
    action_plans,
    transition,
    timestep,
    position,
    n_restart,
    seed
):
    # np.save("transition_velocity_atvv.npy", transition_velocity_atvv)
    # np.save("transition_position_pvp.npy", transition_position_pvp)
    rng = np.random.default_rng(seed=seed)
    n_timestep, n_position = timestep.size, position.size
    runs = []
    for i_pol, policy in enumerate(action_plans):
        hist_pos = np.zeros((n_restart, timestep.size))
        hist_vel = np.zeros_like(hist_pos)
        for sample in range(n_restart):
            pos_idx = np.absolute(position).argmin()  # Something close to 0
            for t_idx in range(timestep.size):
                a = policy[t_idx]
                pos_idx = rng.choice(
                    np.arange(n_position),
                    p=transition[a, t_idx, pos_idx, :],
                )
                hist_pos[sample, t_idx] = position[pos_idx]
        policy_name = f"{i_pol}"
        runs.append({"policy": policy_name, "position": hist_pos, "velocity": hist_vel})
    return runs
