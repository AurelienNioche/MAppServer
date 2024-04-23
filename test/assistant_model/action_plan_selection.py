import numpy as np


def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


def select_action_plan(
        log_prior_position: np.ndarray,
        gamma: float,
        position: np.ndarray,
        velocity: np.ndarray,
        alpha_atvv: np.ndarray,
        transition_position_pvp: np.ndarray,
        v_idx: int,
        pos_idx: int,
        t_idx: int,
        action_plans: np.ndarray,
):
    """
    Select the best action to take
    """

    # Get the dimensions of the action plans
    n_action_plan, h = action_plans.shape

    # Initialize action plan values
    pragmatic = np.zeros(n_action_plan)
    epistemic = np.zeros(n_action_plan)

    alpha_t = alpha_atvv.copy()
    qt = normalize_last_dim(alpha_t)

    # Compute value of each action plan
    for ap_index, ap in enumerate(action_plans):

        qvs = np.zeros((h, velocity.size))
        qps = np.zeros((h, position.size))

        qv = np.zeros(velocity.size)
        qv[v_idx] = 1.
        qp = np.zeros(position.size)
        qp[pos_idx] = 1.

        for h_idx in range(h):

            previous_qv = qv.copy()

            a = ap[h_idx]
            rollout_t_index = t_idx + h_idx

            _qt = qt[a, rollout_t_index]
            _alpha = alpha_t[a, rollout_t_index]

            qv = qv @ _qt  # Using beliefs about velocity transitions
            qp = qp @ (qv @ transition_position_pvp)

            # Equation B.34 (p 253)
            make_sense = _alpha > 0
            # _qt += 1e-16
            w = 1/(2*_alpha) - 1/(2*np.sum(_alpha, axis=-1, keepdims=True))
            w *= make_sense.astype(float)
            # E_Q[D_KL(Q(o) || Q(o|o'))]
            v_model = (previous_qv@w)@qv

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

            qvs[h_idx] = qv
            qps[h_idx] = qp

        # Eq B.28
        pragmatic[ap_index] = np.sum(qps @ log_prior_position)

    # Choose the best action plan
    # print("pragmatic", pragmatic)
    # print("epistemic", epistemic)
    if np.isnan(pragmatic).all() and np.isnan(epistemic).all():
        print("All values are nan")
        return np.random.randint(n_action_plan), pragmatic, epistemic

    if not np.isnan(pragmatic).all() and not np.isnan(epistemic).all():
        efe = gamma * epistemic + pragmatic
    elif np.isnan(pragmatic).all():
        print("Pragmatic values are all nan")
        efe = epistemic
    else:
        print("Epistemic values are all nan")
        efe = pragmatic
    close_to_max_efe = np.isclose(efe, efe.max())
    # print("efe", efe)
    # print("close to max", close_to_max_efe)
    idx_close_to_max = np.where(close_to_max_efe)[0]
    # print("idx close to max", idx_close_to_max)
    best_action_plan_index = np.random.choice(idx_close_to_max)
    return best_action_plan_index, pragmatic, epistemic