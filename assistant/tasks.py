import os
import numpy as np
from celery import shared_task
from scipy import interpolate
from datetime import datetime

from assistant.models import Velocity, Position, Alpha, Schedule, User, Action
from user.models import Activity
from config import N_TIMESTEP, N_ACTION, N_VELOCITY, \
    N_POSITION, POSITIONS, VELOCITIES, EXPERIMENT, DT


def update_beliefs(u: User, now: datetime = None):
    if now is None:
        now = datetime.now()

    entries = Activity.objects.filter(user=u, dt__date=now.date)
    dt = np.asarray(entries.values_list("dt", flat=True))
    y = np.asarray(entries.values_list("step_midnight", flat=True))

    old_entries = Velocity.objects.filter(user=u, dt__date=now.date)
    if old_entries is not None:
        old_entries.delete()

    old_entries = Position.objects.filter(user=u, dt__date=now.date)
    if old_entries is not None:
        old_entries.delete()

    actions = Action.objects.filter(user=u, date=now.date).order_by("timestep_index")

    min_ts = np.min(dt).timestamp()
    x_sec = np.asarray([_dt.timestamp() for _dt in dt])

    f = interpolate.interp1d(x_sec, y, kind="linear")

    # min_val = 0
    max_ts = now.timestamp()
    # max_val = max_ts  # - min_ts
    x_new = np.arange(min_ts, max_ts, DT)
    y_new = np.zeros_like(x_new)

    can_be_interpolated = (x_new >= x_sec.min()) * (x_new <= x_sec.max())
    y_new[can_be_interpolated] = f(x_new[can_be_interpolated])
    y_new[x_new < x_sec.min()] = 0
    y_new[x_new > x_sec.max()] = y.max()

    # Compute the diff
    y_diff = np.diff(y_new) / DT
    x_diff = [datetime.fromtimestamp(x_) for x_ in x_new[:-1]]  # Forward approximation

    # Record values ---------------

    for x_, y_ in zip(x_diff, y_diff):
        Velocity.objects.create(dt=x_, velocity=y_)

    for x_, y_ in zip(x_new, y_new):
        Position.objects.create(dt=x_, velocity=y_)

    # Discretize ------------------

    bins = list(VELOCITIES) + [np.inf]
    v_indexes = np.digitize(y_diff, bins, right=True) - 1

    bins = list(POSITIONS) + [np.inf]
    p_indexes = np.digitize(y_new, bins, right=True) - 1

    # density = hist / np.sum(hist)
    alpha_tapvv = np.zeros((N_TIMESTEP, N_ACTION, N_POSITION, N_VELOCITY, N_VELOCITY))
    for t_idx, a in enumerate(actions):
        if len(v_indexes) <= t_idx + 1:
            break
        p = p_indexes[t_idx]
        v = v_indexes[t_idx]
        v_t_plus_one = v_indexes[t_idx + 1]
        alpha_tapvv[t_idx, a, p, v, v_t_plus_one] += 1

    Alpha.objects.create(user=u, date=now.date, alpha=alpha_tapvv)


@shared_task
def update_beliefs_for_all_users():
    print("hello from the background task")

    now = datetime.now()

    # This is a background task that runs every X seconds.
    for u in User.objects.filter(experiment=EXPERIMENT):

        update_beliefs(u, now)
