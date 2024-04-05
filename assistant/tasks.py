import numpy as np
from celery import shared_task
from scipy import interpolate, stats
from datetime import datetime, time
import itertools
from scipy.special import softmax


from assistant.models import Velocity, Position, Alpha, User
# from assistant.config import N_TIMESTEP, N_ACTION, N_VELOCITY, \
 #    N_POSITION, POSITIONS, VELOCITIES, EXPERIMENT, DT

EXPERIMENT = "april2024"
HORIZON = 24
N_TIMESTEP = 24
N_ACTION = 2
N_VELOCITY = 24
N_POSITION = 48
MAX_VELOCITY = 2000
MAX_POSITION = 20000
SIGMA_TRANS_POS = 2000  # Standard deviation using for the transition matrix of the position
GAMMA = 0.1
LOG_PRIOR = np.log(softmax(np.arange(N_POSITION)))

TIMESTEP = np.linspace(0, 1, N_TIMESTEP)
VELOCITY = np.linspace(0, MAX_VELOCITY, N_VELOCITY)
POSITION = np.linspace(0, MAX_POSITION, N_POSITION)


# ------------------------------

def normalize_last_dim(alpha: np.ndarray):
    """
    Normalize the last dimension of a matrix
    """
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


# ------------------------------

def compute_position_matrix():

    """
    Compute the position transition matrix
    """

    # Compute position transition matrix
    tr = np.zeros((POSITION.size, VELOCITY.size, POSITION.size))
    for p_idx, p in enumerate(POSITION):
        for v_idx, v in enumerate(VELOCITY):
            # TODO: IMPLEMENT A DYNAMIC VERSION OF THE SIGMA
            dist = stats.norm.pdf(POSITION, loc=p + v, scale=SIGMA_TRANS_POS)
            if np.sum(dist) == 0:
                if p + v < 0:
                    dist[0] = 1
                elif p + v > POSITION[-1]:
                    dist[-1] = 1 # All weight on greatest position
                else:
                    print(f"bounds: {POSITION[0]}, {POSITION[1]}")
                    print(f"p+v: {p+v}")
                    raise ValueError("This should not happen, try increasing 'sigma_transition_position'")
            tr[p_idx, v_idx, :] = dist

    transition_position_pvp = normalize_last_dim(tr)
    return transition_position_pvp


# Utils --------------------

def numpy_to_list(arr: np.ndarray) -> object:
    """
    Convert a numpy array to a list
    """
    if arr.ndim == 1:
        return arr.tolist()
    else:
        return [numpy_to_list(sub_arr) for sub_arr in arr]


# ----------------

def extract_step_events(u: User):
    """
    Extract the step events for a given user
    """

    entries = u.activity_set  #.filter(dt__date=now.date())
    dt = np.asarray(entries.values_list("dt", flat=True))
    all_pos = np.asarray(entries.values_list("step_midnight", flat=True))

    min_date = dt.min().date()
    days = np.asarray([(_dt.date() - min_date).days for _dt in dt])
    uniq_days = list(np.sort(np.unique(days)))
    all_timestamp = (
        np.asarray(
            [
                (_dt - datetime.combine(_dt, time.min, _dt.tz)).total_seconds()
                for _dt in dt
            ]
        )
        / 86400
    )  # in fraction of day (between 0 and 1)

    # List of step events for each day, the event itself being the timestamp of the step
    step_events = [[] for _ in range(len(uniq_days))]

    for idx_day, day in enumerate(uniq_days):
        is_day = days == day
        obs_timestamp, obs_pos = all_timestamp[is_day], all_pos[is_day]

        # Sort the data by timestamp
        idx = np.argsort(obs_timestamp)
        obs_timestamp, obs_pos = obs_timestamp[idx], obs_pos[idx]

        # Compute the number of steps between each observed timestamp
        diff_obs_pos = np.diff(obs_pos)

        for ts, dif in zip(obs_timestamp, diff_obs_pos):
            # TODO: In the future, we probably want to spread that
            #  over a period assuming something like 6000 steps per hour
            step_events[idx_day] += [ts for _ in range(dif)]

    return step_events, uniq_days, dt.min(), dt.max()


# -----------------------

def compute_deriv_cum_steps(step_events):
    """
    Compute the pseudo-derivative of the cumulative steps to get the activity level
    """

    deriv_cum_steps = np.zeros((len(step_events), N_TIMESTEP))
    for day, step_events_day in enumerate(step_events):

        # Compute the cumulative steps and the derivative of the cumulative steps to get the activity
        cum_steps_day = np.sum(step_events_day <= TIMESTEP[:, None], axis=1)
        deriv_cum_steps_day = np.gradient(cum_steps_day, TIMESTEP + 1) / (TIMESTEP.size - 1)
        deriv_cum_steps[day] = deriv_cum_steps_day

    return deriv_cum_steps


