from user.models import User

from user.models import Reward, Activity

import utils.time

import assistant.core
# from django.utils import timezone
# from utils.time import datetime_to_sting
# from random import shuffle


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

    @staticmethod
    def update(r):

        u = User.objects.filter(username=r["username"]).first()
        if u is None:
            raise ValueError("User not recognized")

        # Record any new progress
        if "progress" in r:
            progress = r["progress"]
            for p in progress:
                timestamp = p["timestamp"]
                step_number = p["step_number"]
                a = Activity(user=u, timestamp=timestamp, step_number=step_number)
                a.save()

            # Update assistant
            assistant.core.update(u=u)

        # Get the latest user_progress timestamp
        latest_pgr = Activity.objects.latest("timestamp")
        if latest_pgr is None:
            latest_pgr_timestamp = None
        else:
            latest_pgr_timestamp = latest_pgr.timestamp

        # Look at rewards that need to be sent over
        new_rewards = None
        if "latest_reward_timestamp" in r:
            latest_rw_ts = utils.time.string_to_datetime(r["latest_reward_timestamp"])
            r_not_sent = Reward.objects.filter(timestamp__gt=latest_rw_ts)
            if r_not_sent is not None:
                new_rewards = []
                for r in r_not_sent:
                    new_rewards.append(dict(
                        timestamp=utils.time.datetime_to_sting(r.timestamp),
                        amount=r.amount,
                        comment=r.comment
                    ))

        latest_pgr_timestamp = utils.time.datetime_to_sting(latest_pgr_timestamp)

        rsp = dict(
            subject=r["subject"],
            latest_pgr_timestamp=latest_pgr_timestamp,
            new_rewards=new_rewards,
        )

        return rsp


# --------------------------------------- #


def treat_request(r):

    subject = r["subject"]
    try:
        f = getattr(RequestHandler, subject)
    except AttributeError:
        raise ValueError(
            f"Subject of the request not recognized: '{subject}'")
    return f(r)


# def to_json_serializable_dic(obj):
#
#     dic = obj.__dict__
#     for (k, v) in dic.items():
#         if type(v) == np.ndarray:
#             dic[k] = [int(i) for i in v]
#         elif type(v) == np.int64:
#             dic[k] = int(v)
#
#     return dic
