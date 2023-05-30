from user.models import User
from user.authentication import login

# from django.utils import timezone
# from utils.time import datetime_to_sting
# from random import shuffle


def _login(r):
    rsp = dict(subject=r["subject"])
    username = r["username"]
    u = login(username=username)
    if u is not None:
        spec = dict(ok=True, user_id=u.id)
    else:
        spec = dict(ok=False)
    rsp.update(spec)
    return rsp


def _log_progress(r):

    u = User.objects.filer(id=r["user_id"])
    assert u is not None
    progress = r["progress"]
    for p in progress:
        step_number = p["step_number"]

    # TODO

# --------------------------------------- #

ORIENT_REQUEST = {
    "login": _login,
    "progress": _log_progress,
}

# --------------------------------------- #


def treat_request(r):

    subject = r["subject"]
    if subject not in ORIENT_REQUEST:
        raise ValueError(
            f"Subject of the request not recognized: '{subject}'")


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