# ------------------------

def extract_actions(u: User, deriv_cum_steps: np.ndarray, dates: list, now: datetime):

    """
    Extract the actions taken by the assistant
    """

    actions = np.zeros((deriv_cum_steps.shape[0], N_TIMESTEP))
    ch = u.challenge_set.filter(accepted=True, dt_end__lt=now)  # Less than now
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in ch])
    ch_timestep = np.asarray([get_timestep(ch.dt_begin) for ch in ch])
    for a, t in zip(ch_date, ch_timestep):
        actions[a, t] = 1
    return actions


def compute_alpha(actions, dt_min, dt_max, deriv_cum_steps):

    """
    Compute the alpha matrix (pseudo-counts) for the transition matrix
    """

    dt_min_sec = dt_min.timestamp()
    dt_max_sec = dt_max.timestamp()
    sec_in_day = 86400
    sec_per_timestep = sec_in_day / N_TIMESTEP

    bins = np.concatenate((VELOCITY, np.full(1, np.inf)))
    drv = np.clip(deriv_cum_steps, bins[0], bins[-1])
    v_idx = np.digitize(drv, bins, right=False) - 1

    alpha_atvv = np.zeros((N_ACTION, TIMESTEP.size-1, VELOCITY.size, VELOCITY.size))
    dt = dt_min_sec
    for day in range(deriv_cum_steps.shape[0]):
        for t in range(TIMESTEP.size - 1):
            if dt < dt_min_sec or dt > dt_max_sec:
                dt += sec_per_timestep
                continue
            alpha_atvv[actions[day, t+1], t, v_idx[day, t], v_idx[day, t + 1]] += 1
            dt += sec_per_timestep


def get_day_index(dt, dates):

    """
    Get the index of the day in the list of dates
    """
    return dates.index(dt.date())


def get_timestep(dt):
    """
    Get the timestep index for a given datetime
    """
    timestep_duration = 24 / N_TIMESTEP
    timestep = dt.hour // timestep_duration
    return timestep


def get_future_challenges(u: User, now: datetime):
    """
    Get all future challenges that will happen today
    """
    future_objects = u.challenge_set.filter(dt_offer_end__gt=now, dt_begin__day=now.date()).order_by('earliest')
    return future_objects


def select_action(alpha_atvv, transition_position_pvp, v_idx, pos_idx, earliest_challenge_dt):

    """
    Select the best action to take
    """

    t_idx = get_timestep(earliest_challenge_dt)

    h = min(HORIZON, N_TIMESTEP - t_idx)
    action_plan = list(itertools.product(range(N_ACTION), repeat=h))

    # Initialize action plan values
    pragmatic = np.zeros(len(action_plan))
    epistemic = np.zeros(len(action_plan))

    alpha_t = alpha_atvv.copy()
    qt = normalize_last_dim(alpha_t)

    # Compute value of each action plan
    for ap_index, ap in enumerate(action_plan):

        qvs = np.zeros((h, VELOCITY.size))
        qps = np.zeros((h, POSITION.size))

        qv = np.zeros(VELOCITY.size)
        qv[v_idx] = 1.
        qp = np.zeros(POSITION.size)
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
            epistemic[ap_index] += v_model # + v_state_v  # + v_state_p  # + v_model

            qvs[h_idx] = qv
            qps[h_idx] = qp

        # Eq B.28
        pragmatic[ap_index] = np.sum(qps @ LOG_PRIOR)

    # Choose the best action plan
    efe = GAMMA*epistemic + pragmatic
    best_action_plan_index = np.random.choice(np.arange(len(action_plan))[np.isclose(efe, efe.max())])
    a = action_plan[best_action_plan_index][0]


def get_current_position_and_velocity(u, deriv_cumulative_steps, dates, now):

    last_act = u.activity_set.filter(dt__date=now.date(), now__lt=now).order_by('dt').first()
    if last_act is None:
        return 0, 0
    pos = last_act.step_midnight
    pos_idx = np.digitize(pos, POSITION, right=False) - 1

    date = get_day_index(now, dates)
    ts = get_timestep(now)

    v = deriv_cumulative_steps[date, ts]

    v_idx = np.digitize(v, VELOCITY, right=False) - 1
    return pos_idx, v_idx

    # today_activities = u.activity_set.filter(dt__date=now.date()).order_by('dt')
    # last_act = today_activities.first()
    # if last_act is None:
    #     return 0, 0
    #
    #
    # # Get the position and velocity indexes
    # pos_idx = np.digitize(first_challenge.position, POSITION, right=False) - 1


