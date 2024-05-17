import numpy as np
from MAppServer.settings import (
    LOG_AT_EACH_TIMESTEP,
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER,
    LOG_ASSISTANT_MODEL,
    LOG_WARNING_NAN,
    POSITION,
    LOG_PRIOR,
    GAMMA,
    SEED_ASSISTANT
)
from core.activity import initialize_pseudo_counts


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def make_a_step(
        t_idx,
        policy,
        pos_idx,
        transition,
        rng
):
    # print("rng state", rng.bit_generator.state['state']['state'])
    # Pick new action
    action = policy[t_idx]
    # Draw position
    new_pos_idx = rng.choice(
        POSITION.size,
        p=transition[action, t_idx, pos_idx, :]
    )
    if LOG_AT_EACH_TIMESTEP:
        # n_steps {POSITION[pos_idx]}
        print(f"t {t_idx:02} a {action} p {pos_idx:02} -> {new_pos_idx:02}") # rng state {rng.bit_generator.state['state']['state']}")

    return action, new_pos_idx


def compute_number_of_observations(pseudo_counts):
    return int(np.sum(pseudo_counts)
               - initialize_pseudo_counts(ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER).sum())

from MAppServer.settings import TIMESTEP
def select_action_plan(
        pseudo_counts: np.ndarray,
        pos_idx: int,
        t_idx: int,
        action_plans: np.ndarray
):
    """Select the best action to take"""
    # Set the seed
    # TODO: Check if this is the correct way to set the seed
    # log_str = ""
    rng = np.random.default_rng(SEED_ASSISTANT)
    if LOG_ASSISTANT_MODEL:
        n_obs = compute_number_of_observations(pseudo_counts)
        # rng state {rng.bit_generator.state['state']['state']}"
        print(f"Assistant: t_idx={t_idx:02} pos_idx={pos_idx:02} n obs {n_obs:02}")
        # if n_obs == 24:  # 144
        #     print("action plans")
        #     print(action_plans)
        #     print("peseudo counts")
        #     for action in range(2):
        #         for ts in range(TIMESTEP.size):
        #             for pos in range(POSITION.size):
        #                 print("action", action, "ts", ts, "pos", pos, pseudo_counts[action, ts, pos])
    # Get the dimensions of the action plans
    n_action_plan, h = action_plans.shape
    # Initialize action plan values
    pragmatic = np.zeros(n_action_plan)
    epistemic = np.zeros(n_action_plan)
    # Initialize belief about the velocity transition
    alpha_t = pseudo_counts.copy()
    # Normalize the last dimension
    qt = normalize_last_dim(alpha_t)
    # Compute value of each action plan
    for ap_index, ap in enumerate(action_plans):
        # For history of beliefs
        qps = np.zeros((h, POSITION.size))
        # We know where we start
        qp = np.zeros(POSITION.size)
        qp[pos_idx] = 1.
        for h_idx in range(h):
            previous_qp = qp.copy()
            a = ap[h_idx]
            rollout_t_index = t_idx + h_idx
            _qt = qt[a, rollout_t_index]
            _alpha = alpha_t[a, rollout_t_index]
            _sums = np.sum(_alpha, axis=-1, keepdims=True)
            qp = qp @ _qt
            # Handle specific case where the pseudo count is 0
            make_sense = _alpha > 0
            _alpha[_alpha == 0] = 1
            w = 1/(2*_alpha) - 1/(2*_sums)
            w *= make_sense.astype(float)
            v_model = (previous_qp@w)@qp
            epistemic[ap_index] += v_model
            # record the values
            qps[h_idx] = qp
        pragmatic[ap_index] = np.sum(qps @ LOG_PRIOR)
    # Choose the best action plan
    # If all values are nan, return a random action plan
    if np.isnan(pragmatic).all() and np.isnan(epistemic).all():
        if LOG_WARNING_NAN:
            print("All values are nan")
        efe = np.ones(n_action_plan)
    # If one of the values is nan, return the other
    elif np.isnan(pragmatic).all():
        if LOG_WARNING_NAN:
            print("Pragmatic values are all nan")
        efe = epistemic
    elif np.isnan(epistemic).all():
        if LOG_WARNING_NAN:
            print("Epistemic values are all nan")
        efe = pragmatic
    # Otherwise, compute the Expected Free Energy
    else:
        efe = GAMMA * epistemic + pragmatic
    close_to_max_efe = np.isclose(efe, efe.max())
    idx_close_to_max = np.where(close_to_max_efe)[0]
    best_action_plan_index = rng.choice(idx_close_to_max)
    if LOG_ASSISTANT_MODEL:
        print("Selected action plan", best_action_plan_index)
        print("-"*80)
    return best_action_plan_index, pragmatic, epistemic
