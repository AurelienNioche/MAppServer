import numpy as np
import itertools

from demo.plot.plot import plot_runs
from model.preference import compute_log_prior
from model.transition import compute_transition_position_matrix, compute_transition_velocity_matrix
from model.baseline import run_baseline_pragmatic


def evaluate_pragmatic(
        timestep, position, velocity, action, friction_factor,
        n_run, n_sample_transition_velocity, seed_transition_velocity):

    n_timestep = len(timestep)
    n_velocity = len(velocity)
    n_position = len(position)
    n_action = len(action)
    horizon = n_timestep

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

    # Log prior
    log_prior = compute_log_prior(position)
    
    # For logs
    hist_pos, hist_vel = np.zeros((n_run, n_timestep)), np.zeros((n_run, n_timestep))
    
    # For each sample...
    for sample in range(n_run):
        p_idx = np.absolute(position).argmin()  # Something close to 0
        v_idx = np.absolute(velocity).argmin()  # Something close to 0
    
        np.random.seed(123 + sample * 123)
    
        for t_idx in range(n_timestep):
            h = min(horizon, n_timestep - t_idx)
            action_plan = list(itertools.product(range(n_action), repeat=h))
    
            pragmatic = np.zeros(len(action_plan))
            for ap_index, ap in enumerate(action_plan):
                qvs = np.zeros((h, n_velocity))
                qps = np.zeros((h, n_position))
    
                qv = np.zeros(n_velocity)
                qv[v_idx] = 1.0
                qp = np.zeros(n_position)
                qp[p_idx] = 1.0
    
                for h_idx in range(h):
                    a = ap[h_idx]
                    qv = qp @ (qv @ transition_velocity_tapvv[t_idx + h_idx, a, :, :, :])
                    qp = qp @ (qv @ transition_position_pvp)
                    qvs[h_idx] = qv
                    qps[h_idx] = qp
    
                pragmatic[ap_index] = np.sum(qps @ log_prior)
    
            a = action_plan[np.argmax(pragmatic)][0]
    
            v_idx = np.random.choice(
                np.arange(n_velocity),
                p=transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :],
            )
            p_idx = np.random.choice(
                np.arange(n_position), p=transition_position_pvp[p_idx, v_idx, :]
            )
    
            hist_pos[sample, t_idx] = position[p_idx]
            hist_vel[sample, t_idx] = velocity[v_idx]

    return {"policy": "act-inf", "position": hist_pos, "velocity": hist_vel}


def main():

    n_timestep = 6
    n_velocity = 20
    n_action = 2
    n_position = 50

    timestep = np.linspace(0, 1.0, n_timestep)
    position = np.linspace(0, 2.0, n_position)
    velocity = np.linspace(0., 3.0, n_velocity)
    action = np.arange(n_action)

    friction_factor = 0.5
    n_sample_transition_velocity = 300
    seed_transition_velocity = 123
    n_run = 10

    results = run_baseline_pragmatic(
        timestep=timestep,
        position=position,
        velocity=velocity,
        action=action,
        friction_factor=friction_factor,
        n_sample_transition_velocity=n_sample_transition_velocity,
        seed_transition_velocity=seed_transition_velocity,
        n_run=n_run,
    )
    r = evaluate_pragmatic(
        timestep=timestep,
        position=position,
        velocity=velocity,
        action=action,
        friction_factor=friction_factor,
        n_sample_transition_velocity = n_sample_transition_velocity,
        seed_transition_velocity=seed_transition_velocity,
        n_run=n_run)
    results.append(r)
    plot_runs(results)


if __name__ == "__main__":

    main()
