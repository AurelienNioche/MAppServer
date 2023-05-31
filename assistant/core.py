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

        while True:

            all_rewardable_up = Activity.objects.filter(user=u, rewardable=True).order_by('timestamp')
            oldest_up = all_rewardable_up.first()

            if oldest_up is None:
                break
            else:

                ts = oldest_up.timestamp
                lb = ts.replace(hour=0, minute=0, second=0, microsecond=0)
                ub = ts.day.replace(hour=23, minute=59, second=59, microsecond=1e+6)
                ups = all_rewardable_up.filter(
                    timestamp__gt=lb,
                    timestamp__lt=ub).order_by('-step_number')

                sn = ups.first().step_number
                if sn >= cls.DAILY_THRESHOLD:
                    r = Reward(amount=cls.REWARD_AMOUNT)
                    r.save()
                    with transaction.atomic():
                        for up in ups:
                            up.rewardable = False
                            up.save()


def update(u):

    f = getattr(RewardDistributor, u.condition)
    f()

    # tz = pytz.timezone(TIME_ZONE)
    # now = datetime.datetime.now(tz=tz)
    # midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

