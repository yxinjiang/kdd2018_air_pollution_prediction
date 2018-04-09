import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def group(ts: pd.DataFrame, mode, value=None, time_key='time', agg_op=None):
    """
        Groups data into specific time intervals, then returns aggregated values of
        those with f(time) = value; both intervals and matching rows depend on the given mode
        modes:
            h: hour of day [0, 23]
            dw: day of week [0, 6], where 0: sunday, 6: saturday
            w: week of month [0, 3]
            m: month of year [1, 12]
            s: season of year [1, 3]
        dt.<fields>: https://pandas.pydata.org/pandas-docs/stable/api.html#datetimelike-properties
        Prepare time series data for learning
    """
    agg_op = {'value': 'mean'} if agg_op is None else agg_op
    sample = ts.copy()
    time = pd.to_datetime(ts[time_key])
    if mode == 'h':
        sample[time_key] = time.dt.strftime("%Y-%m-%d %H:00:00")  # coarse-grain the time to hour of day
        matches_value = time.dt.hour == value
    elif mode == '3h':
        time = time.apply(lambda dt: round_hour(dt, 3))
        sample[time_key] = time.dt.strftime("%Y-%m-%d %H:00:00")
        matches_value = time.dt.hour == value
    elif mode == '6h':
        time = time.apply(lambda dt: round_hour(dt, 6))
        sample[time_key] = time.dt.strftime("%Y-%m-%d %H:00:00")
        matches_value = time.dt.hour == value
    elif mode == 'dw':
        sample[time_key] = time.dt.strftime("%Y-%W-%w")  # coarse-grain the time to day of week
        # in pandas dayofweek is 0: monday, 6: sunday,
        # unlike strftime where 0: sunday, 6:saturday
        matches_value = time.dt.dayofweek == ((value + 6) % 7)
    elif mode == 'm':
        sample[time_key] = time.dt.strftime("%Y-%m")  # coarse-grain the time to month
        matches_value = time.dt.month == value
    elif mode == 's':
        sample[time_key] = np.mod(time.dt.strftime('%Y-%m').astype(int), 4)

    # sample those with matching time values
    sample = sample.loc[matches_value, :] if value is not None else sample
    # aggregate values based on mode
    sample = sample.groupby([time_key], as_index=False).agg(agg_op)
    sample.reset_index(drop=True, inplace=True)
    return sample


def group_behind(time: list, value: list, index, step, hours):
    """
        Group values according to unit, that are mostly hours * step behind the time(index)
    :param time: time series of data-time objects
    :param value:   time series of values to be grouped
    :param index:
    :param step:
    :param hours: number of hours as a unit to group
    :return:
    """
    aggregate = dict()  # sum of values for a time group
    count = dict()  # number of values for a time group
    cur_t = time[index]
    min_t = cur_t - timedelta(hours=step * hours)
    while cur_t >= min_t:
        # t: rounded time to aggregate values using a dictionary
        t = round_hour(cur_t, hours)
        aggregate[t] = aggregate[t] + value[index] if t in aggregate else value[index]
        count[t] = count[t] + 1 if t in count else 1
        if index == 0:
            break
        index = index - 1
        cur_t = time[index]

    remained_steps = step - len(aggregate)
    # remained_steps > 0 when index hits 0 before "step" entries are filled
    if remained_steps > 0:
        last_t = cur_t
        for i in range(0, remained_steps):
            cur_t -= timedelta(hours=hours)
            t = round_hour(cur_t, hours)
            aggregate[t] = aggregate[last_t]
            count[t] = 1

    for t, v in iter(aggregate.items()):
        aggregate[t] /= count[t]

    return [value for (key, value) in sorted(aggregate.items())]


def round_hour(time: datetime, hours):
    return time.replace(hour=time.hour - time.hour % hours, minute=0, second=0)


def select(df: pd.DataFrame, time_key,
           from_time='00-00-00 00', to_time='99-01-01 00'):
    filter_index = (df[time_key] >= from_time) & (df[time_key] < to_time)
    return df.loc[filter_index, :].reset_index(drop=True)
