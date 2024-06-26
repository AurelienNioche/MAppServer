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


CAMEL_TO_SNAKE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


# ----------- Utils ------------------------------------------


def camel_to_snake(s):
    """
    Convert a CamelCase string to snake_case
    """
    return CAMEL_TO_SNAKE_PATTERN.sub("_", s).lower()


def convert_android_timestamp_to_datetime(ts):
    """
    Convert a timestamp in milliseconds to a datetime object
    """
    tz = pytz.timezone(TIME_ZONE)
    return datetime.datetime.fromtimestamp(ts / 1000, tz=tz)


def convert_datetime_to_android_timestamp(dt):
    """
    Convert a datetime object to a timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def convert_android_dict_to_python_dict(d):
    """
    Convert a dictionary from Android to a Python dictionary
    """
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
    """
    Convert a JSON string from Android to a Python dictionary
    """
    android_obj = json.loads(json_string)
    if isinstance(android_obj, dict):
        return convert_android_dict_to_python_dict(android_obj)
    elif isinstance(android_obj, list):
        return [convert_android_dict_to_python_dict(a) for a in android_obj]
    else:
        raise ValueError(f"Unknown type: `{type(android_obj)}` not a dict or a list.")


# ------------------ Login ------------------------------


def update_user_status_after_login(u):
    u.last_login = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    u.save()

    challenges = u.challenge_set.order_by("dt_offer_begin")
    challenges_android = [r.to_android_dict() for r in challenges]

    total_cashed_out = np.sum(
        u.challenge_set.filter(cashed_out=True).values_list("amount", flat=True)
    )
    chest_amount = u.base_chest_amount + total_cashed_out

    status = u.status_set.first()
    status.chest_amount = chest_amount
    status.error = ""  # Reset error if any error was present

    status.save()
    status_android = status.to_android_dict()

    step_records = u.activity_set.order_by("dt", "step_midnight")
    step_records_android = [s.to_android_dict() for s in step_records]

    return {
        "challengeList": json.dumps(challenges_android),
        "stepList": json.dumps(step_records_android),
        "status": json.dumps(status_android),
    }


# ------------------ Activity ----------------------------


def get_last_activity_timestamp(u):
    """
    Get the latest `Activity` timestamp
    """
    user_activities = u.activity_set
    if user_activities.count():
        last_record = user_activities.latest("dt")
        dt = last_record.dt
    else:
        dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

    last_activity_ts = convert_datetime_to_android_timestamp(dt)
    return {"lastActivityTimestampMillisecond": last_activity_ts}


def record_activity(u, activities_json):
    """
    Record the activities of a user
    """
    activities = read_android_json(activities_json)
    n_already_existing_with_same_id = 0
    n_already_existing_with_same_number_same_day = 0
    n_added = 0
    with transaction.atomic():
        for a in activities:
            if u.activity_set.filter(android_id=a["android_id"]).first() is not None:
                n_already_existing_with_same_id += 1
                continue

            # dt = a["dt"]
            # if (
            #     u.activity_set.filter(
            #         dt__day=dt.day,
            #         dt__month=dt.month,
            #         dt__year=dt.year,
            #         step_midnight=a["step_midnight"],
            #     ).first()
            #     is not None
            # ):
            #     n_already_existing_with_same_number_same_day += 1
            #     continue

            Activity.objects.create(user=u, **a)
            n_added += 1

    if n_already_existing_with_same_id > 0:
        print(
            f"Found {n_already_existing_with_same_id} already existing with the same ID"
        )
    if n_already_existing_with_same_number_same_day > 0:
        print(
            f"Found {n_already_existing_with_same_number_same_day} already existing with the same number and day"
        )
    return n_added > 0

# ----------------- Interaction -----------------------


def record_interactions(u, interactions_json):
    """
    Record the interactions of a user with the app
    """
    interactions = read_android_json(interactions_json)
    with transaction.atomic():
        for itr in interactions:
            # print(f"adding new interaction: {itr}")

            if (
                u.interaction_set.filter(android_id=itr["android_id"]).first()
                is not None
            ):
                print("Record already exists")
                continue

            Interaction.objects.create(user=u, **itr)


def get_last_interaction_timestamp(u):
    """
    Get the latest `Interaction` timestamp
    """

    # Get the latest `Interaction` timestamp
    user_interactions = u.interaction_set
    if user_interactions.count():
        last_interaction = user_interactions.latest("dt")
        dt = last_interaction.dt
    else:
        dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

    last_interaction_ts = convert_datetime_to_android_timestamp(dt)
    return {"lastInteractionTimestampMillisecond": last_interaction_ts}


# -------------------- Challenge ----------------------------


def sync_challenges(u, unsynced_challenges_json):
    # First, update the challenges as by the user state
    unsynced_challenges = read_android_json(unsynced_challenges_json)
    synced_challenges_id = []
    synced_challenges_new_server_tags = []

    with transaction.atomic():
        # Update the challenges that were updated by the user
        for entry in unsynced_challenges:
            u.challenge_set.filter(android_id=entry["android_id"]).update(**entry)

            synced_challenges_id.append(entry["android_id"])
            synced_challenges_new_server_tags.append(entry["android_tag"])

        # Get the challenges that were updated by the assistant
        updated_challenges = u.challenge_set.exclude(android_tag=F("server_tag")).order_by("dt_offer_begin")
        updated_challenges_android = [r.to_android_dict() for r in updated_challenges]

    return {
        "syncedChallengesId": json.dumps(synced_challenges_id),
        "syncedChallengesTag": json.dumps(synced_challenges_new_server_tags),
        "updatedChallenges": json.dumps(updated_challenges_android)
    }


class RequestHandler:
    @staticmethod
    def login(r):
        """
        Handle the login request
        """
        # Check the app version
        if "appVersion" not in r or r["appVersion"] != APP_VERSION:
            print(f"App version {r['appVersion']} not supported. I'll skip this request.")
            return
        # Extract the data
        username = r["username"]
        # Check the user
        # print(f"User {r['username']} is trying to connect...")
        u = User.objects.filter(username=username).first()
        ok = u is not None
        if not ok:
            print(f"User {r['username']} not recognized!")
            return {"ok": ok}
        # Update the user status if everything is fine
        r.update(update_user_status_after_login(u), **{"ok": ok})
        return r

    @staticmethod
    def update(r):
        """
        Handle the update request
        """
        app_version = r["appVersion"]
        if "appVersion" not in r or r["appVersion"] != APP_VERSION:
            print(f"App version {app_version} not supported. I'll skip this request.")
            return
        # Extract the data
        username = r.get("username", None)
        subject = r.get("subject", None)
        activities_json = r.get("steps", None)
        interactions_json = r.get("interactions", None)
        un_synced_challenges_json = r.get("unSyncedChallenges", None)
        status = r.get("status", None)
        now = r.get("now", None)  # This is for testing purposes
        # Find the user
        u = User.objects.filter(username=username).first()
        if u is None:
            print(
                f"Ask for update but user not recognized: {username}. I'll skip this request."
            )
            return
        # Find the user
        u = User.objects.filter(username=username).first()
        if u is None:
            raise ValueError("User not recognized")
        # Record the new activities
        record_activity(u, activities_json)
        # Record the interactions
        record_interactions(u, interactions_json)
        # Update the user status
        Status.objects.filter(user=u).update(**read_android_json(status))
        # Register the connection to the server
        ConnectionToServer.objects.create(user=u)
        # Update the model
        # TODO: this might take a long time
        #  would need to use Celery or something similar
        assistant.tasks.update_beliefs_and_challenges(u=u, now=now)
        # Prepare the response
        r = {"subject": subject}
        r.update(get_last_activity_timestamp(u))
        r.update(get_last_interaction_timestamp(u))
        r.update(sync_challenges(u, un_synced_challenges_json))
        return r


# --------------------------------------- #


def treat_request(r):
    subject = r["subject"]
    try:
        f = getattr(RequestHandler, subject)
    except AttributeError:
        raise ValueError(f"Subject of the request not recognized: '{subject}'")
    return f(r)
