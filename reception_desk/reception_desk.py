import json
import datetime
import pytz
from django.db import transaction
import numpy as np
import re

import assistant.tasks
from MAppServer.settings import TIME_ZONE, APP_VERSION
from user.models import User, Challenge, Activity, Status, ConnectionToServer, Interaction

from __test_user__create import create_test_user
from __test_user__small_objectives import create_user__small_objectives

CAMEL_TO_SNAKE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')


# ----------- Utils ------------------------------------------


def camel_to_snake(s):
    return CAMEL_TO_SNAKE_PATTERN.sub('_', s).lower()


def convert_android_timestamp_to_datetime(ts):
    tz = pytz.timezone(TIME_ZONE)
    return datetime.datetime.fromtimestamp(ts / 1000, tz=tz)


def convert_android_dict_to_python_dict(d):
    python_dict = {}
    for k, v in d.items():
        k = camel_to_snake(k)
        if "ts" in k:
            k.replace("ts", "dt")
            v = convert_android_timestamp_to_datetime(v)
        elif k == "id":
            k = "android_id"
        python_dict[k] = v
    return python_dict


# ----------------------------------------------------


class RequestHandler:

    @staticmethod
    def login(r):

        if "appVersion" not in r:
            return

        if r["appVersion"] != APP_VERSION:
            print(f"App version {r['appVersion']} not supported. I'll skip this request.")
            return

        print(f"User {r['username']} is trying to connect...")

        username = r["username"]
        reset_user = r["resetUser"]

        if reset_user:
            if username == "123test":
                print("Resetting user")
                u = User.objects.filter(username=username).first()
                if u is not None:
                    u.delete()
                    create_test_user()
                else:
                    print("User not found")
            elif username == "smallobj":
                u = User.objects.filter(username=username).first()
                if u is not None:
                    u.delete()
                    create_user__small_objectives()
                else:
                    print("User not found")

        u = User.objects.filter(username=username).first()
        ok = u is not None
        if ok:
            u.last_login = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            u.save()
            print(f"User {username} successfully connected")
            rewards = u.challenge_set.order_by("date", "objective")
            rewards_android = [r.to_android_dict() for r in rewards]

            total_reward_cashed_out = np.sum(
                u.reward_set.filter(cashed_out=True).values_list("amount", flat=True))
            chest_amount = u.base_chest_amount + total_reward_cashed_out

            status = u.status_set.first()
            status.daily_objective = u.daily_objective
            status.chest_amount = chest_amount
            status.error = ""  # Reset error if any error was present

            status.save()
            status_android = status.to_android_dict()

            step_records = u.activity_set.order_by("dt", "step_midnight")
            step_records_android = [s.to_android_dict() for s in step_records]

        else:
            print(f"User {r['username']} not recognized!")
            # Just to be sure that the variables are defined for passing to json decoder
            rewards_android, status_android, step_records_android = [], {}, []

        return {
            "subject": r["subject"],
            "ok": ok,
            "challengeList": json.dumps(rewards_android),
            "stepList": json.dumps(step_records_android),
            "status": json.dumps(status_android),
            "username": username,
        }

    @staticmethod
    def update(r):

        app_version = r["appVersion"]
        if "appVersion" not in r or r["appVersion"] != APP_VERSION:
            print(f"App version {app_version} not supported. I'll skip this request.")
            return

        subject = r["subject"]
        username = r["username"]

        u = User.objects.filter(username=username).first()
        if u is None:
            print(f"Ask for update but user not recognized: {username}. I'll skip this request.")
            return

        activities_json = r["records"]
        interactions_json = r["interactions"]
        unsynced_challenges_json = r["unsyncedChallenges"]  # TODO: rename in Android project
        status = r["status"]

        u = User.objects.filter(username=username).first()
        if u is None:
            raise ValueError("User not recognized")

        # --------------------------------------------------------------------------------------------

        # Record any new activity
        activities = json.loads(activities_json)
        n_already_existing_with_same_id = 0
        n_already_existing_with_same_number_same_day = 0
        n_added = 0
        with transaction.atomic():
            for a in activities:

                android_id = a["id"]
                ts = a["ts"]
                ts_last_boot = a["tsLastBoot"]
                step_last_boot = a["stepLastBoot"]
                step_midnight = a["stepMidnight"]

                if u.activity_set.filter(android_id=android_id).first() is not None:
                    n_already_existing_with_same_id += 1
                    continue

                dt = convert_android_timestamp_to_datetime(ts)
                dt_last_boot = convert_android_timestamp_to_datetime(ts_last_boot)

                if u.activity_set.filter(dt__day=dt.day, dt__month=dt.month, dt__year=dt.year,
                                         step_midnight=step_midnight).first() is not None:
                    n_already_existing_with_same_number_same_day += 1
                    continue

                # Check if there isn't record too close in time from the same day, and delete it if so
                # to_delete = Activity.objects.filter(user=u)\
                #     .filter(dt__gt=dt - datetime.timedelta(minutes=2))\
                #     .exclude(dt__lt=datetime.datetime.combine(dt.date(), datetime.datetime.min.time())).first()
                # to_delete.delete()

                Activity.objects.create(
                    user=u,
                    android_id=android_id,
                    dt=dt,
                    dt_last_boot=dt_last_boot,
                    step_last_boot=step_last_boot,
                    step_midnight=step_midnight)
                n_added += 1

        if n_already_existing_with_same_id > 0:
            print(f"Found {n_already_existing_with_same_id} already existing with the same ID")
        if n_already_existing_with_same_number_same_day > 0:
            print(f"Found {n_already_existing_with_same_number_same_day} already existing with the same number and day")

        print(f"Added {n_added} new records")
        if n_added:
            # TODO: this might take a long time, would need to use Celery or something similar
            assistant.tasks.update_beliefs(u=u)

        # --------------------------------------------------------------------------------------------

        # Record any new interaction
        interactions = json.loads(interactions_json)
        with transaction.atomic():
            for entry in interactions:

                if u.interaction_set.filter(android_id=android_id).first() is not None:
                    print("Record already exists")
                    continue

                Interaction.objects.create(
                    user=u,
                    **convert_android_dict_to_python_dict(entry))

        # ------------------------------------------------------------------------------------

        # Get the latest `Activity` timestamp
        user_activities = u.activity_set
        if user_activities.count():
            last_record = user_activities.latest("dt")
            last_record_dt = last_record.dt
        else:
            last_record_dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

        last_activity_ts = int(last_record_dt.timestamp() * 1000)

        # ------------------------------------------------------------------------------------
        # Get the latest `Interaction` timestamp
        user_interactions = u.interaction_set
        if user_interactions.count():
            last_interaction = user_interactions.latest("dt")
            last_interaction_dt = last_interaction.dt
        else:
            last_interaction_dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

        last_interaction_ts = int(last_interaction_dt.timestamp() * 1000)

        # ------------------------------------------------------------------------------------------------

        unsynced_challenges = json.loads(unsynced_challenges_json)
        synced_challenges_id = []
        synced_challenges_new_server_tags = []

        with transaction.atomic():

            for entry in unsynced_challenges:
                e = convert_android_dict_to_python_dict(entry)
                Challenge.objects.filter(id=e["id"]).update(**e)

                synced_challenges_id.append(e["reward_id"])
                synced_challenges_new_server_tags.append(e["android_tag"])

        new_challenges = Challenge.objects.filter(user=u, android_tag__isnull=True)

        # -------------------------------------------------------------------------------

        # Update the user status
        status = convert_android_dict_to_python_dict(json.loads(status))
        Status.objects.filter(user=u).update(**status)

        ConnectionToServer.objects.create(user=u)

        return {
            'subject': subject,
            'lastActivityTimestampMillisecond': last_activity_ts,
            'lastInteractionTimestampMillisecond': last_interaction_ts,
            'syncedChallengesId': json.dumps(synced_challenges_id),
            'syncedChallengesTag': json.dumps(synced_challenges_new_server_tags),
            'newChallenges': json.dumps([c.to_android_dict() for c in new_challenges])
        }

# --------------------------------------- #


def treat_request(r):

    subject = r["subject"]
    try:
        f = getattr(RequestHandler, subject)
    except AttributeError:
        raise ValueError(
            f"Subject of the request not recognized: '{subject}'")
    return f(r)
