import numpy as np


def run(
    action_plans,
    transition_velocity_atvv,
    transition_position_pvp,
    timestep,
    position,
    velocity,
    n_restart
):
    n_timestep, n_velocity, n_position = timestep.size, velocity.size, position.size

    runs = []

    for policy in action_plans:

        hist_pos = np.zeros((n_restart, timestep.size - 1))
        hist_vel = np.zeros_like(hist_pos)

        for sample in range(n_restart):
            pos_idx = np.absolute(position).argmin()  # Something close to 0
            v_idx = np.absolute(velocity).argmin()  # Something close to 0

            np.random.seed(123 + sample * 123)

            for t_idx in range(timestep.size - 1):
                a = policy[t_idx]

                v_idx = np.random.choice(
                    np.arange(n_velocity),
                    p=transition_velocity_atvv[a, t_idx, v_idx, :],
                )  # = np.average(velocity, weights=p_)
                pos_idx = np.random.choice(
                    np.arange(n_position), p=transition_position_pvp[pos_idx, v_idx, :]
                )

                hist_pos[sample, t_idx] = position[pos_idx]
                hist_vel[sample, t_idx] = velocity[v_idx]

        policy_name = f"{list(policy).index(1)}"
        runs.append({"policy": policy_name, "position": hist_pos, "velocity": hist_vel})
    return runs
