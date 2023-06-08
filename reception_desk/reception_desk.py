import json
import datetime
import pytz
from django.db import transaction

from MAppServer.settings import TIME_ZONE, USER_BASE_REWARD, USER_DAILY_OBJECTIVE, USER_LENGTH_REWARD_QUEUE
from user.models import User, Reward, Activity
import utils.time
# import assistant.core


class RequestHandler:

    @staticmethod
    def login(r):
        username = r["username"]
        u = User.objects.filter(username=username).first()
        ok = u is not None
        return dict(
            subject=r["subject"],
            ok=ok
        )
        # TODO: return error message if connection before or after experiment

    @staticmethod
    def update(r):

        """
        r has the followings keys:

        subject,
        username,
        rewardId,
        objectiveReached,
        objectiveReachedTimestamp,
        rewardCashedOut,
        rewardCashedOutTimestamp
        records.

        records has the following keys:
        @PrimaryKey(autoGenerate = true)
        public int id;

        @ColumnInfo()
        public long ts;  // Timestamp of the recording

        @ColumnInfo()
        public long tsLastBoot; // Timestamp of the last boot

        @ColumnInfo()
        public int stepLastBoot; // Number of step since the last boot

        @ColumnInfo() //  Number of step since midnight (not hyper duper precise)
        public int stepMidnight;
        """

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
            last_record_ts = last_record.timestamp()

        # ------------------------------------------------------------------------------------------------

        rewards_done = r["rewardsDone"]
        for reward_dic in rewards_done:
            reward_id = reward_dic["id"]
            reward = Reward.objects.filter(id=reward_id).first()

        if reward is not None:
            if r["objectiveReached"] is True:
                reward.objective_reached = True

                dt = datetime.datetime.fromtimestamp(r["objectiveReachedTimestamp"])
                pytz.timezone(TIME_ZONE).localize(dt)
                reward.objective_reached_dt = dt

            if r["cashedOut"] is True:
                dt = datetime.datetime.fromtimestamp(r["cashedOutTimestamp"])
                pytz.timezone(TIME_ZONE).localize(dt)
                reward.cashed_out_dt = dt

            if r["accessible"] is False:
                reward.accessible = False

            reward.save()

        # -------------------------------------------------------------------------------

        if len(rewards_done): # If some rewards are already too old and/or have been obtained
            rewards = Reward.objects.filter(accessible=True).order_by("date", "objective")
            rewards = [r.to_dict() for r in rewards][:USER_LENGTH_REWARD_QUEUE]
            print("gives new rewards", rewards)
        else:
            rewards = []

        # -------------------------------------------------------------------------------

        total_reward_cashed_out = Reward.objects.filter(user=u, cashed_out_by_user=True)\
            .values_list("amount", flat=True).sum()

        chest_amount = USER_BASE_REWARD + total_reward_cashed_out

        # -------------------------------------------------------------------------------

        return {
            'subject': r["subject"],
            'lastRecordTimestamp': last_record_ts,
            'chestAmount': chest_amount,
            'dailyObjective': USER_DAILY_OBJECTIVE,
            'rewards': rewards,
            'rewardsDoneId': [reward_dic["id"] for reward_dic in rewards_done]
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
