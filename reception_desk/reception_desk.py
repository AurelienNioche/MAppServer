import json
import datetime
import pytz
from django.db import transaction
import numpy as np

from MAppServer.settings import TIME_ZONE, USER_BASE_REWARD, USER_DAILY_OBJECTIVE, USER_LENGTH_REWARD_QUEUE
from user.models import User, Reward, Activity
import utils.time
# import assistant.core


class RequestHandler:

    @staticmethod
    def login(r):
        print(f"User {r['username']} is trying to connect")
        username = r["username"]
        u = User.objects.filter(username=username).first()
        ok = u is not None
        if ok:
            u.last_login = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            u.save()
            print(f"User {username} successfully connected")
            # if len(rewards_done_id) or Reward.objects.filter(accessible=False).count() == 0:  # If some rewards are already too old and/or have been obtained
            rewards = Reward.objects.filter(user=u, accessible=True).order_by("date", "objective")
            rewards = [r.to_dict() for r in rewards]
            print(f"Gives new rewards: {rewards}")
            total_reward_cashed_out = np.sum(Reward.objects.filter(user=u, cashed_out=True) \
                                             .values_list("amount", flat=True))

            print("total reward_cashed_out", total_reward_cashed_out)
            chest_amount = u.base_chest_amount = total_reward_cashed_out
        else:
            chest_amount = 0
            rewards = []

        return {
            "subject": r["subject"],
            "ok": ok,
            "dailyObjective": chest_amount,
            "chestAmount": chest_amount,
            "rewards": rewards,
            "username": username,
        }
        # TODO: return error message if connection before or after experiment

    @staticmethod
    def update(r):

        u = User.objects.filter(username=r["username"]).first()
        if u is None:
            raise ValueError("User not recognized")

        # --------------------------------------------------------------------------------------------

        # Record any new progress
        progress_json = r["records"]
        progress = json.loads(progress_json)
        with transaction.atomic():
            for p in progress:

                dt = datetime.datetime.fromtimestamp(p["ts"] / 1000)
                dt = pytz.timezone(TIME_ZONE).localize(dt)

                dt_last_boot = datetime.datetime.fromtimestamp(p["tsLastBoot"] / 1000)
                dt_last_boot = pytz.timezone(TIME_ZONE).localize(dt_last_boot)

                # if Activity.objects.filter(user=u, timestamp=dt).first() is None:
                a = Activity(
                    user=u,
                    dt=dt,
                    dt_last_boot=dt_last_boot,
                    step_last_boot=p["stepLastBoot"],
                    step_midnight=p["stepMidnight"])
                a.save()

        # ------------------------------------------------------------------------------------

        # Get the latest user_progress timestamp
        last_record = Activity.objects.latest("dt")
        if last_record is None:
            last_record_ts = datetime.datetime(1, 1, 1).timestamp()
        else:
            last_record_ts = last_record.dt.timestamp()

        # ------------------------------------------------------------------------------------------------

        rewards_done_id = []
        with transaction.atomic():
            if "rewardsDone" in r:
                for reward_dic in r["rewardsDone"]:

                    reward_id = reward_dic["id"]
                    print(f"Reward {reward_id} is done, I will remove it")

                    reward = Reward.objects.filter(id=reward_id).first()
                    reward.objective_reached = reward_dic["objectiveReached"]
                    reward.cashed_out = reward_dic["cashedOut"]
                    reward.accessible = False  # Should be false by definition of 'done'
                    reward.save()

                    rewards_done_id.append(reward_id)

                # TODO: ADD TIMESTAMPS
                # dt = datetime.datetime.fromtimestamp(r["objectiveReachedTimestamp"])
                # pytz.timezone(TIME_ZONE).localize(dt)
                # reward.objective_reached_dt = dt

                # dt = datetime.datetime.fromtimestamp(r["objectiveReachedTimestamp"])
                # pytz.timezone(TIME_ZONE).localize(dt)
                # reward.objective_reached_dt = dt

        # -------------------------------------------------------------------------------

        # else:
        #     rewards = []

        # -------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------

        return {
            'subject': r["subject"],
            'lastRecordTimestamp': last_record_ts,
            'chestAmount': chest_amount,
            'dailyObjective': USER_DAILY_OBJECTIVE,
            'rewards': rewards,
            'rewardsDoneId': rewards_done_id
        }

        # -------------------------------------------------------------------------------
        #
        # latest_pgr_timestamp = utils.time.datetime_to_sting(latest_pgr_timestamp)

        # public int rewardId = -1;
        #         public string rewardDate = "<date>";
        #         public float rewardAmount = -1;
        #         public int dailyObjective = -1;
        #         public int rewardObjective = -1;
        #         public bool lastRewardOfTheDay = false;
        #         public bool objectiveReached = false; // In case of app restart but still need to cashout
        #
        #         public int newRewardId = -1;
        #         public string newRewardDate = "<date>";
        #         public float newRewardAmount = -1;
        #         public int newDailyObjective = -1;
        #         public int newRewardObjective = -1;
        #         public bool newLastRewardOfTheDay = false;
        #
        #         public string lastRecordTimestamp = DUMMY_TIMESTAMP;
        #
        #         public float chestAmount = -1;


# --------------------------------------- #


def treat_request(r):

    subject = r["subject"]
    try:
        f = getattr(RequestHandler, subject)
    except AttributeError:
        raise ValueError(
            f"Subject of the request not recognized: '{subject}'")
    return f(r)
