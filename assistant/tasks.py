import django.db.models
import numpy as np
import \
    pandas as pd
# from celery import shared_task
from scipy import stats
from datetime import datetime, time, timedelta
import itertools
from scipy.special import softmax
from pytz import timezone
import uuid

from MAppServer.settings import TIME_ZONE


from assistant.models import User

from test.config.config import TIMESTEP, POSITION, VELOCITY, SIGMA_POSITION_TRANSITION, GAMMA, LOG_PRIOR
from test.test__generative_model import get_possible_action_plans
from test.activity.activity import (
    compute_deriv_cum_steps,
    get_timestep, get_datetime_from_timestep,
    extract_actions, extract_step_events,
    build_pseudo_count_matrix, build_position_transition_matrix)

from test.assistant_model.action_plan_selection import select_action_plan


SEC_IN_DAY = 86400


def generate_uuid():
    return str(uuid.uuid4())


def read_activities_and_extract_step_events(
        u: User
) -> tuple:
    """Extract the step events for a given user"""
    entries = u.activity_set
    dt = np.asarray(entries.values_list("dt", flat=True))
    all_pos = np.asarray(entries.values_list("step_midnight", flat=True))
    days = np.asarray([_dt.date() for _dt in dt])
    uniq_days = list(np.sort(np.unique(days)))
    step_events = extract_step_events(
        step_counts=all_pos,
        datetimes=pd.to_datetime(dt),
        remove_empty_days=True
    )
    return step_events, uniq_days, dt.min(), dt.max()


def get_day_index(dt, dates):
    """Get the index of the day in the list of dates"""
    return dates.index(dt.date())


def get_future_challenges(u: User, now: datetime):
    """Get all future challenges that will happen today"""
    date = now.date()
    u_challenges = u.challenge_set
    today_u_challenges = u_challenges.filter(dt_begin__day=date.day, dt_begin__month=date.month, dt_begin__year=date.year)
    not_yet = today_u_challenges.filter(dt_offer_begin__gt=now)
    sorted_challenges = not_yet.order_by('dt_earliest')

    return sorted_challenges


def get_current_position_and_velocity(
        u: User,
        deriv_cumulative_steps: np.ndarray,
        dates: list,
        now: datetime,
        timestep: np.ndarray
) -> tuple:
    """Get the current position and velocity of the user"""
    # Get the current position and velocity
    start_of_day = datetime.combine(now, time.min, tzinfo=timezone(TIME_ZONE))
    today_activities = u.activity_set.filter(dt__gt=start_of_day, dt__lt=now)
    last_act = today_activities.order_by('dt').first()
    if last_act is None:
        return 0, 0
    pos = last_act.step_midnight
    pos_idx = np.digitize(pos, POSITION, right=False) - 1
    # Get the velocity
    date = get_day_index(now, dates)
    ts = get_timestep(now, timestep=timestep)
    print("date", date, "ts", ts)
    print("deriv_cumulative_steps", deriv_cumulative_steps.shape)
    v = deriv_cumulative_steps[date, ts]
    # print("v", v)
    v_idx = np.digitize(v, VELOCITY, right=False) - 1
    return pos_idx, v_idx


def local(dt: datetime) -> datetime:
    return dt.astimezone(timezone(TIME_ZONE))


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


def update_beliefs(
        u: User,
        now: str = None
):
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

    step_events, dates, dt_min, dt_max = read_activities_and_extract_step_events(u=u)
    deriv_cum_steps = compute_deriv_cum_steps(
        step_events=step_events,
        timestep=TIMESTEP
    )

    # .filter(date=now.date())
    actions = extract_actions(
        u=u,
        timestep=TIMESTEP,
    )

    alpha_tvv = build_pseudo_count_matrix(
        activity=deriv_cum_steps,
        actions=actions,
        timestep=TIMESTEP,
        velocity=VELOCITY,
        dt_min=dt_min, dt_max=dt_max)

    transition_position_pvp = build_position_transition_matrix(
        position=POSITION,
        velocity=VELOCITY,
        sigma_transition_position=SIGMA_POSITION_TRANSITION
    )

    pos_idx, v_idx = get_current_position_and_velocity(
        u=u,
        deriv_cumulative_steps=deriv_cum_steps,
        dates=dates,
        now=now,
        timestep=TIMESTEP)

    first_challenge_dt = first_challenge.dt_offer_end  # Begin of the first challenge
    t_idx = get_timestep(first_challenge_dt, timestep=TIMESTEP)

    today_challenges = u.challenge_set.filter(dt_begin__date=now.date())

    action_plans = get_possible_action_plans(
        challenges=today_challenges,
        timestep=TIMESTEP
    )
    action_plans = np.unique(action_plans[:, t_idx:], axis=0)
    print("T", t_idx, get_datetime_from_timestep(t_idx, now, TIMESTEP))
    print("Action plans", action_plans)
    action_plan_idx, pragmatic_value, epistemic_value = select_action_plan(
        alpha_atvv=alpha_tvv,
        transition_position_pvp=transition_position_pvp,
        v_idx=v_idx,
        pos_idx=pos_idx,
        t_idx=t_idx,
        action_plans=action_plans,
        log_prior_position=LOG_PRIOR,
        gamma=GAMMA,
        position=POSITION,
        velocity=VELOCITY
    )

    action_plans__datetime = np.asarray([get_datetime_from_timestep(t, timestep=TIMESTEP, now=now)
                                         for t in range(t_idx, TIMESTEP.size)])
    print("Action plan idx", action_plan_idx)
    selected = np.argwhere(action_plans[action_plan_idx] == 1).flatten()
    print(selected)
    action_plans__datetime = action_plans__datetime[selected]
    print("Action plan datetime", action_plans__datetime)
    # TODO: Implement the change of action, that is updating the challenge(s)
    update_challenges_based_on_action_plan(
        action_plan__datetime=action_plans__datetime,
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
