import numpy as np
from celery import shared_task
from scipy import interpolate, stats
from datetime import datetime, time


from assistant.models import Velocity, Position, Alpha, User
# from assistant.config import N_TIMESTEP, N_ACTION, N_VELOCITY, \
 #    N_POSITION, POSITIONS, VELOCITIES, EXPERIMENT, DT

EXPERIMENT = "april2024"
N_TIMESTEP = 24
N_ACTION = 2
N_VELOCITY = 24
N_POSITION = 48
MAX_VELOCITY = 2000
MAX_POSITION = 20000
SIGMA_TRANS_POS = 2000  # Standard deviation using for the transition matrix of the position

TIMESTEP = timestep = np.linspace(0, 1, N_TIMESTEP)
VELOCITY = np.linspace(0, MAX_VELOCITY, N_VELOCITY)
POSITION = np.linspace(0, MAX_POSITION, N_POSITION)

# ------------------------------

def normalize_last_dim(alpha):
    sum_col = np.sum(alpha, axis=-1)
    sum_col[sum_col <= 0.0] = 1
    return alpha / np.expand_dims(sum_col, axis=-1)

# ------------------------------

def compute_position_matrix():

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
    if arr.ndim == 1:
        return arr.tolist()
    else:
        return [numpy_to_list(sub_arr) for sub_arr in arr]

# ----------------

def extract_step_events(u: User):

    entries = u.activity_set  #.filter(dt__date=now.date())
    dt = np.asarray(entries.values_list("dt", flat=True))
    all_pos = np.asarray(entries.values_list("step_midnight", flat=True))

    min_date = dt.min().date()
    days = np.asarray([(_dt.date() - min_date).days for _dt in dt])
    uniq_days = np.sort(np.unique(days))
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
    step_events = [[] for _ in range(uniq_days.size)]

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

    start =
    return step_events, list(uniq_days)


# -----------------------

def compute_deriv_cum_steps(step_events):

    deriv_cum_steps = np.zeros((len(step_events), N_TIMESTEP))
    for day, step_events_day in enumerate(step_events):

        # Compute the cumulative steps and the derivative of the cumulative steps to get the activity
        cum_steps_day = np.sum(step_events_day <= TIMESTEP[:, None], axis=1)
        deriv_cum_steps_day = np.gradient(cum_steps_day, timestep + 1) / (timestep.size - 1)
        deriv_cum_steps[day] = deriv_cum_steps_day

    return deriv_cum_steps


# ------------------------

def extract_actions(u: User, deriv_cum_steps: np.ndarray, dates: list, now: datetime):

    actions = np.zeros((deriv_cum_steps.shape[0], N_TIMESTEP))
    ch = u.challenge_set.filter(accepted=True, dt_end__lt=now)
    ch_date = np.asarray([dates.index(ch.dt_end.date()) for ch in ch])
    ch_timestep = np.asarray([ch.timestep_index for ch in ch])
    for a, t in zip(ch_date, ch_timestep):
        actions[a, t] = 1
    return actions


def compute_alpha(actions):


    alpha_atvv = np.zeros((N_ACTION, timestep.size-1, VELOCITY.size, VELOCITY.size))
    for sample in range(n_sample_beta):
    for t in range(timestep.size - 1):
        alpha_atvv[actions[sample, t+1], t, v_idx[sample, t], v_idx[sample, t + 1]] += 1


def update_beliefs(u: User, now: datetime = None):
    if now is None:
        now = datetime.now()

    print(f"Updating beliefs for user {u.username} at {now}")
    print("Now date: ", now.date())
    # Delete all entries for today
    # u.velocity_set.filter(dt__date=now.date()).delete()
    # u.position_set.filter(dt__date=now.date()).delete()
    # u.alpha_set.filter(date=now.date()).delete()

    step_events, dates = extract_step_events(u=u)
    deriv_cum_steps = compute_deriv_cum_steps(step_events=step_events)

    # .filter(date=now.date())
    extract_actions(u=u, deriv_cum_steps=deriv_cum_steps, dates=dates, now=now)

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
