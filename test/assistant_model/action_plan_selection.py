import numpy as np
from test.config.config import LOG_AT_EACH_TIMESTEP, \
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER, LOG_ASSISTANT_MODEL, \
    LOG_WARNING_NAN


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def make_a_step(
        t_idx,
        policy,
        pos_idx,
        position,
        transition,
        rng
):
    # print("rng state", rng.bit_generator.state['state']['state'])
    # Pick new action
    action = policy[t_idx]
    # Draw position
    new_pos_idx = rng.choice(
        position.size,
        p=transition[action, t_idx, pos_idx, :]
    )
    if LOG_AT_EACH_TIMESTEP:
        print(f"t_idx {t_idx:02} a {action} pos_idx {pos_idx:02} n_steps {position[pos_idx]} => new pos_idx {new_pos_idx:02} rng state {rng.bit_generator.state['state']['state']}")

    return action, new_pos_idx


def compute_number_of_observations(pseudo_counts):
    return int(np.sum(pseudo_counts) - pseudo_counts.size * ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER)


def select_action_plan(
        log_prior_position: np.ndarray,
        gamma: float,
        position: np.ndarray,
        pseudo_counts: np.ndarray,
        pos_idx: int,
        t_idx: int,
        action_plans: np.ndarray,
        seed: int
):
    """Select the best action to take"""
    # Set the seed
    # TODO: Check if this is the correct way to set the seed
    rng = np.random.default_rng(seed)
    if LOG_ASSISTANT_MODEL:
        n_obs = compute_number_of_observations(pseudo_counts)
        # print("number of observations", n_obs)
        # print("sum pseudo counts", np.sum(pseudo_counts))
        # print("jitter sum", pseudo_counts.size*ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER)
        print(f"Assistant: t_idx={t_idx:02} pos_idx={pos_idx:02} n obs {n_obs:02} rng state {rng.bit_generator.state['state']['state']}")
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
        qps = np.zeros((h, position.size))
        # We know where we start
        qp = np.zeros(position.size)
        qp[pos_idx] = 1.
        for h_idx in range(h):
            previous_qp = qp.copy()
            a = ap[h_idx]
            rollout_t_index = t_idx + h_idx
            _qt = qt[a, rollout_t_index]
            _alpha = alpha_t[a, rollout_t_index]
            qp = qp @ _qt  # Using beliefs about velocity transitions
            # Equation B.34 (p 253)
            make_sense = _alpha > 0
            # _qt += 1e-16
            w = 1/(2*_alpha) - 1/(2*np.sum(_alpha, axis=-1, keepdims=True))
            w *= make_sense.astype(float)
            # E_Q[D_KL(Q(o) || Q(o|o'))]
            v_model = (previous_qp@w)@qp
            # Eq B.29
            # H(Q(o)) = - sum_i Q(o_i) log(Q(o_i)) - E_Q(s)[H[P(o |s)]]
            # For a justification of the epistemic value for state, see p 137
            # The second term is 0 because the entropy of the likelihood matrices is 0
            # Because the likelihood is trivial, Q(o) = Q(s)
            # v_state_p = - qp @ np.log(qp + 1e-16)
            # v_state_v = - qv @ np.log(qv + 1e-16)
            # v_state_c = - 0   # Context is known and perfectly predictable in this case
            # A possibility is to consider only the last timestep
            # if h_idx == h-1:
            epistemic[ap_index] += v_model  # + v_state_v  # + v_state_p  # + v_model
            # record the values
            qps[h_idx] = qp
        # Eq B.28
        pragmatic[ap_index] = np.sum(qps @ log_prior_position)
    # Choose the best action plan
    # print("pragmatic", pragmatic)
    # print("epistemic", epistemic)
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
        efe = gamma * epistemic + pragmatic
    close_to_max_efe = np.isclose(efe, efe.max())
    # print("efe", efe)
    # print("close to max", close_to_max_efe)
    idx_close_to_max = np.where(close_to_max_efe)[0]
    # print("idx close to max", idx_close_to_max)
    best_action_plan_index = rng.choice(idx_close_to_max)
    if LOG_ASSISTANT_MODEL:
        print("Selected action plan", best_action_plan_index)
        print("-"*80)
    return best_action_plan_index, pragmatic, epistemic
