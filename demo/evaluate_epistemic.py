import numpy as np
import itertools
import os
import pickle
from tqdm import tqdm

from demo.plot.plot import plot_error
from model.transition import compute_transition_position_matrix, compute_transition_velocity_matrix
from model.baseline import run_baseline_epistemic
from model.helpers import compute_q, compute_sum_kl_div_dirichlet


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
    
    for sample in tqdm(range(n_run), leave=False, position=0):
        # Initialize alpha
        alpha_tapvv = (
            np.zeros((n_timestep, n_action, n_position, n_velocity, n_velocity))
            + np.finfo(np.float64).eps
        )
        if sample == 0:
            # Log error
            error = np.mean((transition_velocity_tapvv - compute_q(alpha_tapvv)) ** 2)

            print(f"Initial error {error:.6f}")

        epoch = 0
        for ep_idx in tqdm(range(n_episode_per_run), leave=False, position=1):
            np.random.seed(12334 + ep_idx + sample * 123)

            p_idx = np.absolute(position).argmin()  # Something close to 0
            v_idx = np.absolute(velocity).argmin()  # Something close to 0

            # random_action_plan = np.random.randint(n_action, size=n_timestep)
            # print("random action plan", random_action_plan)

            for t_idx, t in enumerate(timestep):
                h = min(horizon, n_timestep - t_idx)
                action_plan = list(itertools.product(range(n_action), repeat=h))
                # print(action_plan)

                # Initialize action plan values
                epistemic = np.zeros(len(action_plan))

                #TODO: Need to sample instead of using the expectation
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
                        to_add = np.outer(qp, qv)[..., None] * q[rollout_t_index, a, :, :, :]
                        alpha_tapvv_rollout[rollout_t_index, a, :, :, :] += to_add
                        # Update beliefs about the velocity and position
                        # [IMPORTANT] => do it after updating beliefs about the transitions
                        qv = to_add.sum(axis=(0, 1))  # Same as: qv = qp @ (qv @ q[rollout_t_index, a, :, :, :])
                        qp = qp @ (qv @ transition_position_pvp)

                    # Choose the best action plan
                    epistemic[ap_index] = compute_sum_kl_div_dirichlet(
                        alpha_rollout=alpha_tapvv_rollout,
                        alpha=alpha_tapvv)

                    # print("ap", action_plan[ap_index])
                    # print(epistemic[ap_index])

                # # Choose an action plan
                def softmax(x, temperature=1.0):
                    x = x / temperature
                    e_x = np.exp(x - np.max(x))
                    return e_x / e_x.sum(axis=0)
                selected_action_plan_index = np.random.choice(
                    len(action_plan),
                    p=softmax(epistemic,
                              temperature=1000))
                # np.random.choice(
                #    np.arange(len(action_plan))[epistemic == epistemic.max()]
                # )
                # np.random.choice(
                #     np.arange(len(action_plan))[epistemic == epistemic.max()]
                # )
                a = action_plan[selected_action_plan_index][0]
                # a = np.random.randint(n_action) # random_action_plan[t_idx]

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
        print("run", sample, f"error {hist_err[sample, -1]:.6f}")
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

    n_episode_per_run = 200
    n_run = 20

    bkp_baseline = "bkp/epistemic_baseline.pkl"

    if not os.path.exists(bkp_baseline):
        os.makedirs(os.path.dirname(bkp_baseline), exist_ok=True)
        r_baseline = run_baseline_epistemic(
            timestep=timestep,
            position=position,
            velocity=velocity,
            action=action,
            n_run=n_run,
            n_episode_per_run=n_episode_per_run,
            friction_factor=friction_factor,
            seed_transition_velocity=seed_transition_velocity,
            n_sample_transition_velocity=n_sample_transition_velocity,
        )
        with open(bkp_baseline, "wb") as f:
            pickle.dump(r_baseline, f)
    else:
        with open(bkp_baseline, "rb") as f:
            r_baseline = pickle.load(f)

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

    plot_error([r_baseline, r_act_inf])


if __name__ == "__main__":

    main()
