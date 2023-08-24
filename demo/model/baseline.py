import numpy as np
from . transition import compute_transition_position_matrix, compute_transition_velocity_matrix
from . helpers import compute_q


def run_baseline_pragmatic(
        timestep, position, velocity, action,
        n_run,
        friction_factor,
        n_sample_transition_velocity,
        seed_transition_velocity):

    n_timestep = len(timestep)
    n_velocity = len(velocity)
    n_position = len(position)

    # Transition matrix for position (dimensions: p v p)
    transition_position_pvp = compute_transition_position_matrix(
        timestep=timestep,
        position=position,
        velocity=velocity)

    # Transition matrix for velocity (dimensions: t a p v v)
    transition_velocity_tapvv = compute_transition_velocity_matrix(
        timestep=timestep,
        position=position,
        velocity=velocity,
        action=action,
        n_sample=n_sample_transition_velocity,
        seed=seed_transition_velocity,
        friction_factor=friction_factor)
    
    policies = ["all-one", "all-zero", "random", "max-expected-velocity"]
    results = []

    for policy in policies:
        hist_pos = np.zeros((n_run, n_timestep))
        hist_vel = np.zeros_like(hist_pos)
    
        for sample in range(n_run):
            p_idx = np.absolute(position).argmin()  # Something close to 0
            v_idx = np.absolute(velocity).argmin()  # Something close to 0
    
            np.random.seed(123 + sample * 123)
    
            for t_idx, t in enumerate(timestep):
                if policy == "all-one":
                    a = 1
                elif policy == "all-zero":
                    a = 0
                elif policy == "random":
                    a = np.random.choice([0, 1])
                elif policy == "max-expected-velocity":
                    e_v = np.zeros(2)
                    for a in range(2):
                        e_v[a] = np.average(
                            velocity,
                            weights=transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :],
                        )
                    a = e_v.argmax()
                else:
                    raise ValueError
                tr_vel = transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :]
                # print(t_idx, a, p_idx, v_idx)
                v_idx = np.random.choice(np.arange(n_velocity), p=tr_vel)
                tr_pos = transition_position_pvp[p_idx, v_idx, :]
                p_idx = np.random.choice(np.arange(n_position), p=tr_pos)
    
                hist_pos[sample, t_idx] = position[p_idx]
                hist_vel[sample, t_idx] = velocity[v_idx]

        results.append({
            "policy": policy,
            "position": hist_pos,
            "velocity": hist_vel
        })
    return results


def run_baseline_epistemic(
        timestep,
        position,
        velocity,
        action,
        friction_factor,
        n_episode_per_run,
        n_run,
        seed_transition_velocity,
        n_sample_transition_velocity):

    n_timestep = len(timestep)
    n_velocity = len(velocity)
    n_position = len(position)
    n_action = len(action)

    # Transition matrix for position (dimensions: p v p)
    transition_position_pvp = compute_transition_position_matrix(
        timestep=timestep,
        position=position,
        velocity=velocity)

    # Transition matrix for velocity (dimensions: t a p v v)
    transition_velocity_tapvv = compute_transition_velocity_matrix(
        timestep=timestep,
        position=position,
        velocity=velocity,
        action=action,
        n_sample=n_sample_transition_velocity,
        seed=seed_transition_velocity,
        friction_factor=friction_factor)

    hist_err = np.zeros((n_run, n_episode_per_run * n_timestep))
    
    for sample in range(n_run):
        alpha_tapvv = (
            np.zeros((n_timestep, n_action, n_position, n_velocity, n_velocity))
            + np.finfo(np.float64).eps
        )
    
        if sample == 0:
            error = np.mean(
                (transition_velocity_tapvv - compute_q(alpha_tapvv)) ** 2
            )
            print(f"Initial error {error:.2f}")
    
        epoch = 0
        for ep_idx in range(n_episode_per_run):
            np.random.seed(12334 + ep_idx + sample * 123)
    
            p_idx = np.absolute(position).argmin()  # Something close to 0
            v_idx = np.absolute(velocity).argmin()  # Something close to 0
    
            action_plan = np.random.randint(n_action, size=n_timestep)
    
            for t_idx, t in enumerate(timestep):
                # Pick new action
                a = action_plan[t_idx]

                # Update velocity
                tr_vel = transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :]
                new_v_index = np.random.choice(np.arange(n_velocity), p=tr_vel)
    
                # Update alpha
                # https://blog.jakuba.net/posterior-predictive-distribution-for-the-dirichlet-categorical-model/
                alpha_tapvv[t_idx, a, p_idx, v_idx, new_v_index] += 1
    
                # Update velocity and position
                v_idx = new_v_index
                tr_pos = transition_position_pvp[p_idx, v_idx, :]
                p_idx = np.random.choice(np.arange(n_position), p=tr_pos)
    
                # Log
                error = np.mean(
                    (transition_velocity_tapvv - compute_q(alpha_tapvv)) ** 2
                )
                # print(error)
                hist_err[sample, epoch] = error
                epoch += 1
    
        print(f"[Sample {sample}] Error after {epoch} epochs {error:.6f}")
    
    return {"policy": "random", "error": hist_err}
