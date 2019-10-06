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

    if isinstance(data_point, pd.Series):
        data_point['weekend_event'] = data_point['day_of_week'] in ('Sat', 'Sun')
        data_point['mid_week_event'] = data_point['day_of_week'] in ['Wed', 'Tues', 'Mon']
        data_point['sat_event'] = data_point['day_of_week'] in ['Sat']
        data_point['fri_event'] = data_point['day_of_week'] in ('Fri',)
        data_point['fri_sat_event'] = data_point['day_of_week'] in ('Fri','Sat')
        data_point['early_week_event'] = data_point['day_of_week'] in ['Tues', 'Mon']
    else:
        data_point['weekend_event'] = data_point['day_of_week'].isin(('Sat', 'Sun'))
        data_point['mid_week_event'] = data_point['day_of_week'].isin(['Wed', 'Tues', 'Mon'])
        data_point['sat_event'] = data_point['day_of_week'].isin(('Sat',))
        data_point['fri_event'] = data_point['day_of_week'].isin(('Fri',))
        data_point['fri_sat_event'] = data_point['day_of_week'].isin(('Fri','Sat'))
        data_point['early_week_event'] = data_point['day_of_week'].isin(['Tues', 'Mon'])

    # Also, lets normalize capacity
    data_point['venue_capacity_norm'] = data_point['venue_capacity'] / data_point['population_city']
    data_point['popularity_country_norm'] = data_point['venue_capacity'] / data_point['population_country']
    data_point['popularity_region_norm'] = data_point['venue_capacity'] / data_point['population_city']
    data_point['popularity_in_country_resid'] = data_point['popularity_in_country'] - data_point['popularity_in_region']
    data_point['population_country_resid'] = data_point['population_country'] - data_point['population_city']
    data_point['price_mean_normalized'] = data_point['price_mean']/data_point['gdp_country']
    data_point['price_median_normalized'] = data_point['price_median']/data_point['gdp_country']
    data_point['subcat_52'] = data_point['subcat']=='52'
    data_point['subcat_1'] = data_point['subcat']=='1'
    #data_point['price_last_normalized'] = data_point['price_mean']/data_point['gdp_country']
    #data_point['price_last_normalized'] = data_point['price_mean']/data_point['gdp_country']

    return data_point

def fill_na(df):
    if isinstance(df, pd.DataFrame):
        for k,v in fill_na_dict.items():
            if k in df:
                df[k] = df[k].fillna(v)
    else:
        for k, v in fill_na_dict.items():

            if pd.isna(df[k]):
                df[k] = np.nan
    return df

def features_for_dataset(df):
    df = features_for_data_point(df)
    return df

if __name__ == '__main__':
    pass

