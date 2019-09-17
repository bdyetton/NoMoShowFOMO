import pandas as pd
import os
import seaborn as sns
sns.set(font_scale=1.5)
import matplotlib.pyplot as plt
import datetime
import numpy as np
import pytz
my_file = os.path.dirname('__file__')
days_of_week = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']


def add_time_features(df):
    df['day_of_week'] = df['event_date'].apply(lambda x: days_of_week[x.weekday()])
    df['time_of_day'] = df['event_date'].apply(lambda x: x.hour)
    df['on_sale_period'] = df.apply(lambda x: (x['event_date'] - x['on_sale_date']).total_seconds() / 60 / 60 / 24,
                                    axis=1)
    df['days_to_event'] = df.apply(lambda x: (x['event_date'] - x['sample_date'].to_pydatetime()).total_seconds()/60/60/24, axis=1)
    df['days_on_sale'] = df.apply(lambda x: (x['sample_date'].to_pydatetime() - x['on_sale_date']).total_seconds()/60/60/24, axis=1)
    df['event_complete'] = df['days_to_event'] < 0
    df.loc[df['event_complete'], 'days_on_sale'] = df.loc[df['event_complete'], 'on_sale_period']
    df.loc[df['event_complete'], 'days_to_event'] = np.nan
    return df


def stacked_area(df):
    sf_counts = df.loc[:,['days_on_sale','avail_first_tier']]
    sf_counts['count'] = 1
    sf_counts = sf_counts.pivot_table(index=['days_on_sale'],values=['count'], columns=['avail_first_tier'])
    sf_counts = sf_counts.fillna(0).reset_index()
    sf_counts['days_on_sale'] = pd.to_timedelta(sf_counts['days_on_sale'].apply(lambda x: datetime.timedelta(days=x)))
    sf_counts = sf_counts.set_index('days_on_sale').resample().sum()
    sf_counts = sf_counts.groupby('days_on_sale','avail_first_tier').count()
    sf_totals = sf_counts.groupby('avail_first_tier').sum()
    sf_perc = pd.merge(sf_counts, sf_totals, on='days_on_sale')
    sf_perc['perc_avail_first_tier'] = sf_perc['avail_first_tier_x']/sf_perc['avail_first_tier_y']
    plt.stackplot(sf_perc['days_on_sale'], sf_perc['perc_avail_first_tier'], labels=[])
    plt.legend(loc='upper left')
    plt.show()


if __name__ == '__main__':
    tm_df = pd.read_pickle(os.path.join(my_file,'../../data/ticketmaster.pkl'))
    tm_df = add_time_features(tm_df)
    tm_df = tm_df.loc[tm_df['days_on_sale']<356*2,:]
    for label in tm_df['avail_first_tier'].unique():
        if label == 'unknown':
            continue
        sns.distplot(a=tm_df.loc[tm_df['avail_first_tier']==label,'days_on_sale'], label=label)
        plt.legend()
    plt.show()
    sns.countplot(x='avail_first_tier', data=tm_df)
    plt.show()
    sns.countplot(x='day_of_week', data=tm_df, order=days_of_week)
    plt.show()
    #tm_df = add_time_features(tm_df)
    #tm_df.to_pickle(os.path.join(my_file,'../../data/ticketmaster.pkl'))

