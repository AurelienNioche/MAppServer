import datetime
import pytz
from django.db import transaction
from MAppServer.settings import TIME_ZONE

from user.models import Activity, Reward


class RewardDistributor:

    DAILY_THRESHOLD = 7500
    REWARD_AMOUNT = 1.5

    @classmethod
    def rewarded_only_at_goal(cls, u):

        all_rewardable = Activity.objects.filter(user=u, rewardable=True).order_by('timestamp')

        while True:

            oldest_up = all_rewardable.first()

            if oldest_up is None:
                break

            ts = oldest_up.timestamp
            ub = ts.replace(hour=23, minute=59, second=59, microsecond=999999)
            act = all_rewardable.filter(
                timestamp__lte=ub).order_by('-step_number')

            a = act.first()
            reach_threshold = a.step_number >= cls.DAILY_THRESHOLD

            give_reward = False
            if reach_threshold:
                # give reward only if no reward has been given for the same day
                give_reward = Reward.objects.filter(timestamp__day=a.timestamp.day).first() is None

            if give_reward:
                r = Reward(user=u, timestamp=a.timestamp, amount=cls.REWARD_AMOUNT)
                r.save()

            all_rewardable = all_rewardable.filter(timestamp__gt=ub)
            successor_day_exists = all_rewardable.filter(timestamp__gt=ub).first() is not None

            # If a reward has been given now or before the same day,
            # or it was the activity of a previous day,
            # activity is not rewardable anymore
            if reach_threshold or successor_day_exists:
                with transaction.atomic():
                    for a in act:
                        a.rewardable = False
                        a.save()


def update(u):

    f = getattr(RewardDistributor, u.condition)
    f(u)

    # tz = pytz.timezone(TIME_ZONE)
    # now = datetime.datetime.now(tz=tz)
    # midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

