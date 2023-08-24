import numpy as np
import itertools

from demo.plot.plot import plot_error
from model.transition import compute_transition_position_matrix, compute_transition_velocity_matrix
from model.baseline import run_baseline_epistemic
from model.helpers import kl_div_dirichlet, compute_q, compute_sum_kl_div_dirichlet


def evaluate_epistemic(
        timestep, position, velocity,
        friction_factor, action,
        n_episode_per_run, n_run,
        n_sample_transition_velocity,
        seed_transition_velocity):

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

    horizon = len(timestep)

    n_timestep, n_action, n_position, n_velocity, _ = transition_velocity_tapvv.shape

    hist_err = np.zeros((n_run, n_episode_per_run * n_timestep))
    
    for sample in range(n_run):
        # Initialize alpha
        alpha_tapvv = (
            np.zeros((n_timestep, n_action, n_position, n_velocity, n_velocity))
            + np.finfo(np.float64).eps
        )
        if sample == 0:
            # Log error
            error = np.mean((transition_velocity_tapvv - compute_q(alpha_tapvv)) ** 2)

            print(f"Initial error {error:.2f}")

        epoch = 0
        for ep_idx in range(n_episode_per_run):
            np.random.seed(12334 + ep_idx + sample * 123)

            p_idx = np.absolute(position).argmin()  # Something close to 0
            v_idx = np.absolute(velocity).argmin()  # Something close to 0

            random_action_plan = np.random.randint(n_action, size=n_timestep)
            print("random action plan", random_action_plan)

            for t_idx, t in enumerate(timestep):
                h = min(horizon, n_timestep - t_idx)
                action_plan = list(itertools.product(range(n_action), repeat=h))
                print(action_plan)

                # Initialize action plan values
                epistemic = np.zeros(len(action_plan))

                q = compute_q(alpha_tapvv)

                # Compute value of each action plan
                for ap_index, ap in enumerate(action_plan):
                    # Initialize the rollout model (= counts)
                    alpha_tapvv_rollout = alpha_tapvv.copy()

                    qv = np.zeros(n_velocity)
                    qv[v_idx] = 1.0

                    qp = np.zeros(n_position)
                    qp[p_idx] = 1.0

                    for h_idx, a in enumerate(ap):
                        # Update rollout time index
                        rollout_t_index = t_idx + h_idx

                        # Update beliefs about the transition model
                        qv_tiled = np.expand_dims(np.tile(qv, (n_position, 1)), axis=-1)
                        qp_tiled = np.expand_dims(np.tile(qp, (n_velocity, 1)).T, axis=-1)
                        to_add = qv_tiled * qp_tiled * q[rollout_t_index, a, :, :, :]
                        alpha_tapvv_rollout[rollout_t_index, a, :, :, :] += to_add

                        # Update beliefs about the velocity and position
                        # [IMPORTANT] => do it after updating beliefs about the transitions
                        qv = qp @ (qv @ q[rollout_t_index, a, :, :, :])
                        qp = qp @ (qv @ transition_position_pvp)

                        # Choose the best action plan
                    epistemic[ap_index] = compute_sum_kl_div_dirichlet(alpha_tapvv_rollout=alpha_tapvv_rollout,
                                                                       alpha_tapvv=alpha_tapvv)
                    print("ap", action_plan[ap_index])
                    print(epistemic[ap_index])
                #
                # # Choose the best action plan
                # best_action_plan_index = np.random.choice(
                #     np.arange(len(action_plan))[epistemic == epistemic.max()]
                # )
                # a = np.random.randint(2) #action_plan[best_action_plan_index][0]
                a = random_action_plan[t_idx]

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
                error = np.mean((transition_velocity_tapvv - compute_q(alpha_tapvv))**2)
                hist_err[sample, epoch] = error
                epoch += 1

    return {"policy": "act-inf", "error": hist_err}


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
    seed_transition_velocity = 123
    n_sample_transition_velocity = 200

    n_episode_per_run = 2
    n_run = 1

    # r_baseline = run_baseline_epistemic(
    #     timestep=timestep,
    #     position=position,
    #     velocity=velocity,
    #     action=action,
    #     n_run=n_run,
    #     n_episode_per_run=n_episode_per_run,
    #     friction_factor=friction_factor,
    #     seed_transition_velocity=seed_transition_velocity,
    #     n_sample_transition_velocity=n_sample_transition_velocity,
    # )

    r_act_inf = evaluate_epistemic(
        timestep=timestep,
        position=position,
        velocity=velocity,
        action=action,
        friction_factor=friction_factor,
        n_episode_per_run=n_episode_per_run,
        seed_transition_velocity=seed_transition_velocity,
        n_sample_transition_velocity=n_sample_transition_velocity,
        n_run=n_run)

    plot_error([r_act_inf])


if __name__ == "__main__":

    main()
