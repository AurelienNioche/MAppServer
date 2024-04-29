import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "MAppServer.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import numpy as np

from user.models import User
from reception_desk.reception_desk import RequestHandler
import utils.time
from datetime import datetime
import pytz

from MAppServer.settings import TIME_ZONE


# u = User.objects.filter(username="123test").first()
# RequestHandler.log_progress(dict(
#     subject="log_progress",
#     user_id=u.id,
#     progress=[
#         {
#             "timestamp": utils.time.datetime_to_sting(datetime.now(tz=pytz.timezone(TIME_ZONE))),
#             "step_number": 34
#         },
#     ]))

# v = np.load("transition_velocity_atvv.npy")
# p = np.load("transition_position_pvp.npy")
#
# v2 = np.load("transition_velocity_atvv_2.npy")
# p2 = np.load("transition_position_pvp_2.npy")
#
# pos = np.load("position.npy")
# vel = np.load("velocity.npy")
#
# ap = np.load("action_plans.npy")
#
# pos2 = np.load("position_2.npy")
# vel2 = np.load("velocity_2.npy")
# ap2 = np.load("action_plans_2.npy")
#
# print("v == v2", np.allclose(v, v2))
# print("p == p2", np.allclose(p, p2))
#
# print("pos == pos2", np.allclose(pos, pos2))
# print("vel == vel2", np.allclose(vel, vel2))
# print("ap == ap2", np.allclose(ap, ap2))

