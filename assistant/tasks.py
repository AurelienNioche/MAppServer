import django.db.models
import numpy as np
# from celery import shared_task
from scipy import stats
from datetime import datetime, time, timedelta
import itertools
from scipy.special import softmax
from pytz import timezone
import uuid

from MAppServer.settings import TIME_ZONE


from assistant.models import Velocity, Position, Alpha, User
# from assistant.config import N_TIMESTEP, N_ACTION, N_VELOCITY, \
 #    N_POSITION, POSITIONS, VELOCITIES, EXPERIMENT, DT

EXPERIMENT = "april2024"
N_TIMESTEP = HORIZON = 24*4  # 15 minutes
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

# Utils --------------

SEC_IN_DAY = 86400


# ------------------------------

def normalize_last_dim(alpha: np.ndarray):
    """
    Normalize the last dimension of a matrix
    """
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)


# ------------------------------

def generate_uuid():
    return str(uuid.uuid4())


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

    # min_date = dt.min().date()
    days = np.asarray([_dt.date() for _dt in dt])
    # print("days")
    uniq_days = list(np.sort(np.unique(days)))
    all_timestamp = (
        np.asarray(
            [
                (_dt - datetime.combine(_dt, time.min, tzinfo=_dt.tzinfo)).total_seconds()
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

    actions = np.zeros((deriv_cum_steps.shape[0], N_TIMESTEP), dtype=int)
    ch = u.challenge_set.filter(accepted=True, dt_end__lt=now)  # Less than now
    ch_date = np.asarray([dates.index(ch.dt_begin.date()) for ch in ch])
    ch_timestep = np.asarray([get_timestep(ch.dt_begin) for ch in ch])
    for a, t in zip(ch_date, ch_timestep):
        actions[a, t] = 1
    return actions


def compute_alpha(actions: np.ndarray, dt_min: datetime, dt_max: datetime, deriv_cum_steps: np.ndarray) -> np.ndarray:

    """
    Compute the alpha matrix (pseudo-counts) for the transition matrix
    """

    dt_min_sec = dt_min.timestamp()
    dt_max_sec = dt_max.timestamp()
    sec_per_timestep = SEC_IN_DAY / N_TIMESTEP

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

    return alpha_atvv


def get_day_index(dt, dates):

    """
    Get the index of the day in the list of dates
    """
    # print("dates", dates, "dt.date()", dt.date())
    return dates.index(dt.date())


def get_timestep(dt, timestep=TIMESTEP, time_zone=TIME_ZONE):
    """
    Get the timestep index for a given datetime
    """
    timestep_duration = SEC_IN_DAY / timestep.size
    start_of_day = datetime.combine(dt, time.min, tzinfo=timezone(time_zone))
    diff = (dt - start_of_day).total_seconds()
    timestep = diff // timestep_duration
    return int(timestep)


def get_future_challenges(u: User, now: datetime):
    """
    Get all future challenges that will happen today
    """
    date = now.date()
    u_challenges = u.challenge_set
    # print("all challenges:")
    # for c in u_challenges.all():
    #     print(c.dt_offer_begin)
    today_u_challenges = u_challenges.filter(dt_begin__day=date.day, dt_begin__month=date.month, dt_begin__year=date.year)
    # print("challenges today:")
    # for c in today_u_challenges.all():
    #     print(c.dt_offer_begin)
    not_yet = today_u_challenges.filter(dt_offer_begin__gt=now)
    # print("Not yet challenges:")
    # for c in not_yet.all():
    # print(c.dt_offer_begin)
    sorted_challenges = not_yet.order_by('dt_earliest')

    return sorted_challenges


def select_action_plan(alpha_atvv, transition_position_pvp, v_idx, pos_idx, t_idx, action_plans):

    """
    Select the best action to take
    """

    h = len(action_plans[0])

    n_action_plan = len(action_plans)

    # Initialize action plan values
    pragmatic = np.zeros(n_action_plan)
    epistemic = np.zeros(n_action_plan)

    alpha_t = alpha_atvv.copy()
    qt = normalize_last_dim(alpha_t)

    # Compute value of each action plan
    for ap_index, ap in enumerate(action_plans):

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
    # print("pragmatic", pragmatic)
    # print("epistemic", epistemic)
    if np.isnan(pragmatic).all() and np.isnan(epistemic).all():
        # print("All values are nan")
        return np.random.choice(range(n_action_plan))

    if not np.isnan(pragmatic).all() and not np.isnan(epistemic).all():
        efe = GAMMA*epistemic + pragmatic
    elif np.isnan(pragmatic).all():
        # print("Pragmatic values are all nan")
        efe = epistemic
    else:
        # print("Epistemic values are all nan")
        efe = pragmatic
    close_to_max_efe = np.isclose(efe, efe.max())
    # print("efe", efe)
    # print("close to max", close_to_max_efe)
    idx_close_to_max = np.where(close_to_max_efe)[0]
    # print("idx close to max", idx_close_to_max)
    best_action_plan_index = np.random.choice(idx_close_to_max)
    return best_action_plan_index


def get_current_position_and_velocity(u, deriv_cumulative_steps, dates, now):

    start_of_day = datetime.combine(now, time.min, tzinfo=timezone(TIME_ZONE))
    today_activities = u.activity_set.filter(dt__gt=start_of_day, dt__lt=now)
    last_act = today_activities.order_by('dt').first()
    if last_act is None:
        return 0, 0
    pos = last_act.step_midnight
    pos_idx = np.digitize(pos, POSITION, right=False) - 1

    date = get_day_index(now, dates)
    ts = get_timestep(now)
    # print("date index", date)
    # print("timestep index", ts)

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


def local(dt: datetime) -> datetime:
    return dt.astimezone(timezone(TIME_ZONE))


def get_possible_action_plans(
        t_idx: int,
        later_challenges: django.db.models.QuerySet
) -> (list[np.ndarray], list[np.ndarray]):

    h = min(HORIZON, N_TIMESTEP - t_idx - 1)
    # print("Horizon:", h, "t_idx", t_idx, "N_TIMESTEP", N_TIMESTEP)

    # TODO: Only implement possible action plans depending on challenges structure
    # action_plan = # list(itertools.product(range(N_ACTION), repeat=h))

    strategies = []
    related_timesteps = []

    begin_of_day = local(later_challenges.first().dt_earliest).replace(hour=0, minute=0, second=0, microsecond=0)
    delta_t = timedelta(seconds=SEC_IN_DAY/N_TIMESTEP)

    for ch in later_challenges:
        # print("Challenge:", local(ch.dt_earliest), local(ch.dt_latest))
        ch_earliest_t_idx = get_timestep(ch.dt_earliest)
        ch_latest_t_idx = get_timestep(ch.dt_latest)
        duration_in_timestep = ch_latest_t_idx - ch_earliest_t_idx
        # print(timedelta(seconds=duration_in_timestep*SEC_IN_DAY/N_TIMESTEP))
        # print("duration in timestep", duration_in_timestep)
        # print("duration in time", ch.dt_latest - ch.dt_earliest)
        timesteps = np.arange(ch_earliest_t_idx, ch_latest_t_idx)
        strategy = np.eye(duration_in_timestep, dtype=int)
        strategies.append(strategy)
        related_timesteps.append(timesteps)

    action_plans = []
    action_plans__datetime = []
    for challenge_parts in itertools.product(*strategies):
        action_plan = np.zeros(h, dtype=int)
        action_plan__datetime = np.zeros(len(challenge_parts), dtype=datetime)
        for i, challenge_part in enumerate(challenge_parts):
            action_plan[related_timesteps[i] - t_idx] = challenge_part
            action_plan__datetime[i] = begin_of_day + delta_t * related_timesteps[i][np.where(challenge_part == 1)[0][0]]

        action_plans.append(action_plan)
        action_plans__datetime.append(action_plan__datetime)

    # print(f"action plan ({len(action_plan)})", action_plan)
    return action_plans, action_plans__datetime


def update_challenges_based_on_action_plan(action_plan__datetime, later_challenges):

    """
    Update the challenges based on the action plan
    """
    for ch, dt in zip(later_challenges, action_plan__datetime):
        challenge_delta = ch.dt_end - ch.dt_begin
        ch.dt_begin = dt
        ch.dt_end = dt + challenge_delta
        ch.server_tag = generate_uuid()
        ch.save()
    return


def update_beliefs(u: User, now: str = None):
    if now is None:
        now = datetime.now(tz=timezone(TIME_ZONE))
    else:
        now = timezone(TIME_ZONE).localize(datetime.strptime(now, "%d/%m/%Y %H:%M:%S"))

    print(f"Updating beliefs for user {u.username} at {now}")
    print("Now:", now)
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
    actions = extract_actions(u=u, deriv_cum_steps=deriv_cum_steps, dates=dates, now=now)

    alpha_tvv = compute_alpha(
        deriv_cum_steps=deriv_cum_steps,
        actions=actions,
        dt_min=dt_min, dt_max=dt_max)

    transition_position_pvp = compute_position_matrix()

    pos_idx, v_idx = get_current_position_and_velocity(
        u=u, deriv_cumulative_steps=deriv_cum_steps, dates=dates, now=now)

    first_challenge_dt = first_challenge.dt_offer_end  # Begin of the first challenge
    t_idx = get_timestep(first_challenge_dt)

    action_plans, action_plans__datetime = get_possible_action_plans(t_idx=t_idx, later_challenges=later_challenges)

    action_plan_idx = select_action_plan(
        alpha_atvv=alpha_tvv,
        transition_position_pvp=transition_position_pvp,
        v_idx=v_idx, pos_idx=pos_idx, t_idx=t_idx, action_plans=action_plans)

    # TODO: Implement the change of action, that is updating the challenge(s)
    update_challenges_based_on_action_plan(action_plan__datetime=action_plans__datetime[action_plan_idx],
                                           later_challenges=later_challenges)


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
