"""
    Learn the time-series using an MLP over all stations all together
"""
import numpy as np
import pandas as pd
import const, settings
from src import util
from src.preprocess import times
from src.methods.neural_net import NeuralNet


def replace_time(data: pd.DataFrame):
    """
        Replace the complete datetime with its (day of week, hour)
    :param data:
    :return:
    """
    date = pd.to_datetime(data[const.TIME], format=const.T_FORMAT, utc=True)
    data.insert(loc=0, column='hour', value=date.dt.hour)
    data.insert(loc=0, column='dayofweek', value=(date.dt.dayofweek + 1) % 7)  # 0: monday -> 0: sunday
    data.drop(columns=[const.TIME], inplace=True)


# access default configurations
config = settings.config[const.DEFAULT]

# load data
stations = pd.read_csv(config[const.BJ_STATIONS], sep=";", low_memory=False)
ts = pd.read_csv(config[const.BJ_FEATURES], sep=";", low_memory=False)

train = times.select(df=ts, time_key=const.TIME, from_time='00-01-01 00', to_time='17-11-31 23')
valid = times.select(df=ts, time_key=const.TIME, from_time='17-11-31 00', to_time='17-12-31 23')
test = times.select(df=ts, time_key=const.TIME, from_time='17-12-31 00', to_time='18-01-31 23')

replace_time(train)
replace_time(valid)
replace_time(test)

pollutants = ['PM2.5']  # ['PM2.5', 'PM10', 'O3']
columns = ['forecast', 'actual', 'station', 'pollutant']
predictions = pd.DataFrame(data={}, columns=columns)
x = range(0, 52)
y = range(52, 99)
x_train = train.iloc[:, x]
y_train = train.iloc[:, y]
x_valid = valid.iloc[:, x]
y_valid = valid.iloc[:, y]
x_test = test.iloc[:, x]
y_test = test.iloc[:, y]

mlp = NeuralNet.mlp(x_train=x_train, y_train=y_train, x_valid=x_valid, y_valid=y_valid)

y_predict = mlp.predict(x_test)
# drop NaN records
predictions.dropna(inplace=True)

y_test = y_test.values.reshape(y_test.size)
y_predict = np.array(y_predict).reshape(y_test.size)
print('SMAPE', util.SMAPE(forecast=y_predict, actual=y_test))



