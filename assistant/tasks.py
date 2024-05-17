import numpy as np
import pandas as pd
from datetime import datetime, time
from pytz import timezone
import uuid
from django.db import transaction
import django.db.models

from MAppServer.settings import (
    TIMESTEP,
    POSITION,
    HEURISTIC,
    ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER,
    SEED_ASSISTANT,
    INIT_POS_IDX,
    TIME_ZONE
)
from assistant.models import User, ActionPlan
from core.action_plan_selection import select_action_plan
from core.action_plan_generation import get_possible_action_plans
from core.activity import (
    step_events_to_cumulative_steps,
    extract_actions,
    extract_step_events,
    build_pseudo_count_matrix
)
from core.timestep_and_datetime import get_datetime_from_timestep, get_timestep_from_datetime


def generate_uuid():
    return str(uuid.uuid4())


def read_activities_and_extract_step_events(
        u: User
) -> (list[list], pd.Series):
    """Extract the step events for a given user"""
    entries = u.activity_set.order_by("dt")
    dts = np.asarray(entries.values_list("dt", flat=True))
    dts = pd.to_datetime([_dt.astimezone(timezone(TIME_ZONE)) for _dt in dts])
    all_pos = np.asarray(entries.values_list("step_midnight", flat=True))
    step_events = extract_step_events(
        step_counts=all_pos,
        datetimes=dts,
        remove_empty_days=False
    )
    return step_events, dts


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
        now: datetime,
) -> tuple:
    """Get the current position and velocity of the user"""
    # Get the current timestep
    t_idx = get_timestep_from_datetime(now)
    # Manage the case where there is no activity/we are at the start of the day
    if t_idx == 0:
        return INIT_POS_IDX, t_idx
    # Get the current position and velocity
    start_of_day = datetime.combine(now, time.min, tzinfo=now.tzinfo)
    today_activities = u.activity_set.filter(dt__gt=start_of_day, dt__lt=now)
    last_act = today_activities.order_by('dt').first()
    if last_act is None:
        return 0, t_idx
    pos = last_act.step_midnight
    pos_idx = np.argmin(POSITION - pos)
    return pos_idx, t_idx


def update_challenges_based_on_action_plan(action_plan, now, later_challenges):
    """Update the challenges based on the action plan"""
    t_idx = get_timestep_from_datetime(now)
    t_selected = t_idx + np.argwhere(action_plan == 1).flatten()
    action_plan__datetime = [
        get_datetime_from_timestep(t, now=now)
        for t in t_selected
    ]

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
    """Update the beliefs concerning the user and update the challenges accordingly."""
    if now is None:
        now = datetime.now(tz=timezone(TIME_ZONE))
    else:
        now = timezone(TIME_ZONE).localize(datetime.strptime(now, "%d/%m/%Y %H:%M:%S"))

    # Look if a decision has already been taken for that day
    ap = u.actionplan_set.filter(date=now.date()).first()
    if ap is not None:
        # print("Decision already taken")
        return

    # Get later challenges
    later_challenges = get_future_challenges(u, now)
    first_challenge = later_challenges.first()
    if first_challenge is None:
        return

    # Get the step events
    step_events, dts = read_activities_and_extract_step_events(u=u)

    # Transform the step events into cumulative steps
    if len(step_events) > 0:
        # Get the minimum date
        min_date = dts.min().date()
        day_idx_now = (now.date() - min_date).days
        # TODO: It will probably be suitable to discard the first day to avoid
        #      to bias the inferences
        cum_steps = step_events_to_cumulative_steps(step_events=step_events)
        n_days_act = cum_steps.shape[0]
        if day_idx_now < n_days_act:
            cum_steps = cum_steps[:day_idx_now]  # Exclude today
    else:
        cum_steps = np.empty((0, TIMESTEP.size))

    pos_idx, t_idx = get_current_position_and_velocity(
        u=u,
        now=now
    )
    actions = extract_actions(
        u=u
    )
    actions = np.atleast_2d(actions)
    pseudo_counts = build_pseudo_count_matrix(
        cum_steps=cum_steps,
        actions=actions,
        jitter=ACTIVE_INFERENCE_PSEUDO_COUNT_JITTER
    )
    # Get the challenges for today
    today_challenges = u.challenge_set.filter(dt_begin__date=now.date())
    # Get the possible action plans
    action_plans_including_past, action_plans = get_possible_action_plans(
        challenges=today_challenges,
        u=u,
        now=now
    )
    # TODO: Do extra tests to be sure that the action plans are correct
    if len(action_plans) == 0:
        print("No possible action plans")
        return
    # Select the action plan
    if HEURISTIC is None:
        # Select the action plan using active inference
        action_plan_idx, pragmatic_value, epistemic_value = select_action_plan(
            pseudo_counts=pseudo_counts,
            pos_idx=pos_idx,
            t_idx=t_idx,
            action_plans=action_plans
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
        later_challenges=later_challenges
    )
    with transaction.atomic():
        ActionPlan.objects.create(user=u, date=now.date(), value=list(action_plan))
