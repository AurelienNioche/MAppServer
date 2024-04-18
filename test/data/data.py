import numpy as np
import pandas as pd
from datetime import datetime, time
from glob import glob

from test.activity.activity import extract_step_events

N_SECONDS_IN_DAY = 86400


def load_data(
        user: str,
        data_path: str,
        remove_empty_days: bool = True
) -> list:
    # Extract the file path
    file = glob(f"{data_path}/dump_latest/{user}_activity*.csv")[0]

    df = pd.read_csv(file, index_col=0)
    df.dt = pd.to_datetime(df.dt, utc=False, format="ISO8601")
    df.dt = df.dt.dt.tz_convert("Europe/London")

    step_events = extract_step_events(
        step_counts=df.step_midnight,
        datetimes=df.dt,
        remove_empty_days=remove_empty_days
    )
    return step_events
