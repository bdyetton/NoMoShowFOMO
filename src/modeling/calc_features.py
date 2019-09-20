import pandas as pd
import os
import seaborn as sns
sns.set(font_scale=1.5)
my_file = os.path.dirname('__file__')
days_of_week = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']


def calc_features(data_point):
    data_point['weekend_event'] = data_point['day_of_week'] in ('Sat', 'Sun')
    return data_point

if __name__ == '__main__':
    pass

