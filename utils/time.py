from datetime import datetime
import pytz

from MAppServer.settings import TIME_ZONE

FORMAT = '%Y-%m-%d %H:%M:%S.%f'
FORMAT_DATE = '%Y-%m-%d'


def string_to_datetime(string_time):
    dt = datetime.strptime(string_time, FORMAT)
    return pytz.timezone(TIME_ZONE).localize(dt)


def string_to_date(string_date):
    dt = datetime.strptime(string_date, FORMAT_DATE)
    return pytz.timezone(TIME_ZONE).localize(dt).date()


def datetime_to_sting(datetime_obj):
    return datetime_obj.astimezone(pytz.timezone(TIME_ZONE)).strftime(FORMAT)
