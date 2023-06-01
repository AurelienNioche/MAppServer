import datetime
from django.db import transaction

from user.models import User, Reward, Activity
import utils.time
import assistant.core


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
        if "activity" in r:
            print("Recording new activity")
            progress = r["activity"]
            with transaction.atomic():
                for p in progress:
                    timestamp = utils.time.string_to_datetime(p["timestamp"])
                    step_number = p["step_number"]
                    if Activity.objects.filter(user=u, timestamp=timestamp).first() is None:
                        a = Activity(user=u, timestamp=timestamp, step_number=step_number)
                        a.save()

            # Update assistant
            print("Updating the assistant")
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
            latest_rwd_ts = r["latest_reward_timestamp"]
            if latest_rwd_ts is None:
                latest_rwd_ts = datetime.datetime.min
            else:
                latest_rwd_ts = utils.time.string_to_datetime(latest_rwd_ts)
            rwd_not_sent = Reward.objects.filter(timestamp__gt=latest_rwd_ts)
            if rwd_not_sent is not None:
                new_rewards = []
                for rwd in rwd_not_sent:
                    new_rewards.append(dict(
                        timestamp=utils.time.datetime_to_sting(rwd.timestamp),
                        amount=rwd.amount,
                        comment=rwd.comment
                    ))

        latest_pgr_timestamp = utils.time.datetime_to_sting(latest_pgr_timestamp)
        return dict(
            subject=r["subject"],
            latest_pgr_timestamp=latest_pgr_timestamp,
            new_rewards=new_rewards,
        )


# --------------------------------------- #


def treat_request(r):

    subject = r["subject"]
    try:
        f = getattr(RequestHandler, subject)
    except AttributeError:
        raise ValueError(
            f"Subject of the request not recognized: '{subject}'")
    return f(r)

