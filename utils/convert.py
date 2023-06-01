import numpy as np


def to_json_serializable_dic(obj):

    dic = obj.__dict__
    for (k, v) in dic.items():
        if type(v) == np.ndarray:
            dic[k] = [int(i) for i in v]
        elif type(v) == np.int64:
            dic[k] = int(v)

    return dic
