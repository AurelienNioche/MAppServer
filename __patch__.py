import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from user.models import User, Reward, Status

username = "302M"
u = User.objects.filter(username=username).first()
if u is not None:
    print(f"I found user {username}")
    status = Status.objects.filter(user=u).first()
    for k in ["last_update_dt", "chest_amount", "daily_objective", "state", "reward_id", "starting_at", "objective",
              "amount", "day_of_the_week", "day_of_the_month", "month", "step_number", "reward_id", "error"]:
        print(f"{k}: {getattr(status, k)}")

    rewards = Reward.objects.filter(user=u).order_by("date", "objective")
    for r in rewards:
        to_print = f"r {r.id}: {r.date} {r.objective} {r.amount}"
        if r.objective_reached:
            to_print += f"{r.objective_reached_dt}"
        print(to_print)

else:
    print(f"I did not found user {username}")

