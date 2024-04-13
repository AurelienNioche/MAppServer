import numpy as np
from tqdm import tqdm


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

    h = action_plans.shape[1]
    # print("h", h)

    n_action_plan = len(action_plans)

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
            # v_state_p = - qp @ np.log(qp + 1e-16) # ---> Add or remove?
            # v_state_v = - qv @ np.log(qv + 1e-16) # ---> Add or remove?
            # v_state_c = - 0   # Context is known and perfectly predictable in this case

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
        return np.random.choice(range(n_action_plan))

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


def test_assistant_model(
        position,
        velocity,
        timestep,
        n_episodes,
        n_restart,
        alpha_jitter,
        transition_velocity_atvv,
        transition_position_pvp,
        action_plans,
        log_prior_position,
        gamma, ):

    hist_err = np.zeros((n_restart, n_episodes*(timestep.size-1)))
    hist_pos = np.zeros((n_restart, n_episodes, timestep.size-1))
    hist_vel = np.zeros_like(hist_pos)

    hist_a = np.zeros((n_restart, timestep.size-1))

    hist_epistemic = np.zeros((n_restart, n_episodes, len(action_plans)))
    hist_pragmatic = np.zeros_like(hist_epistemic)

    init_pos_idx = np.absolute(position).argmin()  # Something close to 0
    init_v_idx = np.absolute(velocity).argmin()    # Something close to 0

    n_action = np.unique(action_plans).size

    for sample in tqdm(range(n_restart)):

        # Initialize alpha
        alpha_atvv = np.zeros((n_action, timestep.size-1, velocity.size, velocity.size)) + alpha_jitter

        # Log error
        error = np.mean(np.absolute(transition_velocity_atvv - normalize_last_dim(alpha_atvv)))
        if sample == 0:
            print(f"Initial error {error:.4f}")

        hist_a = []
        epoch = 0

        # with tqdm(total=n_episode) as pbar:
        for ep_idx in range(n_episodes):

            # Seed for reproducibility
            np.random.seed(ep_idx*12 + sample*123)

            # Select action plan
            action_plan_idx, pr_value, ep_value = select_action_plan(
                log_prior_position=log_prior_position,
                gamma=gamma,
                position=position,
                velocity=velocity,
                alpha_atvv=alpha_atvv,
                transition_position_pvp=transition_position_pvp,
                v_idx=init_v_idx,
                pos_idx=init_pos_idx,
                t_idx=0,
                action_plans=action_plans
            )

            # Record values
            hist_epistemic[sample, ep_idx] = ep_value
            hist_pragmatic[sample, ep_idx] = pr_value

            policy = action_plans[action_plan_idx]

            # policy = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype=int)

            # print("ep_idx", ep_idx)
            # print("policy", policy)

            # Run the policy
            v_idx = init_v_idx
            pos_idx = init_pos_idx

            for t_idx in range(timestep.size - 1):
                # Pick new action
                a = policy[t_idx]

                # Draw new velocity
                new_v_idx = np.random.choice(
                    np.arange(velocity.size),
                    p=transition_velocity_atvv[a, t_idx, v_idx, :])

                # Update pseudo-counts
                # https://blog.jakuba.net/posterior-predictive-distribution-for-the-dirichlet-categorical-model/
                alpha_atvv[a, t_idx, v_idx, new_v_idx] += 1

                # Update velocity and position
                v_idx = new_v_idx
                pos_idx = np.random.choice(position.size, p=transition_position_pvp[pos_idx, v_idx, :])

                # Record position and velocity
                hist_pos[sample, ep_idx, t_idx] = position[pos_idx]
                hist_vel[sample, ep_idx, t_idx] = velocity[v_idx]

                # Log
                error = np.mean(np.absolute(transition_velocity_atvv - normalize_last_dim(alpha_atvv)))
                hist_err[sample, epoch] = error
                # mean_ent = np.mean(np.sum(-alpha_atvv * np.log(alpha_atvv + 1e-16), axis=-1))

                epoch += 1

    return {
            "gamma": gamma,
            "policy": "af",
            "error": hist_err,
            "best_action_plan": hist_a,
            "epistemic": hist_epistemic,
            "pragmatic": hist_pragmatic,
            "position": hist_pos[:, :, :],
            "velocity": hist_vel[:, :, :]}