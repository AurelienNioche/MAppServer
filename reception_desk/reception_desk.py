import json
import datetime
import pytz
from django.db import transaction
import numpy as np

from MAppServer.settings import TIME_ZONE
from user.models import User, Reward, Activity, Status

from test_user__create import test_user_xp_like__create


class RequestHandler:

    @staticmethod
    def login(r):
        print(f"User {r['username']} is trying to connect...")

        reset_user = r["resetUser"]
        if reset_user:
            print("Resetting user")
            u = User.objects.filter(username=r["username"]).first()
            if u is not None:
                u.delete()
                test_user_xp_like__create()
            else:
                print("User not found")

        username = r["username"]
        u = User.objects.filter(username=username).first()
        ok = u is not None
        if ok:
            u.last_login = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            u.save()
            print(f"User {username} successfully connected")
            rewards = Reward.objects.filter(user=u).order_by("date", "objective")
            rewards = [r.to_dict() for r in rewards]

            total_reward_cashed_out = np.sum(
                Reward.objects.filter(user=u, cashed_out=True).values_list("amount", flat=True))
            chest_amount = u.base_chest_amount + total_reward_cashed_out
            daily_objective = u.daily_objective
        else:
            print(f"User {r['username']} not recognized!")
            # Just to be sure that the variables are defined for passing to json decoder
            chest_amount, daily_objective, rewards = 0, 0, []

        return {
            "subject": r["subject"],
            "ok": ok,
            "dailyObjective": daily_objective,
            "chestAmount": chest_amount,
            "rewardList": json.dumps(rewards),
            "username": username,
        }

    @staticmethod
    def update(r):

        subject = r["subject"]
        username = r["username"]
        progress_json = r["records"]
        un_sync_rewards_json = r["unSyncRewards"]
        status = r["status"]

        tz = pytz.timezone(TIME_ZONE)

        u = User.objects.filter(username=username).first()
        if u is None:
            raise ValueError("User not recognized")

        # --------------------------------------------------------------------------------------------

        # Record any new progress
        progress = json.loads(progress_json)
        with transaction.atomic():
            for p in progress:

                android_id = p["id"]
                ts = p["ts"]
                ts_last_boot = p["tsLastBoot"]
                step_last_boot = p["stepLastBoot"]
                step_midnight = p["stepMidnight"]

                if Activity.objects.filter(user=u, android_id=android_id).first() is not None:
                    print("Record already exists")
                    continue

                ts /= 1000
                ts_last_boot /= 1000
                dt = datetime.datetime.fromtimestamp(ts, tz=tz)
                dt_last_boot = datetime.datetime.fromtimestamp(ts_last_boot, tz=tz)

                if Activity.objects.filter(user=u, dt__day=dt.day, dt__month=dt.month, dt__year=dt.year,
                                           step_midnight=step_midnight).first() is not None:
                    print("A record with same number of steps for the same day already exists")
                    continue

                # Check if there isn't record too close in time from the same day, and delete it if so
                # to_delete = Activity.objects.filter(user=u)\
                #     .filter(dt__gt=dt - datetime.timedelta(minutes=2))\
                #     .exclude(dt__lt=datetime.datetime.combine(dt.date(), datetime.datetime.min.time())).first()
                # to_delete.delete()

                a = Activity(
                    android_id=android_id,
                    user=u,
                    dt=dt,
                    dt_last_boot=dt_last_boot,
                    step_last_boot=step_last_boot,
                    step_midnight=step_midnight)
                a.save()

        # ------------------------------------------------------------------------------------

        # Get the latest user_progress timestamp
        if Activity.objects.count():
            last_record = Activity.objects.latest("dt")
            last_record_dt = last_record.dt
        else:
            last_record_dt = datetime.datetime(1, 2, 3)  # Something very far away in the past

        last_record_ts = last_record_dt.timestamp() * 1000

        # ------------------------------------------------------------------------------------------------

        un_sync_rewards = json.loads(un_sync_rewards_json)
        sync_rewards_id = []
        sync_rewards_server_tag = []

        with transaction.atomic():

            for r_android in un_sync_rewards:

                reward_id = r_android["id"]
                objective_reached = r_android["objectiveReached"]
                cashed_out = r_android["cashedOut"]
                objective_reached_ts = r_android["objectiveReachedTs"]
                cashed_out_ts = r_android["cashedOutTs"]

                reward = Reward.objects.filter(id=reward_id).first()
                Reward.objects.filter(id=reward_id).update(**{
                    "objective_reached": objective_reached,
                    "cashed_out": cashed_out,
                    "objective_reached_dt": datetime.datetime.fromtimestamp(objective_reached_ts/1000, tz=tz),
                    "cashed_out_dt": datetime.datetime.fromtimestamp(cashed_out_ts/1000, tz=tz)})

                sync_rewards_id.append(reward.id)
                sync_rewards_server_tag.append(r_android["localTag"])  # Replace serverTag by localTag

        # -------------------------------------------------------------------------------

        # Update the user status
        status = json.loads(status)

        step_number = status["stepNumber"]
        chest_amount = status["chestAmount"]
        daily_objective = status["dailyObjective"]

        reward_id = status["rewardId"]
        objective = status["objective"]
        starting_at = status["startingAt"]
        amount = status["amount"]

        day_of_the_month = status["dayOfTheMonth"]
        day_of_the_week = status["dayOfTheWeek"]
        month = status["month"]

        state = status["state"]
        error = status["error"]

        Status.objects.filter(user=u).update(**{
            "last_update_dt": datetime.datetime.now(tz=tz),

            "step_number": step_number,
            "chest_amount": chest_amount,
            "daily_objective": daily_objective,

            "reward_id": reward_id,
            "objective": objective,
            "starting_at": starting_at,
            "amount": amount,

            "day_of_the_month": day_of_the_month,
            "day_of_the_week": day_of_the_week,
            "month": month,

            "state": state,
            "error": error
        })

        return {
            'subject': subject,
            'lastRecordTimestampMillisecond': last_record_ts,
            'syncRewardsId': json.dumps(sync_rewards_id),
            'syncRewardsServerTag': json.dumps(sync_rewards_server_tag)
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