def update_beliefs(u: User, now: datetime = None):
    if now is None:
        now = datetime.now()

    print(f"Updating beliefs for user {u.username} at {now}")
    print("Now date: ", now.date())
    # Delete all entries for today
    # u.velocity_set.filter(dt__date=now.date()).delete()
    # u.position_set.filter(dt__date=now.date()).delete()
    # u.alpha_set.filter(date=now.date()).delete()

    later_challenges = get_future_challenges(u, now)
    first_challenge = later_challenges.first()
    if first_challenge is None:
        print("No future challenges, exiting")
        return

    step_events, dates, dt_min, dt_max = extract_step_events(u=u)
    deriv_cum_steps = compute_deriv_cum_steps(step_events=step_events)

    # .filter(date=now.date())
    actions = extract_actions(u=u, deriv_cum_steps=deriv_cum_steps, dates=dates, now=now, dt_min=dt_min, dt_max=dt_max)

    alpha_tvv = compute_alpha(
        deriv_cum_steps=deriv_cum_steps,
        actions=actions,
        dt_min=dt_min, dt_max=dt_max)

    transition_position_pvp = compute_position_matrix()

    first_challenge_dt = first_challenge.earliest

    pos_idx, v_idx = get_current_position_and_velocity(
        step_events=step_events,
        deriv_cumulative_steps=deriv_cum_steps,
        dates=dates,
        now=now)



    # # noinspection PyUnresolvedReferences
    # min_ts = np.min(dt).timestamp()
    # x_sec = np.asarray([_dt.timestamp() for _dt in dt])
    #
    # f = interpolate.interp1d(x_sec, y, kind="linear")
    #
    # # min_val = 0
    # max_ts = now.timestamp()
    # # max_val = max_ts  # - min_ts
    # x_new = np.arange(min_ts, max_ts, DT)
    # y_new = np.zeros_like(x_new)
    #
    # can_be_interpolated = (x_new >= x_sec.min()) * (x_new <= x_sec.max())
    # y_new[can_be_interpolated] = f(x_new[can_be_interpolated])
    # y_new[x_new < x_sec.min()] = 0
    # y_new[x_new > x_sec.max()] = y.max()
    #
    # # Compute the diff
    # y_diff = np.diff(y_new) / DT
    # x_diff = x_new[:-1]  # Forward approximation
    #
    # x_new_dt = [datetime.fromtimestamp(x_) for x_ in x_new]
    # x_diff_dt = [datetime.fromtimestamp(x_) for x_ in x_diff]
    #
    # # Record values ---------------
    #
    # for i, (x_, y_) in enumerate(zip(x_new_dt, y_new)):
    #     Position.objects.create(user=u, dt=x_, timestep_index=i, position=y_)
    #
    # for i, (x_, y_) in enumerate(zip(x_diff_dt, y_diff)):
    #     Velocity.objects.create(user=u, dt=x_, timestep_index=i, velocity=y_)
    #
    # # Discretize ------------------
    #
    # bins = list(VELOCITIES) + [np.inf]
    # v_indexes = np.digitize(y_diff, bins, right=True) - 1
    #
    # bins = list(POSITIONS) + [np.inf]
    # p_indexes = np.digitize(y_new, bins, right=True) - 1
    #
    # # density = hist / np.sum(hist)
    # alpha_tapvv = np.zeros((N_TIMESTEP, N_ACTION, N_POSITION, N_VELOCITY, N_VELOCITY))
    # for t_idx, a in enumerate(actions):
    #     if len(v_indexes) <= t_idx + 1:
    #         break
    #     p = p_indexes[t_idx]
    #     v = v_indexes[t_idx]
    #     v_t_plus_one = v_indexes[t_idx + 1]
    #     alpha_tapvv[t_idx, a, p, v, v_t_plus_one] += 1
    #
    # Alpha.objects.create(user=u, date=now.date(), alpha=numpy_to_list(alpha_tapvv))


# @shared_task
# def update_beliefs_for_all_users():
#     print("hello from the background task")
#
#     now = datetime.now()
#
#     # This is a background task that runs every X seconds.
#     for u in User.objects.filter(experiment=EXPERIMENT):
#
#         update_beliefs(u, now)
