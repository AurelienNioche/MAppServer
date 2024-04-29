import numpy as np
import pandas as pd
from datetime import datetime, time
from pytz import timezone
import uuid
import django.db.models

from MAppServer.settings import TIME_ZONE
from assistant.models import User

from test.config.config import (
    TIMESTEP, POSITION, VELOCITY, SIGMA_POSITION_TRANSITION, GAMMA, LOG_PRIOR,
    HEURISTIC, ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER, SEED_ASSISTANT,
    INIT_POS_IDX, INIT_V_IDX
)
from test.test__generative_model import get_possible_action_plans
from test.assistant_model.action_plan_selection import select_action_plan
from test.activity.activity import (
    convert_timesteps_into_activity_level,
    get_timestep, get_datetime_from_timestep,
    extract_actions, extract_step_events,
    build_pseudo_count_matrix, build_position_transition_matrix)


SEC_IN_DAY = 86400


def generate_uuid():
    return str(uuid.uuid4())


def local(dt: datetime) -> datetime:
    return dt.astimezone(timezone(TIME_ZONE))


def read_activities_and_extract_step_events(
        u: User
) -> tuple:
    """Extract the step events for a given user"""
    entries = u.activity_set.order_by("dt")
    dt = np.asarray(entries.values_list("dt", flat=True))
    all_pos = np.asarray(entries.values_list("step_midnight", flat=True))
    days = np.asarray([_dt.date() for _dt in dt])
    uniq_days = list(np.sort(np.unique(days)))
    step_events = extract_step_events(
        step_counts=all_pos,
        datetimes=pd.to_datetime(dt),
        remove_empty_days=False
    )
    if len(step_events) == 0:
        return step_events, uniq_days, None, None
    else:
        return step_events, uniq_days, dt.min(), dt.max()


def get_future_challenges(
        u: User,
        now: datetime
) -> django.db.models.query.QuerySet:
    """Get all future challenges that will happen today"""
    u_challenges = u.challenge_set
    today_u_challenges = u_challenges.filter(
        dt_begin__date=now.date(),
        dt_offer_begin__gt=now)
    return today_u_challenges.order_by('dt_earliest')


def get_current_position_and_velocity(
        u: User,
        activity: np.ndarray,
        dates: list,
        now: datetime,
        timestep: np.ndarray
) -> tuple:
    """Get the current position and velocity of the user"""
    # Get the current timestep
    t_idx = get_timestep(now, timestep=timestep)
    # Manage the case where there is no activity/we are at the start of the day
    if t_idx == 0:
        return INIT_POS_IDX, INIT_V_IDX, t_idx
    # Get the current position and velocity
    start_of_day = datetime.combine(now, time.min, tzinfo=timezone(TIME_ZONE))
    today_activities = u.activity_set.filter(dt__gt=start_of_day, dt__lt=now)
    last_act = today_activities.order_by('dt').first()
    if last_act is None:
        return 0, 0, t_idx
    pos = last_act.step_midnight
    pos_idx = np.digitize(pos, POSITION, right=False) - 1
    date = dates.index(now.date())
    ts = get_timestep(now, timestep=timestep)
    # print("date", date, "ts", ts)
    # print("deriv_cumulative_steps", deriv_cumulative_steps.shape)
    v = activity[date, ts]
    # print("v", v)
    v_idx = np.digitize(v, VELOCITY, right=False) - 1
    return pos_idx, v_idx, t_idx


def update_challenges_based_on_action_plan(action_plan, now, later_challenges, timestep):
    """Update the challenges based on the action plan"""
    t_idx = get_timestep(now, timestep=timestep)
    t_selected = t_idx + np.argwhere(action_plan == 1).flatten()
    action_plan__datetime = [
        get_datetime_from_timestep(t, timestep=timestep, now=now)
        for t in t_selected]

    for ch, dt in zip(later_challenges, action_plan__datetime):
        challenge_delta = ch.dt_end - ch.dt_begin
        ch.dt_begin = dt
        ch.dt_end = dt + challenge_delta
        ch.server_tag = generate_uuid()
        ch.save()


def update_beliefs_and_challenges(
        u: User,
        now: str = None
):
    """
    Update the beliefs concerning the user and update the challenges accordingly
    """
    if now is None:
        print("I used default option for `now`")
        now = datetime.now(tz=timezone(TIME_ZONE))
    else:
        print("now", now)
        now = timezone(TIME_ZONE).localize(datetime.strptime(now, "%d/%m/%Y %H:%M:%S"))
    print("now", now)

    t_idx = get_timestep(now, timestep=TIMESTEP)
    # TODO: Check if it is what we want in the future - but nae bother, no future!
    if t_idx > 0:
        print(f"t_idx={t_idx} Not at the start of the day, exiting")
        return

    later_challenges = get_future_challenges(u, now)
    first_challenge = later_challenges.first()
    if first_challenge is None:
        print("No future challenges, exiting")
        return

    step_events, dates, dt_min, dt_max = read_activities_and_extract_step_events(u=u)
    # print("step_events", step_events)
    if len(step_events) > 0:
        activity = convert_timesteps_into_activity_level(
            step_events=step_events,
            timestep=TIMESTEP
        )
    else:
        activity = np.empty((len(dates), TIMESTEP.size - 1))
        assert activity.size == 0, "Activity should be empty"


    pos_idx, v_idx, t_idx = get_current_position_and_velocity(
        u=u,
        activity=activity,
        dates=dates,
        now=now,
        timestep=TIMESTEP
    )
    # .filter(date=now.date())
    actions = extract_actions(
        u=u,
        timestep=TIMESTEP,
    )
    actions = np.atleast_2d(actions)

    print("actions", actions.shape)
    print("activity", activity.shape)
    if dt_min is not None:
        print("dt_min", local(dt_min))
        print("dt_max", local(dt_max))

    alpha_tvv = build_pseudo_count_matrix(
        activity=activity,
        actions=actions,
        timestep=TIMESTEP,
        velocity=VELOCITY,
        jitter=ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER,
        dt_min=dt_min, dt_max=dt_max)

    transition_position_pvp = build_position_transition_matrix(
        position=POSITION,
        velocity=VELOCITY,
        sigma_transition_position=SIGMA_POSITION_TRANSITION
    )

    # Get the challenges for today
    today_challenges = u.challenge_set.filter(dt_begin__date=now.date())
    # Get the possible action plans
    action_plans_including_past, action_plans = get_possible_action_plans(
        challenges=today_challenges,
        timestep=TIMESTEP,
        u=u,
        now=now
    )
    # TODO: Do extra tests to be sure that the action plans are correct
    if len(action_plans) == 0:
        return
    # Select the action plan
    if HEURISTIC is None:
        # Select the action plan using active inference
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
            velocity=VELOCITY,
            seed=SEED_ASSISTANT
        )
        # Get the action plan based on the index
        action_plan = action_plans[action_plan_idx]
    else:
        # Use the heuristic (for debug)
        print("Using heuristic")
        action_plan = action_plans_including_past[HEURISTIC, t_idx:]
    # Update the challenges based on the action plan
    update_challenges_based_on_action_plan(
        action_plan=action_plan,
        now=now,
        later_challenges=later_challenges,
        timestep=TIMESTEP
    )
    print("-" * 80)
