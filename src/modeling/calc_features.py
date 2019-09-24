import pandas as pd
import os
import seaborn as sns
import numpy as np
# sns.set(font_scale=1.5)
my_file = os.path.dirname('__file__')
days_of_week = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']

fill_na_dict = {}
fill_na_dict['venue_capacity'] = -1
fill_na_dict['venue_capacity_norm'] = 0
fill_na_dict['popularity_in_region'] = 1
fill_na_dict['popularity_in_country'] = 1
fill_na_dict['popularity_in_country_resid'] = 1
fill_na_dict['days_since_last_played'] = -1
fill_na_dict['total_times_played_locally'] = 0
fill_na_dict['sk_popularity'] = -1

def features_for_data_point(data_point):
    data_point['weekend_event'] = data_point['day_of_week'] in ('Sat', 'Sun')
    data_point['mid_week_event'] = data_point['day_of_week'] in ['Wed', 'Tues', 'Mon']

    # Also, lets normalize capacity
    data_point['venue_capacity_norm'] = data_point['venue_capacity'] / data_point['population_city']
    data_point['popularity_country_norm'] = data_point['venue_capacity'] / data_point['population_country']
    data_point['popularity_region_norm'] = data_point['venue_capacity'] / data_point['population_city']
    data_point['popularity_in_country_resid'] = data_point['popularity_in_country'] - data_point['popularity_in_region']

    return data_point

def fill_na(df):
    for k,v in fill_na_dict.items():
        if isinstance(df[k], pd.Series):
            df[k] = df[k].fillna(v)
        else:
            if pd.isna(df[k]):
                df[k] = np.nan
    return df.fillna(np.nan)

def features_for_dataset(df):
    df = df.apply(features_for_data_point, axis=1)
    return df

if __name__ == '__main__':
    pass

