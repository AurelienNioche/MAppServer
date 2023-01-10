from django.utils import timezone

from user.models import User
from user.authentication import login


from utils.time import datetime_to_sting

from random import shuffle


class Subject:

    LOGIN = "login"
    INTERACTION = "interaction"


def treat_request(r):

    if r["subject"] == Subject.LOGIN:
        u = login(email=r["email"], password=r["password"])
        if u is not None:
            return {
                "subject": Subject.LOGIN,
                "ok": True, "user_id": u.id
            }
        else:
            return {
                "subject": Subject.LOGIN,
                "ok": False
            }

    elif r["subject"] == Subject.INTERACTION:

        u = User.objects.filer(id=r["user_id"])
        if u is None:
            print("USER NOT FOUND!!!")
            return

    else:
        raise ValueError(
            f"Subject of the request not recognized: '{r['subject']}'")


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
