import numpy as np
import itertools
from multiprocessing import Pool, cpu_count, Value
import time

import functools

from demo.model.helpers import kl_div_dirichlet, compute_q


def run_sample(sample,
               n_episode,
               position, velocity, timestep, horizon,
               transition_velocity_tapvv,
               transition_position_pvp):

    n_timestep, n_action, n_position, n_velocity, _ = transition_velocity_tapvv.shape

    # Initialize alpha
    alpha_tapvv = (
        np.zeros((n_timestep, n_action, n_position, n_velocity, n_velocity))
        + np.finfo(np.float64).eps
    )

    # Log error
    error = np.mean((transition_velocity_tapvv - compute_q(alpha_tapvv)) ** 2)
    if sample == 0:
        print(f"Initial error {error:.2f}")

    hist_a = []
    hist_err = []
    epoch = 0

    # with tqdm(total=n_episode) as pbar:
    for ep_idx in range(n_episode):
        np.random.seed(12334 + ep_idx + sample * 123)

        p_idx = np.absolute(position).argmin()  # Something close to 0
        v_idx = np.absolute(velocity).argmin()  # Something close to 0

        for t_idx, t in enumerate(timestep):
            h = min(horizon, n_timestep - t_idx)
            action_plan = list(itertools.product(range(n_action), repeat=h))

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

                    # Update beliefs about the transition model     = > (N, 1)
                    qv_tiled = np.tile(qv, (n_position, 1))[:, :, np.newaxis]
                    qp_tiled = np.tile(qp, (n_velocity, 1)).T[:, :, np.newaxis]
                    to_add = qv_tiled * qp_tiled * q[rollout_t_index, a, :, :, :]
                    alpha_tapvv_rollout[rollout_t_index, a, :, :, :] += to_add

                    # Update beliefs about the velocity and position
                    # [IMPORTANT] => do it after updating beliefs about the transitions
                    qv = qp @ (qv @ q[rollout_t_index, a, :, :, :])
                    qp = qp @ (qv @ transition_position_pvp)

                    # Choose the best action plan
                epistemic[ap_index] = kl_div_dirichlet(
                    alpha_tapvv_rollout, alpha_tapvv
                )

            # Choose the best action plan
            best_action_plan_index = np.random.choice(
                np.arange(len(action_plan))[epistemic == epistemic.max()]
            )
            a = action_plan[best_action_plan_index][0]

            new_v_index = np.random.choice(
                n_velocity, p=transition_velocity_tapvv[t_idx, a, p_idx, v_idx, :]
            )

            # https://blog.jakuba.net/posterior-predictive-distribution-for-the-dirichlet-categorical-model/
            alpha_tapvv[t_idx, a, p_idx, v_idx, new_v_index] += 1

            # Update velocity and position
            v_idx = new_v_index
            p_idx = np.random.choice(
                n_position, p=transition_position_pvp[p_idx, v_idx, :]
            )

            # Log
            error = np.mean((transition_velocity_tapvv - q_transition_velocity(alpha_tapvv))**2)
            hist_err.append(error)
            hist_a.append(a)
            epoch += 1

            with shared_counter.get_lock():
                shared_counter.value += 1

            # pbar.set_postfix(error=f"{error:.6f}")
            # pbar.update(1)

    print(f"[Sample {sample}] Error after {epoch} epochs: {error:.2f}")

    print(
        f"[Sample {sample}] Freq choose action 0: {100*hist_a.count(0)/len(hist_a):.2f}%"
    )
    return hist_err


def init_globals(counter):
    global shared_counter
    shared_counter = counter


def wrapper(kwargs):
    return run_sample(**kwargs)


def run_task(pbar, n_episode, n_sample,
             transition_velocity_tapvv, transition_position_pvp,
             position, velocity, timestep, horizon):

    n_timestep, n_action, n_position, n_velocity, _ = transition_velocity_tapvv.shape
    hist_err = np.zeros((n_sample, n_episode * n_timestep))

    num_processes = cpu_count()
    counter = Value("i", 0)
    with Pool(num_processes, initializer=init_globals, initargs=(counter,)) as p:
        result = p.map_async(functools.partial(
                    run_sample,
                    n_episode=n_episode,
                    transition_velocity_tapvv=transition_velocity_tapvv,
                    transition_position_pvp=transition_position_pvp,
                    position=position,
                    velocity=velocity,
                    timestep=timestep,
                    horizon=horizon,
                ), range(n_sample))

        while not result.ready():
            # pbar.n = counter.value
            # pbar.refresh()
            time.sleep(0.1)
            pbar.update(counter.value - pbar.n)
            # pbar.n = counter.value
            # pbar.refresh()
        r = result.get()
        for i, result in enumerate(r):
            hist_err[i] = result

    return hist_err
