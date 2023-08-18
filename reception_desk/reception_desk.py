import json
import datetime
import pytz
from django.db import transaction
import numpy as np
import re
from django.db.models import F

import assistant.tasks
from MAppServer.settings import TIME_ZONE, APP_VERSION
from user.models import User, Activity, Status, ConnectionToServer, Interaction


CAMEL_TO_SNAKE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')


# ----------- Utils ------------------------------------------

def camel_to_snake(s):
    return CAMEL_TO_SNAKE_PATTERN.sub('_', s).lower()


def convert_android_timestamp_to_datetime(ts):
    tz = pytz.timezone(TIME_ZONE)
    return datetime.datetime.fromtimestamp(ts / 1000, tz=tz)


def convert_datetime_to_android_timestamp(dt):
    return int(dt.timestamp() * 1000)


def convert_android_dict_to_python_dict(d):
    python_dict = {}
    for k, v in d.items():
        k = camel_to_snake(k)
        if "ts" in k:
            k = k.replace("ts", "dt")
            v = convert_android_timestamp_to_datetime(v)
        elif k == "id":
            k = "android_id"
        python_dict[k] = v
    return python_dict


def read_android_json(json_string):
    android_obj = json.loads(json_string)
    if type(android_obj) is dict:
        return convert_android_dict_to_python_dict(android_obj)
    elif type(android_obj) is list:
        return [convert_android_dict_to_python_dict(a) for a in android_obj]
    else:
        raise ValueError("Unknown type")

# ----------------------------------------------------


class RequestHandler:

    @staticmethod
    def login(r):

        if "appVersion" not in r:
            print("App version not specified. I'll skip this request.")
            return

        if r["appVersion"] != APP_VERSION:
            print(f"App version {r['appVersion']} not supported. I'll skip this request.")
            return

        print(f"User {r['username']} is trying to connect...")

        username = r["username"]
        # reset_user = r["resetUser"]
        #
        # if reset_user:
        #     if username == "123test":
        #         print("Resetting user")
        #         u = User.objects.filter(username=username).first()
        #         if u is not None:
        #             u.delete()
        #             create_test_user()
        #         else:
        #             print("User not found")

        u = User.objects.filter(username=username).first()
        ok = u is not None
        if ok:
            u.last_login = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            u.save()
            print(f"User {username} successfully connected")
            challenges = u.challenge_set.order_by("dt_offer_begin")
            challenges_android = [r.to_android_dict() for r in challenges]

            total_cashed_out = np.sum(
                u.challenge_set.filter(cashed_out=True).values_list("amount", flat=True))
            chest_amount = u.base_chest_amount + total_cashed_out

            status = u.status_set.first()
            status.chest_amount = chest_amount
            status.error = ""  # Reset error if any error was present

            status.save()
            status_android = status.to_android_dict()

            step_records = u.activity_set.order_by("dt", "step_midnight")
            step_records_android = [s.to_android_dict() for s in step_records]

        else:
            print(f"User {r['username']} not recognized!")
            # Just to be sure that the variables are defined for passing to json decoder
            challenges_android, status_android, step_records_android = [], {}, []

        return {
            "subject": r["subject"],
            "ok": ok,
            "challengeList": json.dumps(challenges_android),
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

        activities_json = r["steps"]
        interactions_json = r["interactions"]
        unsynced_challenges_json = r["unsyncedChallenges"]  # TODO: rename in Android project
        status = r["status"]

        u = User.objects.filter(username=username).first()
        if u is None:
            raise ValueError("User not recognized")

        # --------------------------------------------------------------------------------------------

        # Record any new activity
        activities = read_android_json(activities_json)
        n_already_existing_with_same_id = 0
        n_already_existing_with_same_number_same_day = 0
        n_added = 0
        with transaction.atomic():
            for a in activities:

                if u.activity_set.filter(android_id=a["android_id"]).first() is not None:
                    n_already_existing_with_same_id += 1
                    continue

                dt = a["dt"]
                if u.activity_set.filter(dt__day=dt.day, dt__month=dt.month, dt__year=dt.year,
                                         step_midnight=a["step_midnight"]).first() is not None:
                    n_already_existing_with_same_number_same_day += 1
                    continue

                Activity.objects.create(user=u, **a)
                n_added += 1

        if n_already_existing_with_same_id > 0:
            print(f"Found {n_already_existing_with_same_id} already existing with the same ID")
        if n_already_existing_with_same_number_same_day > 0:
            print(f"Found {n_already_existing_with_same_number_same_day} already existing with the same number and day")

        print(f"Added {n_added} new records")
        if n_added:
            # TODO: this might take a long time, would need to use Celery or something similar
            print("Updating beliefs")
            assistant.tasks.update_beliefs(u=u)

        # --------------------------------------------------------------------------------------------

        # Record any new interaction
        interactions = read_android_json(interactions_json)
        with transaction.atomic():
            for itr in interactions:
                print(f"adding new interaction: {itr}")

                if u.interaction_set.filter(android_id=itr["android_id"]).first() is not None:
                    print("Record already exists")
                    continue

                Interaction.objects.create(user=u, **itr)

        # ------------------------------------------------------------------------------------

        # Get the latest `Activity` timestamp
        user_activities = u.activity_set
        if user_activities.count():
            last_record = user_activities.latest("dt")
            dt = last_record.dt
        else:
            dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

        last_activity_ts = convert_datetime_to_android_timestamp(dt)

        # ------------------------------------------------------------------------------------
        # Get the latest `Interaction` timestamp
        user_interactions = u.interaction_set
        if user_interactions.count():
            last_interaction = user_interactions.latest("dt")
            dt = last_interaction.dt
        else:
            dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

        last_interaction_ts = convert_datetime_to_android_timestamp(dt)

        # ------------------------------------------------------------------------------------------------

        unsynced_challenges = read_android_json(unsynced_challenges_json)
        synced_challenges_id = []
        synced_challenges_new_server_tags = []

        with transaction.atomic():

            for entry in unsynced_challenges:
                u.challenge_set.filter(android_id=entry["android_id"]).update(**entry)

                synced_challenges_id.append(entry["android_id"])
                synced_challenges_new_server_tags.append(entry["android_tag"])

            updated_challenges = u.challenge_set.exclude(android_tag=F("server_tag"))
            for entry in updated_challenges:
                synced_challenges_id.append(entry.android_tag)
                synced_challenges_new_server_tags.append(entry.server_tag)

        # -------------------------------------------------------------------------------

        # Update the user status
        status = read_android_json(status)
        Status.objects.filter(user=u).update(**status)

        ConnectionToServer.objects.create(user=u)

        return {
            'subject': subject,
            'lastActivityTimestampMillisecond': last_activity_ts,
            'lastInteractionTimestampMillisecond': last_interaction_ts,
            'syncedChallengesId': json.dumps(synced_challenges_id),
            'syncedChallengesTag': json.dumps(synced_challenges_new_server_tags),
            # 'newChallenges': json.dumps([c.to_android_dict() for c in new_challenges])
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
